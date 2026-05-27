# PLC Backup Tool

Automated backup tool for RSLogix 5000 PLC program files.
Backs up to a NAS and a local destination with every run.
Also supports on-demand single-file backups triggered by the
PLC Change Watcher's Backup Now button.

---

## What It Does

- Copies PLC program files from the active directory to two destinations
- Only copies files that are new or changed since the last backup
- Each file is compared against its own most recent backup individually
- Warns the operator if programs have not been saved before backing up
- Supports on-demand backup of a single file via backup_single_file()
- Logs every run to a file on the NAS
- Runs automatically via Windows Task Scheduler (weekly)

---

## Destinations

| Destination | Path |
|---|---|
| NAS | Z:\PLC_Programs |
| Local | C:\Python\NAS_Backups\PLC |
| Log | Z:\PLC_Programs\plc_backup_log.txt |

---

## Backup Folder Structure

```
Z:\PLC_Programs\
    Scheduled_Backups\
        PLC_Backup_YYYY-MM-DD_HHMM\   ← weekly Task Scheduler runs
    On_Demand_Backups\
        PLC_Backup_YYYY-MM-DD_HHMM\   ← Backup Now button from change watcher

C:\Python\NAS_Backups\PLC\
    Scheduled_Backups\
    On_Demand_Backups\
```

---

## Processors Backed Up

- Rewash
- SandStone
- Shiploader
- UpperLowerPrimaryCrush

---

## How to Run Manually

```powershell
python C:\Python\NAS_Backups\plc_backup.py
```

---

## How It Works — Scheduled Backup

1. Script runs via Task Scheduler (weekly)
2. Warning popup lists programs not saved since last backup
3. Operator saves programs in RSLogix 5000 via File → Save As
4. Use naming convention: `ProgramName_YYYY_MM_DD.ACD`
5. Click Run Backup Again
6. Success popup confirms backup is complete

## How It Works — On-Demand Backup

1. Operator saves a file in RSLogix 5000
2. PLC Change Watcher popup fires
3. Operator fills in change details and clicks Backup Now
4. Change watcher calls backup_single_file() from this module
5. Single .ACD file and change log CSV backed up to On_Demand_Backups
6. Success popup confirms filename, NAS status, local status

---

## Save Convention

Standard save (first save of the day):
```
ProgramName_YYYY_MM_DD.ACD
Example: Rewash_2026_05_20.ACD
```

Same-day saves use a letter suffix:
```
ProgramName_YYYY_MM_DDa.ACD
ProgramName_YYYY_MM_DDb.ACD
Example: Rewash_2026_05_20a.ACD
```

---

## Files

| File | Description |
|---|---|
| `plc_backup.py` | Main backup script |
| `backup_popup.py` | Warning, success, and on-demand success popups |
| `README.md` | This file |

---

## Display

All popups appear on monitor 2 (right monitor).

---

## Task Scheduler

Configured to run weekly. Uses pythonw.exe so no terminal window appears.
Terminal must remain logged in at all times.

---

## Requirements

- Python 3.x (standard library only, no additional installs)
- NAS mapped as Z: drive
- RSLogix 5000 programs saved in `C:\PLC\CURRENT_PLC_VIRSION\2026`
