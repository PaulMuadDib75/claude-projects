# PLC Change Watcher

## What this is
A file watcher tool for Windows 10 that monitors a folder containing RSLogix 5000
.ACD files. When a file modification is detected, it launches a tkinter popup form
prompting the operator to document the change. Entries are written to a CSV change log.

## Target user
Plant floor operators — non-technical. No terminal interaction after launch.
GUI only. Must be simple and obvious to use.

## Environment
- Windows 10
- Python 3.14 — pythonw.exe at C:\Users\Administrator\AppData\Local\Programs\Python\Python314\pythonw.exe
- Python standard library + watchdog, pystray, Pillow (pre-installed via offline pip)
- Monitor folder: C:\PLC\CURRENT_PLC_VIRSION\2026
- Four processors — multiple .ACD files exist in the monitored folder
- Log file: plc_change_log.csv (auto-created in same folder as script)
- Development machine: C:\claude\projects\plc-change-watcher\
- Production machine: C:\Python\PLC-change-watcher\
- Both machines must be kept in sync manually via Copy-Item after changes

## Architecture
- watchdog library for event-driven file change detection
- Case-sensitive .ACD extension filter — only uppercase .ACD triggers a popup
  (RSLogix backup files use lowercase .acd and are intentionally ignored)
- 60-second debounce per file to prevent duplicate popups on rapid saves
- tkinter for all GUI (popup form only — no main window, no terminal window)
- win.attributes('-topmost', True) forces popup above all other windows including Wonderware HMI
- Popup centered on monitor 2 (1920x1080, starts at X=1920)
- pystray for Windows system tray icon with right-click Exit menu
- Pillow for programmatic tray icon generation (no external .ico file)
- csv module for log writing (standard library)
- Single file: plc_change_watcher.py
- Three-thread model: main thread (tkinter), watchdog daemon thread, pystray daemon thread
- Run with pythonw.exe for no-terminal operation
- Task Scheduler launches at login automatically

## Form fields (in order)
1. Who Made the Change — text entry, required
2. Processor/Program — auto-filled from filename (strip .ACD), read-only
3. Routine — text entry, required, validates yellow on empty
4. Equipment Name / Number — text entry, required, validates yellow on empty
5. Rung — text entry, required, validates yellow on empty
6. Description of Change — multi-line text entry, required
7. Reason for Change — text entry, required
8. Authorized By — text entry, required
9. Date/Time — auto-filled, read-only

## CSV columns (in order)
Timestamp, Who Made the Change, Processor, Routine, Equipment Name / Number,
Rung, Description, Reason, Authorized By, Filename

## Rules
- watchdog for file monitoring — no polling loops
- Case-sensitive suffix check: Path(path).suffix != ".ACD" — do not use .upper()
- Standard library + watchdog, pystray, Pillow only — no other third-party packages
- Large readable fonts — operators are not technical users
- All fields required — no partial submissions accepted
- Routine, Equipment Name / Number, and Rung validate on submit — empty fields highlight yellow (HIGHLIGHT_BG)
- Cancel button must show confirmation dialog before closing without logging
- Filename in CSV row uses Path(filepath).name — not the full path
- One popup per file per 60-second window — debounce duplicate save events
- ensure_csv_headers() must be called inside on_submit() before every CSV write
  (not just at startup) — ensures headers are always present even if file is deleted
  while the script is running
- Comment every section thoroughly
- tkinter popup must not block the file watcher thread
- No terminal window in production — run with pythonw.exe
- No main tkinter window — tray icon is the only persistent visible indicator
