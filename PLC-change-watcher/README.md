# PLC Change Watcher

Monitors RSLogix 5000 `.ACD` files for saves and prompts the operator to
document what changed. All entries are written automatically to a CSV change log.

---

## What It Does

- Watches `C:\PLC\CURRENT_PLC_VIRSION\2026` for `.ACD` file saves
- Pops up a form asking the operator to document the change
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
   - Program/script: `C:\path\to\pythonw.exe`
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
| `DEBOUNCE_SECONDS` | `30` | Minimum seconds between popups for the same file |
| `LOG_FILE` | Same folder as script | Path to the CSV change log |

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
| Popup doesn't appear on file save | Confirm `WATCH_FOLDER` path is correct and the file is `.ACD` |
| Task Scheduler task won't run | Check Start in field has no quotes around the path |
| CSV not created | Confirm the script has write permission to its folder |
