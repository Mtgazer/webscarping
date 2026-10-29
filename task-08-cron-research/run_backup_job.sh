#!/usr/bin/env bash
# ==============================================================================
# Task 8 — Autonomous Cron Backup & Rotation Runner Script
# Designed for scheduled cron execution (e.g. daily at 02:00 AM or 15:00).
# Handles environment paths with whitespace cleanly and logs execution.
# ==============================================================================

set -euo pipefail

# Absolute repository root and virtual environment paths
REPO_DIR="/run/media/ibrahim-khalil/New Volume/Ibrahim/AI Course/webscarpingse"
PYTHON_BIN="$REPO_DIR/.venv/bin/python"
SCRIPT_PATH="$REPO_DIR/task-08-cron-research/main.py"
SOURCE_DIR="$REPO_DIR/task-08-cron-research/data/sample_payload"
BACKUP_DIR="$REPO_DIR/task-08-cron-research/backups"
LOG_FILE="$REPO_DIR/task-08-cron-research/logs/backup_rotation.log"
MANIFEST_FILE="$REPO_DIR/task-08-cron-research/output/backup_manifest.json"

# Validate interpreter and script exist
if [[ ! -x "$PYTHON_BIN" ]]; then
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] [ERROR] Python interpreter not executable at: $PYTHON_BIN" >> "$LOG_FILE"
    exit 1
fi

if [[ ! -f "$SCRIPT_PATH" ]]; then
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] [ERROR] Script not found at: $SCRIPT_PATH" >> "$LOG_FILE"
    exit 1
fi

# Execute Python backup rotator with absolute arguments
exec "$PYTHON_BIN" "$SCRIPT_PATH" \
    --source "$SOURCE_DIR" \
    --backup-dir "$BACKUP_DIR" \
    --log-file "$LOG_FILE" \
    --manifest "$MANIFEST_FILE" \
    --max-backups 7 \
    --trigger "Scheduled Cron Backup Job"
