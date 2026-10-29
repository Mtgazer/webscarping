#!/usr/bin/env bash
# ==============================================================================
# Task 6 — Autonomous Cron Execution Wrapper Script
# Scheduled to run automatically every day at 15:00 (3:00 PM) EEST.
# Handles environment paths with whitespace cleanly and logs stdout/stderr.
# ==============================================================================

set -euo pipefail

# Dynamically resolve absolute repository root and script paths
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
PYTHON_BIN="$REPO_DIR/.venv/bin/python"
SCRIPT_PATH="$SCRIPT_DIR/main.py"
LOG_FILE="$SCRIPT_DIR/logs/daily_execution.log"
JSON_OUTPUT="$SCRIPT_DIR/output/latest_execution.json"

# Verify interpreter and script exist
if [[ ! -x "$PYTHON_BIN" ]]; then
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] [ERROR] Python interpreter not executable at: $PYTHON_BIN" >> "$LOG_FILE"
    exit 1
fi

if [[ ! -f "$SCRIPT_PATH" ]]; then
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] [ERROR] Script not found at: $SCRIPT_PATH" >> "$LOG_FILE"
    exit 1
fi

# Execute Python diagnostic monitor with absolute arguments
exec "$PYTHON_BIN" "$SCRIPT_PATH" \
    --log-file "$LOG_FILE" \
    --output-json "$JSON_OUTPUT" \
    --target-dir "$REPO_DIR" \
    --trigger "Scheduled Cron Job (15:00 Daily)"
