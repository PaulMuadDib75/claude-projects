# =============================================================================
# backup_popup.py
# =============================================================================
#
# WHAT THIS MODULE DOES:
#   Shows a warning window when plc_backup.py detects that one or more .ACD
#   files have not been saved since the last backup. The window lists the
#   affected filenames and gives the operator two choices:
#     - "Run Backup Again" — triggers a fresh backup run and checks again
#     - "Cancel"           — closes the window without re-running
#
# HOW IT IS USED:
#   This module is imported by plc_backup.py — it is NOT meant to be run
#   directly. The show_warning() function is called from plc_backup.py
#   after a backup run finds unchanged .ACD files.
#
# REQUIRES:
#   Python standard library only — uses tkinter, which is included with
#   most Python installations. No pip installs needed.
#
# =============================================================================

import tkinter as tk  # tkinter is Python's built-in GUI toolkit (standard library)


# =============================================================================
# FUNCTION: show_warning
# =============================================================================
# Opens a warning window listing the .ACD files that have not been saved
# since the last backup. Waits for the operator to click a button, then
# either re-runs the backup or exits.
#
# Think of this like a lockout/tagout warning label — it stops the operator,
# identifies the problem, and requires a deliberate action before continuing.
#
# Parameters:
#   unchanged_files      — set or list of .ACD filenames (just the filename,
#                          no folder path) that were skipped in the backup
#   run_backup_callback  — a function with no arguments to call; it runs the
#                          backup again and returns a new set of unchanged
#                          filenames (empty set if all files are now saved)
# =============================================================================

def show_warning(unchanged_files, run_backup_callback):

    # --- Step 1: Create the main window ---
    root = tk.Tk()
    root.title("PLC Backup Warning")

    # Set the window width in pixels
    window_width = 500

    # Make the window taller if there are many files to show.
    # Base height is 300px; add 20px for each file beyond the first 5, up to 600px.
    file_count = len(unchanged_files)
    window_height = min(300 + max(0, (file_count - 5) * 20), 600)

    # Force tkinter to calculate window geometry before we try to center it
    root.update_idletasks()

    # Get the full screen dimensions so we can place the window in the center
    screen_width = root.winfo_screenwidth()
    screen_height = root.winfo_screenheight()

    # Calculate the top-left corner position to center the window on screen
    x_position = (screen_width - window_width) // 2
    y_position = (screen_height - window_height) // 2

    # Apply the size and position.
    # tkinter geometry strings look like "500x300+600+400":
    #   500  = window width in pixels
    #   300  = window height in pixels
    #   +600 = distance from left edge of screen
    #   +400 = distance from top edge of screen
    root.geometry(f"{window_width}x{window_height}+{x_position}+{y_position}")

    # Prevent the operator from resizing the window — keeps the layout clean
    root.resizable(False, False)

    # --- Step 2: Warning label at the top ---
    # Large bold red text grabs attention — like a red indicator lamp on a panel.
    # Font is bigger (16pt) so it is hard to miss on any screen.
    warning_label = tk.Label(
        root,
        text="WARNING: Unsaved ACD Files Detected",
        fg="red",                      # Starts red; flash loop will toggle this
        font=("Arial", 16, "bold"),    # Larger and bolder than before
        anchor="center"                # Text stays centred inside the label widget
    )
    warning_label.pack(pady=(15, 5))  # 15px gap above, 5px gap below

    # --- Step 2a: Flashing effect for the warning label ---
    # Capture the window background colour so we can "hide" the label by
    # matching it.  Alternating red → background → red every 500 ms makes
    # the label appear to flash without needing any threads.
    # Think of it like a flashing beacon light on a control panel — a relay
    # timer fires repeatedly and toggles the lamp on and off.
    bg_color = root.cget("bg")

    def flash_warning():
        # Read the label's current foreground colour
        current_color = warning_label.cget("fg")
        # Toggle: if it is red, make it invisible; otherwise make it red
        if current_color == "red":
            warning_label.config(fg=bg_color)
        else:
            warning_label.config(fg="red")
        # Schedule this function to run again in 500 ms — the loop continues
        # until the window is destroyed (mainloop exits)
        root.after(500, flash_warning)

    # Kick off the first flash after 500 ms
    root.after(500, flash_warning)

    # --- Step 3: Scrollable list of unchanged filenames ---
    # Using a Listbox with a Scrollbar so the list stays readable even with many files.
    # Think of this like a panel schedule — each circuit (file) gets its own labelled row.

    # A Frame groups the listbox and its scrollbar so they sit side by side
    list_frame = tk.Frame(root)
    list_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=5)

    # The scrollbar goes on the right side of the listbox
    scrollbar = tk.Scrollbar(list_frame, orient=tk.VERTICAL)
    scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

    # The Listbox shows one filename per row
    file_listbox = tk.Listbox(
        list_frame,
        yscrollcommand=scrollbar.set,   # Connect the scrollbar to this listbox
        font=("Courier", 10),           # Monospace font — filenames line up cleanly
        height=min(file_count, 8)       # Show up to 8 rows; scrollbar handles the rest
    )
    file_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

    # Connect the listbox back to the scrollbar so they move together
    scrollbar.config(command=file_listbox.yview)

    # Fill the listbox with the unchanged filenames, sorted alphabetically
    for filename in sorted(unchanged_files):
        file_listbox.insert(tk.END, filename)

    # --- Step 4: Instruction text ---
    # Tell the operator exactly what to do next
    instruction_label = tk.Label(
        root,
        text=(
    	    "The above programs have not been saved since the last backup.\n\n"
    	    "In RSLogix 5000: File → Save As\n"
    	    "Use naming convention: ProgramName_YYYY_MM_DD.ACD\n"
    	    "Example: Rewash_2026_05_20.ACD\n\n"
    	    "Save each program then click Run Backup Again."
	),
        justify=tk.CENTER,
        wraplength=460,     # Wrap text so it fits within the 500px window (with margins)
        font=("Arial", 10)
    )
    instruction_label.pack(pady=(5, 10))

    # --- Step 5: Buttons ---

    # A Frame holds the two buttons side by side
    button_frame = tk.Frame(root)
    button_frame.pack(pady=(0, 15))

    # This function runs when the operator clicks "Run Backup Again"
    def on_run_again():
        # Close the current window before re-running — prevents ghost windows stacking up
        root.destroy()

        # Call the backup function that was passed in from plc_backup.py.
        # It runs the full backup and returns a new set of unchanged filenames.
        new_unchanged = run_backup_callback()

        if new_unchanged:
            # Some files are STILL unchanged after the re-run — show the warning again
            # with the updated list. This opens a fresh window and checks once more.
            show_warning(new_unchanged, run_backup_callback)
        # If new_unchanged is empty, all files have been saved — fall through and exit cleanly

    # This function runs when the operator clicks "Cancel"
    def on_cancel():
        # Close the window without re-running anything
        root.destroy()

    # "Run Backup Again" button — green background signals an affirmative action
    run_again_btn = tk.Button(
        button_frame,
        text="Run Backup Again",
        command=on_run_again,
        font=("Arial", 10, "bold"),
        bg="#4CAF50",       # Green background
        fg="white",
        padx=10,
        pady=5
    )
    run_again_btn.pack(side=tk.LEFT, padx=(0, 15))  # Place left, with a gap before Cancel

    # "Cancel" button — neutral styling, closes without any action
    cancel_btn = tk.Button(
        button_frame,
        text="Cancel",
        command=on_cancel,
        font=("Arial", 10),
        padx=10,
        pady=5
    )
    cancel_btn.pack(side=tk.LEFT)

    # --- Step 6: Start the event loop ---
    # mainloop() hands control to tkinter and waits for the operator to click a button.
    # It blocks here until root.destroy() is called — by either on_run_again or on_cancel.
    root.mainloop()


# =============================================================================
# FUNCTION: show_success
# =============================================================================
# Opens a clean confirmation window after a successful backup run.
# Shows whether the NAS and local destinations succeeded, and how many
# files were copied in total.
#
# No flashing here — this is a calm green "all clear" signal, like a green
# pilot light that tells you the circuit is energised and healthy.
#
# Parameters:
#   nas_ok       — True if the NAS backup completed without errors
#   local_ok     — True if the local backup completed without errors
#   files_copied — total number of files copied across both destinations
# =============================================================================

def show_success(nas_ok, local_ok, files_copied):

    # --- Step 1: Create the main window ---
    root = tk.Tk()
    root.title("Backup Successful")
    root.geometry("400x250")     # Fixed size — summary fits comfortably here
    root.resizable(False, False) # Keep layout clean by preventing resizing

    # Centre the window on screen (same pattern used in show_warning)
    root.update_idletasks()
    screen_width  = root.winfo_screenwidth()
    screen_height = root.winfo_screenheight()
    x_position = (screen_width  - 400) // 2
    y_position = (screen_height - 250) // 2
    root.geometry(f"400x250+{x_position}+{y_position}")

    # --- Step 2: "Backup Successful" header in green ---
    # Green text signals success — like a green pilot lamp meaning "circuit OK"
    header_label = tk.Label(
        root,
        text="Backup Successful",
        fg="green",                    # Green = all clear
        font=("Arial", 16, "bold"),    # Large and bold so it is easy to read
        anchor="center"
    )
    header_label.pack(pady=(20, 10))

    # --- Step 3: Summary lines ---
    # Build the NAS status string: "OK" if it worked, "FAILED" if it did not
    nas_status   = "OK"     if nas_ok   else "FAILED"
    local_status = "OK"     if local_ok else "FAILED"

    # A Frame keeps the summary lines grouped in the centre of the window
    summary_frame = tk.Frame(root)
    summary_frame.pack()

    # Three summary lines, each on its own Label row
    for summary_text in [
        f"NAS Backup:              {nas_status}",
        f"Local Backup:            {local_status}",
        f"Files copied this run:  {files_copied}",
    ]:
        tk.Label(
            summary_frame,
            text=summary_text,
            font=("Arial", 11),
            justify=tk.CENTER
        ).pack(pady=4)

    # --- Step 4: OK button at the bottom ---
    # Clicking OK calls root.destroy(), which ends mainloop and closes the window
    ok_btn = tk.Button(
        root,
        text="OK",
        command=root.destroy,
        font=("Arial", 10, "bold"),
        padx=20,
        pady=5
    )
    ok_btn.pack(pady=15)

    # --- Step 5: Start the event loop ---
    # Blocks here until the operator clicks OK
    root.mainloop()


# =============================================================================
# ENTRY POINT GUARD
# =============================================================================
# This module is meant to be imported by plc_backup.py, not run on its own.
# If someone tries to run it directly, we print a helpful message instead of
# opening an empty popup window with no files to display.
# =============================================================================

if __name__ == "__main__":
    print("This module is meant to be imported by plc_backup.py, not run directly.")
