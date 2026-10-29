# Task 6 — Schedule Automatic Code Execution at 15:00

## Objective
Implement an autonomous Python automation script that runs automatically every day at **15:00 (3:00 PM)** using Linux **Cron Jobs**, appending timestamped diagnostic entries to a persistent log file and saving structured execution metadata to JSON without requiring interactive user intervention.

---

## What the Script Does

The diagnostic utility ([`main.py`](./main.py)) performs an autonomous health inspection of the system and workspace:
1. **Timestamping**: Captures high-precision local time with timezone code (e.g. `2026-10-29 15:00:00 EEST`).
2. **Environment & Host Metadata**: Records hostname, operating system kernel, Python interpreter version, and absolute execution path.
3. **Storage Health**: Inspects the mount point (`/run/media/ibrahim-khalil/New Volume`), calculating total, used, and free capacity (in GB and percentage).
4. **System Load**: Records 1, 5, and 15-minute system load averages via `os.getloadavg()`.
5. **Persistent Logging**: Appends human-readable, formatted log lines to [`logs/daily_execution.log`](./logs/daily_execution.log) with clear log levels (`[INFO]`, `[SUCCESS]`, `[ERROR]`).
6. **Structured JSON Output**: Writes the latest execution state to [`output/latest_execution.json`](./output/latest_execution.json).

---

## Technical Architecture & Cron Specifics

### 1. Minimal Cron Environment & Whitespace Handling
Linux `cron` executes jobs under a non-login, non-interactive subshell with a minimal `$PATH` (`/usr/bin:/bin`) and no pre-activated virtual environments.
Furthermore, the project workspace resides on a partition with directory spaces:
```text
/run/media/ibrahim-khalil/New Volume/Ibrahim/AI Course/webscarpingse
```
To eliminate quoting errors or path resolution failures, the task includes a dedicated POSIX runner script ([`run_scheduled_job.sh`](./run_scheduled_job.sh)) with absolute paths, executable bits, and explicit quotes.

### 2. The 5-Field Cron Expression

To execute every day at 15:00 (3:00 PM) local system time:
```text
0 15 * * *
```

| Field | Value | Meaning |
| :--- | :--- | :--- |
| **Minute** | `0` | Execute at minute 0 (the top of the hour). |
| **Hour** | `15` | Execute at hour 15 (3:00 PM in 24-hour time). |
| **Day of Month** | `*` | Every day of the month (1–31). |
| **Month** | `*` | Every month of the year (1–12). |
| **Day of Week** | `*` | Every day of the week (0–7, where 0 and 7 are Sunday). |

---

## Proposed Crontab Entry

```bash
0 15 * * * "/run/media/ibrahim-khalil/New Volume/Ibrahim/AI Course/webscarpingse/task-06-daily-scheduler/run_scheduled_job.sh" >> "/run/media/ibrahim-khalil/New Volume/Ibrahim/AI Course/webscarpingse/task-06-daily-scheduler/logs/cron_stdout.log" 2>&1
```

### Breakdown:
- `0 15 * * *`: Daily trigger at 15:00 local system time (`Africa/Cairo`, EEST / UTC+3).
- `".../run_scheduled_job.sh"`: Absolute path to the executable shell wrapper.
- `>> ".../cron_stdout.log" 2>&1`: Captures stdout and stderr to a log file for auditing.

---

## How to Install and Verify the Cron Job

### Step 1: Open Your User Crontab
```bash
crontab -e
```
*(Select nano if prompted for an editor).*

### Step 2: Add the Entry
Paste the proposed crontab line at the bottom of the file, then save and exit (`Ctrl + O`, `Enter`, `Ctrl + X`).

### Step 3: Verify the Crontab is Active
```bash
crontab -l
```

### Step 4: Verify Cron Daemon Status
```bash
systemctl status cron
```

---

## Verification: Manual Run vs. Scheduled 15:00 Run

In accordance with project integrity standards:
- **Manual Verification (Completed)**: Running [`run_scheduled_job.sh`](./run_scheduled_job.sh) or `python main.py` verifies that the environment, permissions, metrics collection, and log formatting operate without error.
- **Scheduled Verification (Pending 15:00 Trigger)**: To verify autonomous execution at 15:00 without manual triggering:
  1. Leave your machine powered on with the cron daemon active until 15:00.
  2. At 15:01, inspect the execution log:
     ```bash
     cat task-06-daily-scheduler/logs/daily_execution.log
     ```
  3. Verify system cron execution via systemd journal:
     ```bash
     journalctl -u cron.service --since "14:59"
     ```

---

## How to Run Manually and Run Tests

### 1. Execute Script Manually
```bash
# Using project virtual environment
.venv/bin/python task-06-daily-scheduler/main.py --trigger "Manual Test Run"
```

### 2. Execute via Shell Wrapper
```bash
./task-06-daily-scheduler/run_scheduled_job.sh
```

### 3. Run Automated Unit Tests
```bash
.venv/bin/python task-06-daily-scheduler/tests/test_scheduler.py -v
```

---

## Example Log Output ([`logs/daily_execution.log`](./logs/daily_execution.log))

```text
[2026-10-29 11:04:30 EEST] [INFO] Scheduled Job Execution Started (Trigger: Scheduled Cron Job (15:00 Daily))
[2026-10-29 11:04:30 EEST] [INFO] Host: ibrahim-khalil-IdeaPad-Gaming-3-15ACH6 | OS: Linux-7.0.0-38-generic-x86_64-with-glibc2.43
[2026-10-29 11:04:30 EEST] [INFO] Runtime: Python 3.14.8 (/run/media/ibrahim-khalil/New Volume/Ibrahim/AI Course/webscarpingse/.venv/bin/python)
[2026-10-29 11:04:30 EEST] [INFO] Storage (/run/media/ibrahim-khalil/New Volume/Ibrahim/AI Course/webscarpingse): 71.8% used (249.18 GB free / 882.68 GB total)
[2026-10-29 11:04:30 EEST] [INFO] 1/5/15 min Load Average: [0.95, 0.78, 0.68]
[2026-10-29 11:04:30 EEST] [SUCCESS] Daily diagnostic completed successfully. Status: HEALTHY
--------------------------------------------------------------------------------
```

---

## Screenshot Evidence Capture (Ubuntu Wayland)

1. Open your terminal displaying `crontab -l` or the output of `cat task-06-daily-scheduler/logs/daily_execution.log`.
2. Press **`Shift + PrintScreen`** to capture a genuine screenshot.
3. Save the image to:
   ```text
   task-06-daily-scheduler/screenshots/cron_execution_evidence.png
   ```
