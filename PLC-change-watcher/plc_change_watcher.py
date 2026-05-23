# plc_change_watcher.py
#
# Monitors a folder for RSLogix 5000 .ACD file saves and pops up a form
# so operators can document the change. Entries are written to a CSV log.
#
# Run with:   python plc_change_watcher.py       (shows terminal)
#             pythonw plc_change_watcher.py      (no terminal — tray only)

import csv
import queue
import threading
import time
from datetime import datetime
from pathlib import Path

import tkinter as tk
from tkinter import messagebox

from PIL import Image, ImageDraw
import pystray
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

# ---------------------------------------------------------------------------
# Configuration constants
# ---------------------------------------------------------------------------

# Folder that contains the .ACD files to watch
WATCH_FOLDER = r"C:\PLC\CURRENT_PLC_VIRSION\2026"

# CSV log file lives in the same folder as this script
LOG_FILE = Path(__file__).parent / "plc_change_log.csv"

# Column headers for the CSV — order must match the row written in on_submit()
CSV_HEADERS = [
    "Timestamp",
    "Who Made the Change",
    "Processor",
    "Routine",
    "Rung",
    "Description",
    "Reason",
    "Authorized By",
    "Filename",
]

# How many seconds must pass before the same file can trigger another popup
DEBOUNCE_SECONDS = 30

# Font used for all widgets — minimum 12pt for plant-floor readability
FONT = ("Arial", 13)
FONT_BOLD = ("Arial", 13, "bold")

# Background colour for read-only display labels so operators know not to edit them
READONLY_BG = "#e8e8e8"

# Background colour used to highlight empty required fields on a failed submit
HIGHLIGHT_BG = "#fff3cd"


# ---------------------------------------------------------------------------
# Tray icon image — generated with Pillow, no external file required
# ---------------------------------------------------------------------------

def create_tray_image():
    """Return a 64x64 Pillow Image: white background with a solid blue circle."""
    img = Image.new("RGB", (64, 64), color=(255, 255, 255))
    draw = ImageDraw.Draw(img)
    # Draw a solid blue circle inset slightly from the edges
    draw.ellipse([4, 4, 60, 60], fill=(0, 120, 212))
    return img


# ---------------------------------------------------------------------------
# CSV helper — create the log file with headers if it doesn't exist yet
# ---------------------------------------------------------------------------

def ensure_csv_headers():
    """Write the CSV header row if the log file is new or empty."""
    write_headers = not LOG_FILE.exists() or LOG_FILE.stat().st_size == 0
    if write_headers:
        with open(LOG_FILE, "a", newline="", encoding="utf-8") as f:
            csv.writer(f).writerow(CSV_HEADERS)


# ---------------------------------------------------------------------------
# Watchdog event handler — fires when any file in the watched folder changes
# ---------------------------------------------------------------------------

class PLCChangeHandler(FileSystemEventHandler):
    """Listens for file-modified events and enqueues .ACD filenames."""

    def __init__(self, file_queue):
        super().__init__()
        self.file_queue = file_queue
        # Maps absolute filepath string → time.time() of last popup for that file
        self.last_popup_time = {}

    def on_modified(self, event):
        # Ignore directory-level events (e.g. folder timestamp updates)
        if event.is_directory:
            return

        path = event.src_path

        # Only care about RSLogix 5000 project files
        if Path(path).suffix.upper() != ".ACD":
            return

        # Debounce: RSLogix sometimes fires several modified events per save.
        # Ignore the event if a popup was already triggered for this file
        # within the last DEBOUNCE_SECONDS seconds.
        now = time.time()
        if now - self.last_popup_time.get(path, 0) < DEBOUNCE_SECONDS:
            return

        # Record this as the latest popup time for the file, then enqueue
        self.last_popup_time[path] = now
        self.file_queue.put(path)


# ---------------------------------------------------------------------------
# Popup form — always a Toplevel, never a new Tk() root
# ---------------------------------------------------------------------------

def show_change_form(root, filepath):
    """
    Open the change-log entry form as a modal Toplevel window.
    Must be called from the main (tkinter) thread only.
    """

    # Auto-filled values derived from the file path
    processor_name = Path(filepath).stem
    timestamp_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # -----------------------------------------------------------------------
    # Window setup
    # -----------------------------------------------------------------------
    win = tk.Toplevel(root)
    win.title("PLC Change Log")
    win.resizable(False, False)
    win.grab_set()          # Keep keyboard/mouse focus on this window
    win.lift()              # Bring above other windows (e.g. RSLogix)
    win.focus_force()       # Pull focus even from a background application

    # Common grid padding applied to every row
    PAD = {"padx": 15, "pady": 8}

    # -----------------------------------------------------------------------
    # Helper: add a labelled field row and return the entry widget
    # -----------------------------------------------------------------------
    def add_entry_row(parent, row, label_text):
        tk.Label(parent, text=label_text, font=FONT_BOLD, anchor="w").grid(
            row=row, column=0, sticky="w", **PAD
        )
        entry = tk.Entry(parent, font=FONT, width=40)
        entry.grid(row=row, column=1, sticky="ew", **PAD)
        return entry

    # -----------------------------------------------------------------------
    # Field 1 — Who Made the Change
    # -----------------------------------------------------------------------
    entry_who = add_entry_row(win, 0, "Who Made the Change:")

    # -----------------------------------------------------------------------
    # Field 2 — Processor/Program (read-only, auto-filled from filename)
    # -----------------------------------------------------------------------
    tk.Label(win, text="Processor / Program:", font=FONT_BOLD, anchor="w").grid(
        row=1, column=0, sticky="w", **PAD
    )
    tk.Label(win, text=processor_name, font=FONT, bg=READONLY_BG,
             anchor="w", relief="sunken", width=40).grid(
        row=1, column=1, sticky="ew", **PAD
    )

    # -----------------------------------------------------------------------
    # Field 3 — Routine
    # -----------------------------------------------------------------------
    entry_routine = add_entry_row(win, 2, "Routine:")

    # -----------------------------------------------------------------------
    # Field 4 — Rung
    # -----------------------------------------------------------------------
    entry_rung = add_entry_row(win, 3, "Rung:")

    # -----------------------------------------------------------------------
    # Field 5 — Description of Change (multi-line Text widget)
    # -----------------------------------------------------------------------
    tk.Label(win, text="Description of Change:", font=FONT_BOLD, anchor="w").grid(
        row=4, column=0, sticky="nw", **PAD
    )
    text_desc = tk.Text(win, font=FONT, width=40, height=6, wrap="word")
    text_desc.grid(row=4, column=1, sticky="ew", **PAD)

    # -----------------------------------------------------------------------
    # Field 6 — Reason for Change
    # -----------------------------------------------------------------------
    entry_reason = add_entry_row(win, 5, "Reason for Change:")

    # -----------------------------------------------------------------------
    # Field 7 — Authorized By
    # -----------------------------------------------------------------------
    entry_auth = add_entry_row(win, 6, "Authorized By:")

    # -----------------------------------------------------------------------
    # Field 8 — Date/Time (read-only, auto-filled)
    # -----------------------------------------------------------------------
    tk.Label(win, text="Date / Time:", font=FONT_BOLD, anchor="w").grid(
        row=7, column=0, sticky="w", **PAD
    )
    tk.Label(win, text=timestamp_str, font=FONT, bg=READONLY_BG,
             anchor="w", relief="sunken", width=40).grid(
        row=7, column=1, sticky="ew", **PAD
    )

    # -----------------------------------------------------------------------
    # Submit logic — validate, write CSV, confirm, close
    # -----------------------------------------------------------------------
    def on_submit():
        # Collect all field values
        who = entry_who.get().strip()
        routine = entry_routine.get().strip()
        rung = entry_rung.get().strip()
        description = text_desc.get("1.0", "end-1c").strip()
        reason = entry_reason.get().strip()
        authorized = entry_auth.get().strip()

        # Map each value to its widget so we can highlight empty ones
        field_map = [
            (who, entry_who),
            (routine, entry_routine),
            (rung, entry_rung),
            (description, text_desc),
            (reason, entry_reason),
            (authorized, entry_auth),
        ]

        # Reset all backgrounds first (in case the user corrected a field)
        for widget in (entry_who, entry_routine, entry_rung,
                       text_desc, entry_reason, entry_auth):
            widget.config(bg="white")

        # Highlight any empty required field
        missing = False
        for value, widget in field_map:
            if not value:
                widget.config(bg=HIGHLIGHT_BG)
                missing = True

        if missing:
            messagebox.showwarning(
                "Missing Fields",
                "All fields are required.\n\nPlease fill in the highlighted fields.",
                parent=win,
            )
            return  # Do not close the form

        # All fields present — write one row to the CSV log
        row = [
            timestamp_str,
            who,
            processor_name,
            routine,
            rung,
            description,
            reason,
            authorized,
            filepath,
        ]
        with open(LOG_FILE, "a", newline="", encoding="utf-8") as f:
            csv.writer(f).writerow(row)

        # Confirm and close
        messagebox.showinfo("Logged", "Change logged successfully.", parent=win)
        win.destroy()

    # -----------------------------------------------------------------------
    # Submit button
    # -----------------------------------------------------------------------
    tk.Button(
        win,
        text="Submit Change",
        font=FONT_BOLD,
        bg="#0078d4",
        fg="white",
        activebackground="#005fa3",
        activeforeground="white",
        padx=20,
        pady=8,
        command=on_submit,
    ).grid(row=8, column=0, columnspan=2, pady=15)


# ---------------------------------------------------------------------------
# Main-thread queue poller — launched with root.after() every 500 ms
# ---------------------------------------------------------------------------

def check_queue(root, file_queue):
    """
    Drain the inter-thread queue and open a form for each pending file.
    Re-schedules itself so it runs continuously while tkinter is alive.
    """
    while not file_queue.empty():
        filepath = file_queue.get_nowait()
        show_change_form(root, filepath)

    # Schedule the next poll in 500 ms
    root.after(500, check_queue, root, file_queue)


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main():
    # Print a startup message — visible when launched with python.exe.
    # Silently dropped when launched with pythonw.exe (no console window).
    print(f"PLC Change Watcher started.")
    print(f"Monitoring: {WATCH_FOLDER}")
    print(f"Log file:   {LOG_FILE}")
    print("Right-click the tray icon to exit.")

    # Create the CSV log file (with headers) if it doesn't exist yet
    ensure_csv_headers()

    # -----------------------------------------------------------------------
    # Tkinter root — hidden; only Toplevel popups are ever shown to the user
    # -----------------------------------------------------------------------
    root = tk.Tk()
    root.withdraw()

    # -----------------------------------------------------------------------
    # Inter-thread queue: watchdog puts filenames here; main thread reads them
    # -----------------------------------------------------------------------
    file_queue = queue.Queue()

    # Start polling the queue every 500 ms from the main thread
    root.after(500, check_queue, root, file_queue)

    # -----------------------------------------------------------------------
    # Watchdog observer — runs in its own daemon thread (managed by watchdog)
    # -----------------------------------------------------------------------
    handler = PLCChangeHandler(file_queue)
    observer = Observer()
    observer.schedule(handler, WATCH_FOLDER, recursive=False)
    observer.start()

    # -----------------------------------------------------------------------
    # System tray icon
    # -----------------------------------------------------------------------
    tray_image = create_tray_image()
    tray_tooltip = f"PLC Change Watcher\nMonitoring: {WATCH_FOLDER}"

    def on_exit(icon, item):
        """Called when the user clicks Exit in the tray menu."""
        observer.stop()     # Signal the watchdog thread to stop
        icon.stop()         # Stop the pystray Win32 message loop
        root.quit()         # Exit the tkinter mainloop

    tray_menu = pystray.Menu(pystray.MenuItem("Exit", on_exit))
    tray_icon = pystray.Icon(
        name="PLC Watcher",
        icon=tray_image,
        title=tray_tooltip,
        menu=tray_menu,
    )

    # Run the tray icon in a daemon thread so it doesn't block tkinter
    tray_thread = threading.Thread(target=tray_icon.run, daemon=True)
    tray_thread.start()

    # -----------------------------------------------------------------------
    # Tkinter main loop — blocks here; the other threads run concurrently.
    # Ctrl+C in a terminal will raise KeyboardInterrupt after mainloop exits.
    # -----------------------------------------------------------------------
    try:
        root.mainloop()
    except KeyboardInterrupt:
        pass
    finally:
        # Clean up the watchdog thread before the process exits
        observer.stop()
        observer.join()


if __name__ == "__main__":
    main()
