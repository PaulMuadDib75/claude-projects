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
- Project folder: C:\claude\projects\plc-change-watcher\
- Development machine: C:\claude\projects\plc-change-watcher\
- Production machine: separate machine, same script, different path

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
- Run with pythonw.exe (or .pyw extension) for no-terminal operation

## Form fields
- Who Made the Change — text entry, required
- Processor/Program — auto-filled from filename (strip .ACD), read-only
- Routine — text entry, required
- Rung — text entry, required
- Description of Change — multi-line text entry, required
- Reason for Change — text entry, required
- Authorized By — text entry, required
- Date/Time — auto-filled, read-only

## CSV columns
Timestamp, Who Made the Change, Processor, Routine, Rung,
Description, Reason, Authorized By, Filename

## Rules
- watchdog for file monitoring — no polling loops
- Case-sensitive suffix check: Path(path).suffix != ".ACD" — do not use .upper()
- Standard library + watchdog, pystray, Pillow only — no other third-party packages
- Large readable fonts — operators are not technical users
- All fields required — no partial submissions accepted, empty fields highlighted yellow
- Cancel button must show confirmation dialog before closing without logging
- Filename in CSV row uses Path(filepath).name — not the full path
- One popup per file per 60-second window — debounce duplicate save events
- Comment every section thoroughly
- tkinter popup must not block the file watcher thread
- No terminal window in production — run with pythonw.exe or as .pyw
- No main tkinter window — tray icon is the only persistent visible indicator
