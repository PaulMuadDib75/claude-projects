\# PLC Backup Tool



\## What this is

Python tool that backs up RSLogix 5000 PLC program files from the

active program directory to a NAS and a local destination.

Uses incremental logic for .ACD files and warns the operator

if programs have not been saved since the last backup.



\## Source directory

C:\\PLC\\CURRENT\_PLC\_VIRSION\\2026



\## Destinations

\- NAS:   Z:\\PLC\_Programs  (mapped from \\\\192.168.0.65\\Backups)

\- Local: C:\\Python\\NAS\_Backups\\PLC

\- Log:   Z:\\PLC\_Programs\\plc\_backup\_log.txt



\## Files

\- plc\_backup.py   — main backup script

\- backup\_popup.py — tkinter popup module (warning and success)



\## Intended workflow

1\. Backup runs (manually or via Task Scheduler)

2\. Warning popup appears listing the most recent .ACD file

&#x20;  per processor that has not changed since the last backup

3\. Operator saves all four programs in RSLogix 5000 (Ctrl+S)

4\. Operator clicks Run Backup Again

5\. RSLogix creates new dated .ACD files on save

6\. Script detects them as NEW or CHANGED and copies them

7\. Success popup confirms backup complete



The warning popup is a discipline prompt — it fires any time

the most recent .ACD file per processor has not been saved

since the last backup. This is by design, not a bug.



\## Processors backed up (4 total)

\- Rewash

\- SandStone

\- Shiploader

\- UpperLowerPrimaryCrush



\## Incremental logic — .ACD files only

\- NEW:       file did not exist in last backup — copy it

\- CHANGED:   file exists but date modified differs — copy it

\- UNCHANGED: file exists and date modified matches — skip it,

&#x20;            flag it in the warning popup



\## Non-ACD files (BAK, Recovery)

Always copied regardless — no incremental logic applied.

.Sem and .Wrk files are RSLogix session locks — always skipped

with a WARNING log entry, this is expected and harmless.



\## Task Scheduler

Use pythonw.exe (not python.exe) so no terminal window appears.

Instructions are in the comments at the top of plc\_backup.py.

Terminal only stays logged in — never logs off.



\## Rules

\- Comment all code in plain English

\- Standard library only — no pip installs

\- Never modify the incremental logic without updating this file

