# PLC Backup Tool

Automated backup tool for RSLogix 5000 PLC program files.
Backs up to a NAS and a local destination with every run.

## What It Does
- Copies PLC program files from the active directory to two destinations
- Only copies files that are new or changed since the last backup
- Warns the operator if programs have not been saved before backing up
- Logs every run to a file on the NAS
- Runs automatically via Windows Task Scheduler

## Destinations
- NAS:   Z:\PLC_Programs  (\\192.168.0.65\Backups)
- Local: C:\Python\NAS_Backups\PLC
- Log:   Z:\PLC_Programs\plc_backup_log.txt

## Processors Backed Up
- Rewash
- SandStone
- Shiploader
- UpperLowerPrimaryCrush

## How to Run Manually
Double-click plc_backup.py or run from PowerShell:
    python C:\NAS_Backups\plc_backup.py

## How It Works
1. Script runs manually or via Task Scheduler
2. Warning popup appears listing any programs not saved since last backup
3. Operator saves programs in RSLogix 5000 via File > Save As
4. Use naming convention: ProgramName_YYYY_MM_DD.ACD
5. Click Run Backup Again
6. Success popup confirms backup is complete

## Save Convention
    ProgramName_YYYY_MM_DD.ACD
    Example: Rewash_2026_05_20.ACD

## Files
- plc_backup.py   — main backup script
- backup_popup.py — warning and success popup windows

## Task Scheduler
Configured to run monthly. Uses pythonw.exe so no terminal
window appears. Terminal must remain logged in at all times.

## Requirements
- Python 3.x (standard library only, no additional installs)
- NAS mapped as Z: drive
- RSLogix 5000 programs saved in C:\PLC\CURRENT_PLC_VIRSION\2026