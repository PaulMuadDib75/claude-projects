# PLC Change Watcher

Monitors RSLogix 5000 `.ACD` files for saves and prompts the operator to
document what changed. All entries are written automatically to a CSV change log.

---

## What It Does

- Watches `C:\PLC\CURRENT_PLC_VIRSION\2026` for `.ACD` file saves
- Pops up a form on monitor 2 asking the operator to document the change
- Writes every entry to `plc_change_log.csv` in the same folder as the script
- Runs silently in the system tray — no terminal window required

---

## Requirements

- Windows 10
- Python 3.x
- The following packages (install via offline pip if no internet access):
  - `watchdog`
  - `pystray`
  - `Pillow`

### Offline Installation

```powershell
# On an internet-connected machine — download packages
pip download watchdog pystray pillow -d C:\plc_watcher_packages

# On the production machine — install from the downloaded folder
pip install --no-index --find-links C:\plc_watcher_packages watchdog pystray pillow
```

---

## Running the Script

**With terminal (development / testing):**
```powershell
python plc_change_watcher.py
```

**Without terminal (production):**
```powershell
pythonw plc_change_watcher.py
```

A blue circle will appear in the Windows system tray confirming the watcher is running.
Right-click the tray icon and select **Exit** to stop it.

---

## Running at Startup (Task Scheduler)

1. Open Task Scheduler (`Win + R` → `taskschd.msc`)
2. Click **Create Task**
3. **General tab:** Name it `PLC Change Watcher`. Check *Run with highest privileges*
4. **Triggers tab:** New → At log on → your user account
5. **Actions tab:** New → Start a program
   - Program/script: `C:\Users\Administrator\AppData\Local\Programs\Python\Python314\pythonw.exe`
   - Add arguments: `plc_change_watcher.py`
   - Start in: `C:\path\to\script\folder` *(no quotes)*
6. **Conditions tab:** Uncheck *Start only if on AC power*
7. **Settings tab:** Check *Do not start a new instance if already running*

---

## Configuration

Open `plc_change_watcher.py` and update these constants at the top of the file:

| Constant | Default | Description |
|---|---|---|
| `WATCH_FOLDER` | `C:\PLC\CURRENT_PLC_VIRSION\2026` | Folder containing .ACD files |
| `DEBOUNCE_SECONDS` | `60` | Minimum seconds between popups for the same file |
| `LOG_FILE` | Same folder as script | Path to the CSV change log |
| `MONITOR_2_X` | `1920` | X coordinate where monitor 2 starts |
| `MONITOR_2_Y` | `0` | Y coordinate where monitor 2 starts |
| `MONITOR_2_WIDTH` | `1920` | Width of monitor 2 in pixels |
| `MONITOR_2_HEIGHT` | `1080` | Height of monitor 2 in pixels |

---

## Change Log File

`plc_change_log.csv` is created automatically on first run.

| Column | Description |
|---|---|
| Timestamp | Date and time the change was logged |
| Who Made the Change | Operator name as entered |
| Processor | Auto-detected from the .ACD filename |
| Routine | As entered by the operator |
| Rung | As entered by the operator |
| Description | What was changed |
| Reason | Why the change was made |
| Authorized By | Who approved the change |
| Filename | The .ACD file that triggered the popup |

---

## Files

| File | Description |
|---|---|
| `plc_change_watcher.py` | Main script |
| `plc_change_log.csv` | Auto-created change log (do not delete) |
| `README.md` | This file |

---

## Troubleshooting

| Problem | Fix |
|---|---|
| Tray icon doesn't appear | Confirm packages are installed: `python -c "import watchdog, pystray, PIL"` |
| Popup doesn't appear on file save | Confirm `WATCH_FOLDER` path is correct and the file has uppercase `.ACD` extension |
| Two popups appear on one save | RSLogix backup files are triggering the watcher — confirm the extension filter uses `Path(path).suffix != ".ACD"` without `.upper()` |
| Popup appears behind other windows | Confirm `win.attributes('-topmost', True)` is present in `show_change_form()` |
| Popup on wrong monitor | Check `MONITOR_2_X` matches where monitor 2 starts in your display settings |
| Task Scheduler task won't run | Check Start in field has no quotes around the path |
| CSV not created | Confirm the script has write permission to its folder |
