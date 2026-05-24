# PLC Backup Tool

## What this is
Python tool that backs up RSLogix 5000 PLC program files from the
active program directory to a NAS and a local destination.
Uses incremental logic for .ACD files and warns the operator
if programs have not been saved since the last backup.

## Source directory
C:\PLC\CURRENT_PLC_VIRSION\2026

## Destinations
- NAS:   Z:\PLC_Programs  (mapped from \\192.168.0.65\Backups)
- Local: C:\Python\NAS_Backups\PLC
- Log:   Z:\PLC_Programs\plc_backup_log.txt

## Files
- plc_backup.py   — main backup script
- backup_popup.py — tkinter popup module (warning and success)

## Intended workflow
1. Backup runs (manually or via Task Scheduler)
2. Warning popup appears listing the most recent .ACD file
   per processor that has not changed since the last backup
3. Operator saves all four programs in RSLogix 5000 (File > Save As)
   using naming convention: ProgramName_YYYY_MM_DD.ACD
   Same-day saves use a letter suffix: ProgramName_YYYY_MM_DDa.ACD
4. Operator clicks Run Backup Again
5. RSLogix creates new dated .ACD files on save
6. Script detects them as NEW or CHANGED and copies them
7. Success popup confirms backup complete

The warning popup is a discipline prompt — it fires any time
the most recent .ACD file per processor has not been saved
since the last backup. This is by design, not a bug.

## Processors backed up (4 total)
- Rewash
- SandStone
- Shiploader
- UpperLowerPrimaryCrush

## Incremental logic — .ACD files only
Each file is compared against its own most recent backup across
all backup folders (not just the latest folder). This is handled
by build_file_index() which scans all backup folders newest to
oldest and maps each filename to its most recent backed-up copy.

- NEW:       file did not exist in any previous backup — copy it
- CHANGED:   file exists but date modified differs — copy it
- UNCHANGED: file exists and date modified matches — skip it,
             flag it in the warning popup

The warning popup only shows the most recent file per processor
(by date and optional letter suffix). Older saves for the same
processor are suppressed. If a file was backed up as NEW or
CHANGED in the current run, it is suppressed from the popup.

## Non-ACD files (BAK, Recovery)
Always copied regardless — no incremental logic applied.
.Sem and .Wrk files are RSLogix session locks — always skipped
with a WARNING log entry, this is expected and harmless.

## Popup display
Both the warning popup and success popup display on monitor 2
(right monitor, 1920x1080). Positioning constants are defined
at the top of backup_popup.py.

## Task Scheduler
Use pythonw.exe (not python.exe) so no terminal window appears.
Instructions are in the comments at the top of plc_backup.py.
Terminal must remain logged in — never logs off.

## Rules
- Comment all code in plain English
- Standard library only — no pip installs
- Never modify the incremental logic without updating this file
