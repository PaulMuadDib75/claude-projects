\# PLC Tools — Integration Workspace



\## What this workspace contains



Two standalone tools that are being integrated:



| Folder | Tool | Purpose |

|---|---|---|

| PLC-backup\\ | PLC Backup Tool | Backs up RSLogix 5000 .ACD files to NAS and local |

| PLC-change-watcher\\ | PLC Change Watcher | Monitors .ACD saves, prompts operator to document changes |



Each folder has its own CLAUDE.md with full tool-specific detail.



\## Current integration task



Adding a "Backup Now" button to the change watcher popup.

When clicked it logs the change to CSV and backs up the single

.ACD file that triggered the popup. A success popup then confirms.



Three files are being modified:

\- PLC-backup\\plc\_backup.py

\- PLC-backup\\backup\_popup.py

\- PLC-change-watcher\\plc\_change\_watcher.py



\## Deployment locations (programming terminal)



These are the paths where files actually run in production.

This is a DIFFERENT machine from where development happens.



| Tool | Deployed path |

|---|---|

| Backup tool | C:\\Python\\NAS\_Backups\\ |

| Change watcher | C:\\Python\\PLC-change-watcher\\ |



\## Backup destinations — DO NOT CHANGE THESE PATHS



The backup destinations are on the programming terminal.

They are NOT local to this development machine.

Never modify these paths in plc\_backup.py without explicit instruction.



| Destination | Path |

|---|---|

| NAS | Z:\\PLC\_Programs\\ |

| Local | C:\\Python\\NAS\_Backups\\PLC\\ |

| Log file | Z:\\PLC\_Programs\\plc\_backup\_log.txt |

| Change log CSV | C:\\Python\\PLC-change-watcher\\plc\_change\_log.csv |



\## Backup subfolder structure



All backup runs write into subfolders by type:



Scheduled (weekly Task Scheduler runs):

&#x20; Z:\\PLC\_Programs\\Scheduled\_Backups\\PLC\_Backup\_YYYY-MM-DD\_HHMM\\

&#x20; C:\\Python\\NAS\_Backups\\PLC\\Scheduled\_Backups\\PLC\_Backup\_YYYY-MM-DD\_HHMM\\



On-demand (Backup Now button from change watcher):

&#x20; Z:\\PLC\_Programs\\On\_Demand\_Backups\\PLC\_Backup\_YYYY-MM-DD\_HHMM\\

&#x20; C:\\Python\\NAS\_Backups\\PLC\\On\_Demand\_Backups\\PLC\_Backup\_YYYY-MM-DD\_HHMM\\



\## Cross-folder import (programming terminal)



On the programming terminal, plc\_change\_watcher.py imports from

the backup tool using sys.path:



&#x20; sys.path.insert(0, r"C:\\Python\\NAS\_Backups")

&#x20; from plc\_backup import backup\_single\_file

&#x20; from backup\_popup import show\_on\_demand\_success



These paths refer to the DEPLOYMENT locations, not this workspace.



\## Rules

\- Never change backup destination paths without explicit instruction

\- Never change deployment paths without explicit instruction

\- Comment all code in plain English

\- Standard library only for plc\_backup.py and backup\_popup.py

\- plc\_change\_watcher.py already uses watchdog, pystray, Pillow

