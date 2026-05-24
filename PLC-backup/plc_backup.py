# =============================================================================
# plc_backup.py
# =============================================================================
#
# WHAT THIS SCRIPT DOES:
#   Copies PLC program files from the source directory into a new timestamped
#   folder on two destinations: a NAS (network drive) and a local backup folder.
#   For .ACD files, it uses incremental logic — only NEW or CHANGED files are
#   copied. If any .ACD file has NOT been saved since the last backup, a popup
#   warning is shown so the operator can save and re-run.
#
#   Non-ACD files (such as .BAK and recovery files) are always copied.
#
#   If the NAS is unreachable, it logs the error and continues — the local
#   backup still runs. Every run is recorded in a plain-text log file.
#
# IMPORTANT NOTE ABOUT OPEN FILES:
#   This script copies whatever is saved on disk. If RSLogix 5000 is open
#   with unsaved changes, those changes will NOT be in the backup. Only the
#   last Ctrl+S save is captured. The popup warning (backup_popup.py) exists
#   to alert the operator when a file has not been saved since the last backup.
#
# HOW TO RUN MANUALLY:
#   Double-click this file in Windows Explorer, or right-click and choose
#   "Open with" -> Python. A summary will print on screen when it finishes.
#
# -----------------------------------------------------------------------------
# HOW TO SET UP IN WINDOWS TASK SCHEDULER (step by step):
#
#   1. Press the Windows key, type "Task Scheduler", and open it.
#   2. In the right panel, click "Create Basic Task..."
#   3. Name it something like "PLC Sunday Backup" and click Next.
#   4. Choose "Weekly", click Next.
#   5. Set the start time (e.g. 2:00 AM Sunday), check "Sunday", click Next.
#   6. Choose "Start a program", click Next.
#   7. In the "Program/script" box, enter the full path to pythonw.exe
#      Example: C:\Python311\pythonw.exe
#      (Use pythonw.exe instead of python.exe so no black window appears)
#   8. In the "Add arguments" box, enter the full path to this script:
#      Example: "C:\claude\claude-code-course\PLC-backup\plc_backup.py"
#   9. Click Next, then Finish.
#  10. Right-click the new task -> Properties -> General tab ->
#      Check "Run whether user is logged on or not" and
#      "Run with highest privileges" so it works even if no one is logged in.
#
# -----------------------------------------------------------------------------

import os           # For working with file paths and directory listings
import re           # For pattern matching when scanning backup folder names
import shutil       # For copying files and folders
import datetime     # For generating the timestamp used in folder names


# =============================================================================
# CONFIGURATION — Fill in the paths for your site before using
# =============================================================================

# Where the PLC program files live right now
SOURCE_DIR = r"C:\PLC\CURRENT_PLC_VIRSION\2026"

# NAS backup destination (mapped drive or UNC path)
# TODO: FILL IN BEFORE USING — e.g. r"Z:\PLC_Backups" or r"\\servername\share\PLC_Backups"
NAS_BACKUP = r"Z:\PLC_Programs"

# Local backup destination (secondary copy on this machine or a local drive)
# TODO: FILL IN BEFORE USING — e.g. r"D:\Backups\PLC"
LOCAL_BACKUP = r"C:\Python\NAS_Backups\PLC"

# Where the log file will be written (inside the local backup folder is a
# good place so it's easy to find alongside the backups)
# TODO: FILL IN BEFORE USING — update this to match LOCAL_BACKUP above
LOG_FILE = r"Z:\PLC_Programs\plc_backup_log.txt"

# Path to the PLC change-watcher CSV — included in every backup so each
# snapshot also captures the change history recorded at that point in time.
# TODO: Update this path if plc_change_watcher.py is ever moved.
CHANGE_LOG = r"C:\Python\PLC-change-watcher\plc_change_log.csv"


# =============================================================================
# FUNCTION: get_timestamp_folder_name
# =============================================================================
# Think of this like stamping the date and time on a work order.
# It reads the current clock and builds a folder name like:
#   PLC_Backup_2026-05-04_0830
# =============================================================================

def get_timestamp_folder_name():
    # Get the current date and time from the computer's clock
    now = datetime.datetime.now()

    # Format it into a readable string: YYYY-MM-DD_HHMM
    # strftime() is a standard way to format dates — the % codes are placeholders:
    #   %Y = 4-digit year, %m = month, %d = day, %H = hour (24h), %M = minute
    timestamp = now.strftime("%Y-%m-%d_%H%M")

    # Combine the prefix with the timestamp to make the folder name
    folder_name = "PLC_Backup_" + timestamp

    return folder_name


# =============================================================================
# FUNCTION: find_latest_backup_folder
# =============================================================================
# Scans a backup destination to find the most recent backup folder.
# Backup folders are named PLC_Backup_YYYY-MM-DD_HHMM — because the date
# comes first and the format is consistent, alphabetical order equals
# chronological order. So the last item in a sorted list is the most recent.
#
# Think of this like looking at a row of dated binders on a shelf and
# picking the one with the highest date stamp.
#
# Parameters:
#   dest_root — the root backup folder to scan (e.g. Z:\PLC_Programs)
#
# Returns:
#   Full path to the most recent backup folder, or None if none found
# =============================================================================

def find_latest_backup_folder(dest_root):
    # This regex pattern matches folder names in the exact format PLC_Backup_YYYY-MM-DD_HHMM
    # \d{4} means "exactly 4 digits", \d{2} means "exactly 2 digits"
    pattern = re.compile(r"^PLC_Backup_\d{4}-\d{2}-\d{2}_\d{4}$")

    try:
        # Get a list of everything inside the destination root folder
        all_entries = os.listdir(dest_root)
    except Exception:
        # If the folder doesn't exist yet or can't be read, return None.
        # This is expected on a first run before any backups have been made.
        return None

    # Build a list of folder names that match our backup naming pattern
    matching = []
    for entry in all_entries:
        full_path = os.path.join(dest_root, entry)
        # Only include it if it is a folder AND its name matches the pattern
        if os.path.isdir(full_path) and pattern.match(entry):
            matching.append(entry)

    # If no matching folders were found, there is no previous backup
    if not matching:
        return None

    # Sort alphabetically — because the format is YYYY-MM-DD_HHMM, this puts
    # the most recent backup last in the list
    matching.sort()

    # Walk backwards through the sorted list (most recent first) and return
    # the first folder that actually contains at least one .ACD file.
    # This skips folders that were created but received no ACD files (e.g. if
    # the source was empty or the copy failed), so timestamp comparisons in
    # copy_files_to_destination compare against a real previous ACD file.
    for folder_name in reversed(matching):
        folder_path = os.path.join(dest_root, folder_name)
        try:
            contents = os.listdir(folder_path)
        except Exception:
            continue
        # Check whether any file in this folder has a .ACD extension
        if any(f.upper().endswith('.ACD') and 'BAK' not in f.upper() for f in contents):
            return folder_path

    # No backup folder contained any .ACD file — treat as first run
    return None


# =============================================================================
# FUNCTION: _keep_latest_per_processor
# =============================================================================
# Given a list (or any iterable) of ACD filenames, return a new list that
# contains only the most recently dated file for each processor.
#
# Processor name = everything before the first _YYYY_ date pattern.
#   "Rewash_2026_01_03.ACD"  →  processor "Rewash", date "2026_01_03"
#   "Rewash_2026_05_17.ACD"  →  processor "Rewash", date "2026_05_17"
#   → only "Rewash_2026_05_17.ACD" is kept.
#
# String comparison works for dates because YYYY_MM_DD is zero-padded and
# consistent, so lexicographic order equals chronological order.
#
# Files that don't match the expected pattern are kept unconditionally.
# =============================================================================

def _keep_latest_per_processor(file_list):
    import re

    # best maps each processor name to (date_string, filename)
    best = {}

    for filename in file_list:
        # Match: <processor>_YYYY_MM_DD.ACD  (case-insensitive extension)
        match = re.match(r'^(.+?)_(\d{4}_\d{2}_\d{2})\.ACD$', filename, re.IGNORECASE)
        if match:
            processor = match.group(1)   # e.g. "Rewash"
            date_str  = match.group(2)   # e.g. "2026_05_17"
            # Keep this file if we haven't seen this processor yet,
            # or if its date is later than the one we already have
            if processor not in best or date_str > best[processor][0]:
                best[processor] = (date_str, filename)
        else:
            # Doesn't follow the dated-name convention — keep it as-is.
            # Use the full filename as the key so nothing is accidentally dropped.
            best[filename] = ('', filename)

    # Return just the filenames (discard the date strings used for comparison)
    return [entry[1] for entry in best.values()]


# =============================================================================
# FUNCTION: copy_files_to_destination
# =============================================================================
# This is the workhorse — it copies files from the source folder into a new
# timestamped subfolder at the destination, using incremental logic for .ACD
# files: only NEW or CHANGED files are copied. Non-ACD files are always copied.
#
# Think of it like pulling drawings from a filing cabinet — but this time,
# you check if each drawing has been updated since the last copy was made.
# If the drawing hasn't changed, you note it and skip the photocopier.
#
# Parameters:
#   source      — the folder to copy FROM
#   dest_root   — the root backup folder to copy TO (NAS or local)
#   folder_name — the timestamped subfolder name to create inside dest_root
#   log_lines   — a list we append messages to (printed and saved to log later)
#
# Returns:
#   files_copied        — how many files were actually copied (integer)
#   success             — True if no errors occurred, False otherwise
#   unchanged_acd_files — list of .ACD filenames that were skipped because
#                         they have not been saved since the last backup
# =============================================================================

def copy_files_to_destination(source, dest_root, folder_name, log_lines):
    # Build the full path of the new backup folder
    # e.g. Z:\PLC_Backups\PLC_Backup_2026-05-17_0200
    dest_folder = os.path.join(dest_root, folder_name)

    # Find the most recent existing backup folder BEFORE we create today's new one.
    # We do this first so the folder we are about to create is not accidentally
    # treated as the "previous" backup when comparing file timestamps.
    prev_backup = find_latest_backup_folder(dest_root)

    if prev_backup:
        log_lines.append(f"  Comparing against previous backup: {os.path.basename(prev_backup)}")
    else:
        log_lines.append("  No previous backup found — this is a first run, copying everything.")

    files_copied = 0          # Counter — starts at zero, goes up for each file copied
    success = True            # Assume success unless something goes wrong
    unchanged_acd_files = []  # Collects names of .ACD files that have not changed

    try:
        # Create the new timestamped folder
        # exist_ok=True means don't crash if the folder already exists
        os.makedirs(dest_folder, exist_ok=True)
        log_lines.append(f"  Created folder: {dest_folder}")

        # Get a list of everything in the source directory
        all_items = os.listdir(source)

        # Loop through every item in the source folder
        # A loop is like a multi-outlet circuit — same action repeated for each load
        for item_name in all_items:
            # Build the full path to this specific file
            source_file = os.path.join(source, item_name)

            # Only process files — skip any subfolders inside the source
            if not os.path.isfile(source_file):
                continue

            # Where this file will go in today's backup folder
            dest_file = os.path.join(dest_folder, item_name)

            # Get the file extension (the part after the last dot, e.g. ".ACD")
            # We use .upper() so ".acd" and ".ACD" are treated the same way
            _, ext = os.path.splitext(item_name)
            is_acd = (ext.upper() == ".ACD") and ("BAK" not in item_name.upper())

            if not is_acd:
                # Non-ACD files (like .BAK, recovery files, docs) are always copied
                # regardless of whether they have changed — no incremental logic here
                try:
                    shutil.copy2(source_file, dest_file)
                    files_copied += 1
                    log_lines.append(f"    COPIED (non-ACD): {item_name}")
                except Exception as copy_error:
                    log_lines.append(f"    WARNING: Could not copy {item_name} — {copy_error}")

            elif prev_backup is None:
                # This is an ACD file, but there is no previous backup to compare against.
                # This is a first run — copy everything.
                try:
                    shutil.copy2(source_file, dest_file)
                    files_copied += 1
                    log_lines.append(f"    NEW (first run): {item_name}")
                except Exception as copy_error:
                    log_lines.append(f"    WARNING: Could not copy {item_name} — {copy_error}")

            else:
                # This is an ACD file and we have a previous backup to compare against.
                # Check if this file existed in the previous backup folder.
                prev_file = os.path.join(prev_backup, item_name)

                if not os.path.exists(prev_file):
                    # File is brand new — it did not exist in the last backup at all
                    try:
                        shutil.copy2(source_file, dest_file)
                        files_copied += 1
                        log_lines.append(f"    NEW: {item_name}")
                    except Exception as copy_error:
                        log_lines.append(f"    WARNING: Could not copy {item_name} — {copy_error}")

                elif os.path.getmtime(source_file) != os.path.getmtime(prev_file):
                    # The file's "last modified" timestamp differs from the backup copy.
                    # shutil.copy2() preserves timestamps, so a difference means the
                    # operator saved this file in RSLogix 5000 since the last backup.
                    try:
                        shutil.copy2(source_file, dest_file)
                        files_copied += 1
                        log_lines.append(f"    CHANGED: {item_name}")
                    except Exception as copy_error:
                        log_lines.append(f"    WARNING: Could not copy {item_name} — {copy_error}")

                else:
                    # The modified timestamp matches — this file has NOT been saved
                    # since the last backup. Skip copying it and flag it so the
                    # operator warning popup can alert them to save and re-run.
                    log_lines.append(f"    UNCHANGED (skipped): {item_name}")
                    unchanged_acd_files.append(item_name)

        log_lines.append(f"  Total files copied: {files_copied}")
        if unchanged_acd_files:
            log_lines.append(
                f"  Unchanged ACD files (not saved since last backup): "
                f"{', '.join(unchanged_acd_files)}"
            )

    except Exception as error:
        # If anything goes wrong (permission denied, disk full, path not found, etc.)
        # catch the error, record it, and set success to False.
        # We do NOT use "raise" here — we want the script to keep running.
        log_lines.append(f"  ERROR: {error}")
        success = False

    # Keep only the most recently dated .ACD file per processor name
    unchanged_acd_files = _keep_latest_per_processor(unchanged_acd_files)

    return files_copied, success, unchanged_acd_files


# =============================================================================
# FUNCTION: write_log
# =============================================================================
# Appends a record of this backup run to the log file.
# Opening a file in "append" mode is like adding a new entry to a paper log
# book — previous entries are never touched, new content goes at the bottom.
# =============================================================================

def write_log(log_file, log_lines):
    try:
        # Make sure the folder where the log file lives actually exists
        log_folder = os.path.dirname(log_file)
        if log_folder:
            os.makedirs(log_folder, exist_ok=True)

        # Open the log file in append mode ("a") — creates it if it doesn't exist
        with open(log_file, "a") as f:
            # Write a separator line so each run is easy to find in the file
            f.write("\n" + "=" * 60 + "\n")

            # Write the date and time this run happened
            run_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            f.write(f"Backup run: {run_time}\n")
            f.write("=" * 60 + "\n")

            # Write every message we collected during this run
            for line in log_lines:
                f.write(line + "\n")

    except Exception as log_error:
        # If we can't write the log (e.g. no disk space), print a warning
        # but do not crash — the backup itself may have succeeded
        print(f"WARNING: Could not write to log file: {log_error}")


# =============================================================================
# FUNCTION: run_backup
# =============================================================================
# This function contains all the actual backup work. It runs one complete
# backup cycle and returns a set of any .ACD filenames that were UNCHANGED
# (not saved by the operator since the last backup).
#
# Separating the backup work into its own function means the operator warning
# popup (backup_popup.py) can call this function again if the operator clicks
# "Run Backup Again" — without needing to restart the whole script.
#
# Think of it like a sub-panel that main() can switch on whenever needed.
#
# Returns a tuple of four values:
#   unchanged_acd_set — set of .ACD filenames that were not saved since last backup
#   nas_ok            — True if the NAS backup completed without errors
#   local_ok          — True if the local backup completed without errors
#   files_copied      — total number of files copied across both destinations
# =============================================================================

def run_backup():
    # This list collects all status messages during the run.
    # At the end, we write them all to the log file at once.
    log_lines = []

    print("=" * 50)
    print("PLC Backup Tool")
    print("=" * 50)

    # --- Step 1: Generate the timestamped folder name ---
    folder_name = get_timestamp_folder_name()
    log_lines.append(f"Backup folder name: {folder_name}")
    log_lines.append(f"Source directory:   {SOURCE_DIR}")
    print(f"Backup folder: {folder_name}")

    # --- Step 2: Check that the source directory actually exists ---
    if not os.path.isdir(SOURCE_DIR):
        message = f"ERROR: Source directory not found: {SOURCE_DIR}"
        print(message)
        log_lines.append(message)
        write_log(LOG_FILE, log_lines)
        # Return a full tuple so main() can always unpack four values.
        # Both destinations failed, so nas_ok and local_ok are False.
        return (set(), False, False, 0)

    # Snapshot the most recent existing backup folder for each destination
    # BEFORE creating today's new folders.  After copy_files_to_destination()
    # runs, the new folder will contain .ACD files and find_latest_backup_folder()
    # would return it instead — so we capture the previous paths here for the
    # incremental check used later when copying the change log.
    prev_nas_backup   = find_latest_backup_folder(NAS_BACKUP)
    prev_local_backup = find_latest_backup_folder(LOCAL_BACKUP)

    # --- Step 3: Copy to NAS ---
    # The entire NAS copy is wrapped in try/except so if the NAS is
    # offline or unreachable, we catch that error and keep going.
    print("\nCopying to NAS...")
    log_lines.append("\n[NAS BACKUP]")
    log_lines.append(f"  Destination: {NAS_BACKUP}")

    try:
        nas_count, nas_ok, nas_unchanged = copy_files_to_destination(
            SOURCE_DIR, NAS_BACKUP, folder_name, log_lines
        )
        if nas_ok:
            print(f"  NAS backup complete — {nas_count} file(s) copied.")
        else:
            print("  NAS backup had errors — check the log file.")
    except Exception as nas_error:
        # This catches things like the drive letter not being mapped at all
        print(f"  NAS backup FAILED: {nas_error}")
        log_lines.append(f"  NAS backup FAILED: {nas_error}")
        nas_ok = False
        nas_count = 0       # No files were copied if the whole backup failed
        nas_unchanged = []  # No unchanged list if the whole backup failed

    # --- Step 4: Copy to local backup ---
    # This runs regardless of what happened with the NAS above
    print("\nCopying to local backup...")
    log_lines.append("\n[LOCAL BACKUP]")
    log_lines.append(f"  Destination: {LOCAL_BACKUP}")

    try:
        local_count, local_ok, local_unchanged = copy_files_to_destination(
            SOURCE_DIR, LOCAL_BACKUP, folder_name, log_lines
        )
        if local_ok:
            print(f"  Local backup complete — {local_count} file(s) copied.")
        else:
            print("  Local backup had errors — check the log file.")
    except Exception as local_error:
        print(f"  Local backup FAILED: {local_error}")
        log_lines.append(f"  Local backup FAILED: {local_error}")
        local_ok = False
        local_count = 0       # No files were copied if the whole backup failed
        local_unchanged = []  # No unchanged list if the whole backup failed

    # --- Step 5: Copy the change log CSV into both backup folders ---
    # The change log is maintained by plc_change_watcher.py and records every
    # operator-documented change.  Including it in each backup snapshot means
    # the archived copy reflects what was known at the time of that backup.
    # Incremental rule: skip if mtime matches the copy in the previous backup.
    # No popup is shown for this file — just log UNCHANGED and move on.
    print("\nCopying change log...")
    log_lines.append("\n[CHANGE LOG BACKUP]")
    log_lines.append(f"  Source: {CHANGE_LOG}")

    _change_log_name = os.path.basename(CHANGE_LOG)

    for _dest_root, _dest_label, _prev_backup in [
        (NAS_BACKUP,   "NAS",   prev_nas_backup),
        (LOCAL_BACKUP, "Local", prev_local_backup),
    ]:
        _dest_folder = os.path.join(_dest_root, folder_name)

        # If the backup folder was never created (e.g. destination offline), skip
        if not os.path.isdir(_dest_folder):
            log_lines.append(
                f"  WARNING ({_dest_label}): Backup folder not found — "
                f"skipping change log copy"
            )
            continue

        # If the change log source file does not exist, warn and continue
        if not os.path.exists(CHANGE_LOG):
            log_lines.append(
                f"  WARNING ({_dest_label}): Change log not found — {CHANGE_LOG}"
            )
            continue

        # Compare mtime against the copy in the previous backup, if one exists
        _prev_file = (
            os.path.join(_prev_backup, _change_log_name) if _prev_backup else None
        )
        if (_prev_file
                and os.path.exists(_prev_file)
                and os.path.getmtime(CHANGE_LOG) == os.path.getmtime(_prev_file)):
            log_lines.append(
                f"  UNCHANGED (skipped): {_change_log_name} ({_dest_label})"
            )
            continue

        try:
            shutil.copy2(CHANGE_LOG, os.path.join(_dest_folder, _change_log_name))
            log_lines.append(f"  COPIED: {_change_log_name} ({_dest_label})")
        except Exception as _copy_error:
            log_lines.append(
                f"  WARNING ({_dest_label}): Could not copy "
                f"{_change_log_name} — {_copy_error}"
            )

    # --- Step 6: Print final summary ---
    print("\n" + "=" * 50)
    print("SUMMARY")
    print("=" * 50)
    print(f"  NAS backup:   {'OK' if nas_ok else 'FAILED — see log'}")
    print(f"  Local backup: {'OK' if local_ok else 'FAILED — see log'}")
    print(f"  Log file:     {LOG_FILE}")
    print("=" * 50)

    log_lines.append("\n[SUMMARY]")
    log_lines.append(f"  NAS backup:   {'OK' if nas_ok else 'FAILED'}")
    log_lines.append(f"  Local backup: {'OK' if local_ok else 'FAILED'}")

    # Combine the unchanged ACD lists from both destinations into one set.
    # Using a set removes duplicates (the same filename won't appear twice).
    # Using union (|) means: if a file is UNCHANGED on either destination,
    # we warn the operator — even if only one destination had a previous backup.
    unchanged_acd_set = set(nas_unchanged) | set(local_unchanged)
    # Keep only the most recently dated .ACD file per processor name
    unchanged_acd_set = set(_keep_latest_per_processor(unchanged_acd_set))

    if unchanged_acd_set:
        log_lines.append(
            f"  Unchanged ACD files (popup will be shown): "
            f"{', '.join(sorted(unchanged_acd_set))}"
        )

    # --- Step 7: Write everything to the log file ---
    write_log(LOG_FILE, log_lines)
    print("\nLog file updated.")

    # Return a tuple so main() has everything it needs to pick the right popup.
    # nas_count + local_count = total copy operations across both destinations.
    return (unchanged_acd_set, nas_ok, local_ok, nas_count)


# =============================================================================
# FUNCTION: main
# =============================================================================
# This is the entry point — it runs the backup and then checks whether the
# operator warning popup needs to be shown.
#
# Think of it like the main breaker panel: it coordinates which circuits run.
# =============================================================================

def main():
    # Run the full backup and unpack the four values it now returns
    unchanged, nas_ok, local_ok, files_copied = run_backup()

    # We import backup_popup here (not at the top of the file) so that
    # tkinter is only loaded when a popup is actually needed. On a headless
    # Task Scheduler run with no desktop, importing tkinter can cause errors.
    if unchanged:
        # Some ACD files were not saved since the last backup — warn the operator.
        # We pass a lambda instead of run_backup directly so that show_warning
        # still receives a plain set from the callback (not the full tuple).
        # The [0] extracts just the unchanged_acd_set from the tuple.
        from backup_popup import show_warning
        show_warning(unchanged, lambda: run_backup()[0])
    else:
        # All files were up to date — show the clean success summary popup
        from backup_popup import show_success
        show_success(nas_ok, local_ok, files_copied)


# =============================================================================
# ENTRY POINT
# =============================================================================
# This line means: only run main() if this script is run directly.
# It won't run automatically if another script imports this file.
# Think of it like a manual ON switch on a disconnect — it only fires
# when you intentionally flip it.
# =============================================================================

if __name__ == "__main__":
    main()
