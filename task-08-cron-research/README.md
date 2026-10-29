# Task 8 — Cron Jobs Research & Practical Implementation

## Overview
This task fulfills both the **Research** and **Practical Task** requirements of Session 10 for Cron Jobs and autonomous scheduling on Linux:
1. **In-Depth Original Research Report** ([`research.md`](./research.md)): A comprehensive technical analysis covering the architecture of the Unix Cron daemon, the 5-field scheduling syntax, common frequency patterns, crontab management utilities, execution environment caveats, timezone handling, troubleshooting steps, and authoritative citations.
2. **Autonomous Backup & Retention Rotator Bot** ([`main.py`](./main.py)): A self-contained, robust Python utility that archives critical files into timestamped `.tar.gz` compressed archives, verifies SHA-256 cryptographic integrity hashes, enforces a retention rotation policy (retaining the last 7 daily archives), and maintains persistent audit logs and JSON manifests.
3. **Safe Crontab Setup Helper** ([`cron_setup.sh`](./cron_setup.sh)): A non-destructive shell script that inspects the system timezone, verifies the cron daemon, checks existing crontabs, and presents the exact proposed crontab line for review without modifying your system automatically.

---

## 1. Research Summary

The complete research report is documented in [`research.md`](./research.md), addressing:
- **What is a Cron Job**: Autonomous recurring background tasks scheduled via `/usr/sbin/cron` running under systemd.
- **Why Cron Jobs are Used**: Unattended maintenance, database/file backups, log rotation, security certificate renewal, and batch reporting.
- **Difference from Normal Scripts**: Normal scripts require interactive invocation and inherit the user's terminal environment; Cron jobs run non-interactively in the background under a minimal environment (`PATH=/usr/bin:/bin`, `SHELL=/bin/sh`).
- **What is the Crontab**: Configuration tables and the management CLI (`crontab -l` to list, `crontab -e` to edit, `crontab -r` to remove).
- **The Five Cron Fields**:
  ```text
  ┌───────────── Minute (0 - 59)
  │ ┌───────────── Hour (0 - 23)
  │ │ ┌───────────── Day of Month (1 - 31)
  │ │ │ ┌───────────── Month (1 - 12)
  │ │ │ │ ┌───────────── Day of Week (0 - 7, 0 & 7 = Sunday)
  │ │ │ │ │
  * * * * * <command>
  ```
- **Special Operators**: `*` (every), `,` (list), `-` (range), `/` (step/increment).
- **Three Real-World Examples**:
  1. *Nightly Database & Workspace Backups* at 02:00 AM (`0 2 * * *`).
  2. *Log Rotation & Cache Pruning* on Sunday midnight (`0 0 * * 0`).
  3. *Weekly Security Audits & Updates* on Monday 06:00 AM (`0 6 * * 1`).
- **Environment Caveats**:
  - Restrictive `$PATH`: Requires absolute paths to interpreters and scripts.
  - Path whitespace handling: Requires quoting or dedicated runner wrappers.
  - Output redirection: Capturing stdout and stderr (`>> file.log 2>&1`).
  - Timezone behavior: Default execution aligns with `/etc/localtime` (`Africa/Cairo`, EEST / UTC+3).
- **References**: Ubuntu Manpages, Red Hat Enterprise Linux 9 Docs, The Linux Foundation (FHS), GNU Coreutils, and Debian Manpages (accessed October 29, 2026).

---

## 2. Practical Implementation: Backup & Log Rotator Bot

### What the Script Does ([`main.py`](./main.py))
1. **Target Payload**: Compresses the files in [`data/sample_payload/`](./data/sample_payload/) (`config.json`, `report_draft.txt`, `transactions.csv`).
2. **Archive Creation**: Generates a timestamped gzip archive in [`backups/`](./backups/) (e.g. `backup_20261029_112604.tar.gz`).
3. **Cryptographic Verification**: Computes the SHA-256 checksum of the archive to ensure bit-level integrity.
4. **Retention Policy (Rotation)**: Scans the archive directory and automatically prunes archives exceeding the retention threshold (default: 7 archives), preventing disk exhaustion.
5. **Persistent Audit Logging**: Appends timestamped log lines with levels (`[INFO]`, `[SUCCESS]`, `[ROTATION]`, `[ERROR]`) to [`logs/backup_rotation.log`](./logs/backup_rotation.log).
6. **Structured JSON Manifest**: Writes metadata to [`output/backup_manifest.json`](./output/backup_manifest.json).

---

## 3. The 5-Field Cron Expression

To execute the automated backup and rotation daily at **02:00 AM** local system time:
```text
0 2 * * *
```

| Field | Value | Meaning |
| :--- | :--- | :--- |
| **Minute** | `0` | Execute at minute 0 (the top of the hour). |
| **Hour** | `2` | Execute at 2:00 AM (low-traffic maintenance window). |
| **Day of Month** | `*` | Every day of the month (1–31). |
| **Month** | `*` | Every month of the year (1–12). |
| **Day of Week** | `*` | Every day of the week (0–7). |

### Proposed Crontab Line:
```bash
0 2 * * * "/run/media/ibrahim-khalil/New Volume/Ibrahim/AI Course/webscarpingse/task-08-cron-research/run_backup_job.sh" >> "/run/media/ibrahim-khalil/New Volume/Ibrahim/AI Course/webscarpingse/task-08-cron-research/logs/cron_stdout.log" 2>&1
```

*(Note: In accordance with your instructions, your actual user crontab has not been modified automatically).*

---

## Project Structure
```text
task-08-cron-research/
├── README.md                  # Comprehensive task documentation
├── research.md                # In-depth research report with citations
├── main.py                    # Autonomous backup and retention rotator bot
├── run_backup_job.sh          # POSIX shell runner script with absolute paths
├── cron_setup.sh              # Non-destructive crontab inspection helper
├── data/
│   └── sample_payload/        # Sample files to archive
│       ├── config.json
│       ├── report_draft.txt
│       └── transactions.csv
├── backups/                   # Destination for compressed .tar.gz archives
│   └── .gitkeep
├── logs/
│   ├── .gitkeep
│   └── backup_rotation.log    # Persistent timestamped audit log
├── output/
│   └── backup_manifest.json   # Structured manifest with SHA-256 checksums
├── tests/
│   └── test_cron_backup.py    # 8 automated unit tests
└── screenshots/
    └── .gitkeep               # Evidence directory for Wayland desktop screenshots
```

---

## Installation & Setup

Activate the project virtual environment from the repository root:
```bash
source .venv/bin/activate
```

The script utilizes standard library modules (`tarfile`, `hashlib`, `json`, `os`, `sys`, `datetime`). Zero external third-party dependencies are required.

---

## How to Run the Code

### 1. Inspect Crontab & System Timezone
```bash
./task-08-cron-research/cron_setup.sh
```

### 2. Execute Backup & Rotation Job Manually
```bash
./task-08-cron-research/run_backup_job.sh
```
Or directly with the Python interpreter:
```bash
.venv/bin/python task-08-cron-research/main.py
```

### 3. Run Automated Unit Tests
```bash
.venv/bin/python task-08-cron-research/tests/test_cron_backup.py -v
```

### 4. Inspect Outputs & Logs
- **View backup manifest JSON**:
  ```bash
  cat task-08-cron-research/output/backup_manifest.json
  ```
- **View audit log**:
  ```bash
  cat task-08-cron-research/logs/backup_rotation.log
  ```
- **List generated archives**:
  ```bash
  ls -lh task-08-cron-research/backups/
  ```

---

## Example Execution Output

### Console Output:
```text
===========================================================================
TASK 8 — AUTONOMOUS BACKUP & LOG ROTATION JOB
===========================================================================
Trigger         : Scheduled Cron Backup Job
Source Path     : .../task-08-cron-research/data/sample_payload
Archive Created : backup_20261029_112604.tar.gz
Archive Path    : .../task-08-cron-research/backups/backup_20261029_112604.tar.gz
Archive Size    : 707 bytes (3 files)
SHA-256 Hash    : 49e96a3b6eda506c2b31a19d395575ec49fd289f24c04359e23c47185245557a
Pruned Archives : 0 (Retention limit: 7)
Active Archives : 1
Log File        : .../task-08-cron-research/logs/backup_rotation.log
Manifest JSON   : .../task-08-cron-research/output/backup_manifest.json
===========================================================================
Status: SUCCESS (Archive created and verified)
```

---

## Screenshot Evidence Capture (Ubuntu Wayland)

1. Open your terminal displaying the output of `./task-08-cron-research/cron_setup.sh` or `cat task-08-cron-research/logs/backup_rotation.log`.
2. Press **`Shift + PrintScreen`** to capture a genuine screenshot.
3. Save the image to:
   ```text
   task-08-cron-research/screenshots/cron_backup_evidence.png
   ```
