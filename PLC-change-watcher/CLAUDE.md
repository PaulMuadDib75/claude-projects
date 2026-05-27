# PLC Change Watcher

## What this is
Python tool that monitors RSLogix 5000 .ACD files for saves and prompts
the operator to document what changed. Entries are written to a CSV log.
Also integrates with the PLC Backup Tool via a "Backup Now" button.

## Deployment location (programming terminal)
C:\Python\PLC-change-watcher\

## Watch folder
C:\PLC\CURRENT_PLC_VIRSION\2026

## Files
- plc_change_watcher.py  — main script
- plc_change_log.csv     — auto-created change log (do not delete)

## Popup buttons
Two buttons appear on the change log form:

- Backup Now — logs the change to CSV (even if form is incomplete)
              AND backs up the single .ACD file to NAS and local
              On_Demand_Backups folder. Success popup confirms result.
- Cancel     — discards everything. Nothing logged, nothing backed up.

The Submit button was removed. Backup Now is the primary action.

## Integration with PLC Backup Tool
plc_change_watcher.py imports two functions from the backup tool
using sys.path pointing to the deployment location:

  sys.path.insert(0, r"C:\Python\NAS_Backups")
  from plc_backup import backup_single_file
  from backup_popup import show_on_demand_success

DO NOT change these paths without updating the backup tool deployment.

## Backup destinations (on programming terminal — DO NOT CHANGE)
On-demand backups triggered by Backup Now go to:
  NAS:   Z:\PLC_Programs\On_Demand_Backups\PLC_Backup_YYYY-MM-DD_HHMM\
  Local: C:\Python\NAS_Backups\PLC\On_Demand_Backups\PLC_Backup_YYYY-MM-DD_HHMM\

Each on-demand backup folder contains the .ACD file and plc_change_log.csv.

## Monitor
Popup displays on monitor 2 (right monitor, 1920x1080).
Positioning constants are at the top of plc_change_watcher.py.

## Task Scheduler
Runs at logon via Task Scheduler. Uses pythonw.exe — no terminal window.
Terminal must remain logged in at all times.

## Rules
- Comment all code in plain English
- Do not change backup destination paths without explicit instruction
- Do not change sys.path import paths without explicit instruction
- watchdog, pystray, Pillow are required (not standard library)
