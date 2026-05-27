# PLC Backup Tool

## What this is
Python tool that backs up RSLogix 5000 PLC program files from the
active program directory to a NAS and a local destination.
Uses incremental logic for .ACD files and warns the operator
if programs have not been saved since the last backup.
Also provides backup_single_file() for on-demand backups triggered
by the PLC Change Watcher's Backup Now button.

## Source directory
C:\PLC\CURRENT_PLC_VIRSION\2026

## Destinations (on programming terminal — DO NOT CHANGE)
- NAS:   Z:\PLC_Programs
- Local: C:\Python\NAS_Backups\PLC
- Log:   Z:\PLC_Programs\plc_backup_log.txt

## Backup subfolder structure
Scheduled weekly runs:
  Z:\PLC_Programs\Scheduled_Backups\PLC_Backup_YYYY-MM-DD_HHMM\
  C:\Python\NAS_Backups\PLC\Scheduled_Backups\PLC_Backup_YYYY-MM-DD_HHMM\

On-demand runs (Backup Now button from change watcher):
  Z:\PLC_Programs\On_Demand_Backups\PLC_Backup_YYYY-MM-DD_HHMM\
  C:\Python\NAS_Backups\PLC\On_Demand_Backups\PLC_Backup_YYYY-MM-DD_HHMM\

## Files
- plc_backup.py   — main backup script
- backup_popup.py — warning, success, and on-demand success popups

## Intended workflow — scheduled backup
1. Task Scheduler runs plc_backup.py weekly
2. Warning popup lists most recent .ACD per processor not saved since last backup
3. Operator saves programs in RSLogix 5000 (File → Save As)
4. Operator clicks Run Backup Again
5. Success popup confirms backup complete

## Intended workflow — on-demand backup
1. Operator saves a file in RSLogix 5000
2. Change watcher popup fires
3. Operator fills in change details and clicks Backup Now
4. plc_change_watcher.py calls backup_single_file() from this module
5. Single file backed up to On_Demand_Backups on both destinations
6. show_on_demand_success() called from backup_popup.py to confirm result

## Processors backed up (4 total)
- Rewash
- SandStone
- Shiploader
- UpperLowerPrimaryCrush

## Incremental logic — .ACD files only
build_file_index() scans BOTH Scheduled_Backups and On_Demand_Backups
subfolders, newest to oldest, mapping each filename to its most recent
backed-up copy. Each file is compared against its own most recent backup
individually — not just the latest folder overall.

- NEW:       file not found in any previous backup — copy it
- CHANGED:   file found but date modified differs — copy it
- UNCHANGED: file found and date modified matches — skip it,
             flag it in the warning popup

## Non-ACD files (BAK, Recovery)
Always copied regardless — no incremental logic applied.
.Sem and .Wrk files are RSLogix session locks — always skipped
with a WARNING log entry, this is expected and harmless.

## Popup display
All popups display on monitor 2 (right monitor, 1920x1080).
Positioning constants are defined at the top of backup_popup.py.

## Task Scheduler
Weekly schedule. Uses pythonw.exe — no terminal window.
Terminal must remain logged in at all times.

## Rules
- Comment all code in plain English
- Standard library only — no pip installs
- Never change destination paths without explicit instruction
- Never modify incremental logic without updating this file
