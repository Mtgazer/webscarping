#!/usr/bin/env bash
# ==============================================================================
# Task 8 — Safe Crontab Inspection & Setup Helper
# Inspects system timezone, checks existing user crontab, and displays
# the proposed cron entry without modifying crontab automatically.
# ==============================================================================

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
RUNNER_PATH="$SCRIPT_DIR/run_backup_job.sh"
LOG_STDOUT="$SCRIPT_DIR/logs/cron_stdout.log"

PROPOSED_ENTRY="0 2 * * * \"$RUNNER_PATH\" >> \"$LOG_STDOUT\" 2>&1"

echo "==========================================================================="
echo "TASK 8 — CRON CONFIGURATION & INSPECTION HELPER"
echo "==========================================================================="

echo "1. System Timezone & Clock:"
timedatectl | grep -E "Local time|Time zone" || date

echo ""
echo "2. Cron Service Daemon Status:"
systemctl is-active cron >/dev/null 2>&1 && echo "  Daemon Status: ACTIVE (Running)" || echo "  Daemon Status: INACTIVE"

echo ""
echo "3. Existing User Crontab:"
if crontab -l 2>/dev/null | grep -v '^#' | grep -q .; then
    echo "  Existing active jobs found:"
    crontab -l | grep -v '^#'
else
    echo "  No active user crontab entries detected (clean crontab)."
fi

echo ""
echo "4. Proposed Cron Entry (Runs Daily at 02:00 AM):"
echo "  $PROPOSED_ENTRY"
echo ""
echo "Field Breakdown:"
echo "  0  -> Minute 0"
echo "  2  -> Hour 2 (2:00 AM local time)"
echo "  *  -> Every day of month"
echo "  *  -> Every month"
echo "  *  -> Every day of week"
echo "==========================================================================="
echo "SAFETY NOTE: In accordance with project instructions, this helper does NOT"
echo "install or modify your crontab automatically."
echo "To install manually when approved, run: crontab -e"
echo "and append the proposed entry."
echo "==========================================================================="
