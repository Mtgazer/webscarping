import argparse
import datetime
import json
import os
import platform
import shutil
import sys
import time


def get_local_timestamp() -> str:
    """Return ISO-like local timestamp with timezone code."""
    now = datetime.datetime.now().astimezone()
    tz_name = now.tzname() or "Local"
    return f"{now.strftime('%Y-%m-%d %H:%M:%S')} {tz_name}"


def collect_system_metrics(target_path: str = ".") -> dict:
    """Collect system health and workspace diagnostic metrics."""
    # 1. Disk usage
    disk = shutil.disk_usage(target_path)
    disk_total_gb = round(disk.total / (1024 ** 3), 2)
    disk_used_gb = round(disk.used / (1024 ** 3), 2)
    disk_free_gb = round(disk.free / (1024 ** 3), 2)
    disk_pct_used = round((disk.used / disk.total) * 100, 1) if disk.total > 0 else 0.0

    # 2. System load average
    try:
        load_avg = [round(x, 2) for x in os.getloadavg()]
    except (AttributeError, OSError):
        load_avg = [0.0, 0.0, 0.0]

    # 3. Host and runtime info
    return {
        "timestamp": get_local_timestamp(),
        "hostname": platform.node(),
        "os_platform": platform.platform(),
        "python_version": platform.python_version(),
        "python_executable": sys.executable,
        "disk": {
            "target_path": os.path.abspath(target_path),
            "total_gb": disk_total_gb,
            "used_gb": disk_used_gb,
            "free_gb": disk_free_gb,
            "percent_used": disk_pct_used,
        },
        "load_average": load_avg,
        "status": "HEALTHY",
    }


def write_log_entry(log_file_path: str, metrics: dict, trigger_label: str = "Daily 15:00 Execution") -> None:
    """Append structured timestamped diagnostic entry to the log file."""
    os.makedirs(os.path.dirname(os.path.abspath(log_file_path)), exist_ok=True)
    ts = metrics["timestamp"]

    log_lines = [
        f"[{ts}] [INFO] Scheduled Job Execution Started (Trigger: {trigger_label})",
        f"[{ts}] [INFO] Host: {metrics['hostname']} | OS: {metrics['os_platform']}",
        f"[{ts}] [INFO] Runtime: Python {metrics['python_version']} ({metrics['python_executable']})",
        f"[{ts}] [INFO] Storage ({metrics['disk']['target_path']}): {metrics['disk']['percent_used']}% used "
        f"({metrics['disk']['free_gb']} GB free / {metrics['disk']['total_gb']} GB total)",
        f"[{ts}] [INFO] 1/5/15 min Load Average: {metrics['load_average']}",
        f"[{ts}] [SUCCESS] Daily diagnostic completed successfully. Status: {metrics['status']}",
        "-" * 80 + "\n",
    ]

    with open(log_file_path, "a", encoding="utf-8") as f:
        f.write("\n".join(log_lines))


def save_execution_json(output_json_path: str, metrics: dict, trigger_label: str = "Daily 15:00 Execution") -> None:
    """Save execution summary as a structured JSON record."""
    os.makedirs(os.path.dirname(os.path.abspath(output_json_path)), exist_ok=True)
    record = {
        "trigger": trigger_label,
        "execution_time": metrics["timestamp"],
        "metrics": metrics,
    }
    with open(output_json_path, "w", encoding="utf-8") as f:
        json.dump(record, f, indent=2)


def execute_job(
    log_file: str,
    output_json: str,
    target_path: str = ".",
    trigger_label: str = "Daily 15:00 Execution",
) -> bool:
    """Execute the diagnostic job, log findings, and save structured summary."""
    try:
        metrics = collect_system_metrics(target_path=target_path)
        write_log_entry(log_file, metrics, trigger_label=trigger_label)
        save_execution_json(output_json, metrics, trigger_label=trigger_label)

        # Console output for manual and testing execution
        print("=" * 75)
        print("TASK 6 — AUTOMATIC CODE EXECUTION (DIAGNOSTIC MONITOR)")
        print("=" * 75)
        print(f"Timestamp       : {metrics['timestamp']}")
        print(f"Trigger         : {trigger_label}")
        print(f"Host / OS       : {metrics['hostname']} ({metrics['os_platform']})")
        print(f"Python Runtime  : {metrics['python_version']} at {metrics['python_executable']}")
        print(f"Disk Storage    : {metrics['disk']['free_gb']} GB free of {metrics['disk']['total_gb']} GB ({metrics['disk']['percent_used']}% used)")
        print(f"System Load     : {metrics['load_average']}")
        print(f"Execution Log   : {os.path.abspath(log_file)}")
        print(f"Summary JSON    : {os.path.abspath(output_json)}")
        print("=" * 75)
        print("Status: SUCCESS (Diagnostics logged successfully)")
        return True
    except Exception as exc:
        err_msg = f"[{get_local_timestamp()}] [ERROR] Job execution failed: {exc}\n"
        print(err_msg, file=sys.stderr)
        try:
            with open(log_file, "a", encoding="utf-8") as f:
                f.write(err_msg)
        except Exception:
            pass
        return False


def parse_args() -> argparse.Namespace:
    script_dir = os.path.dirname(os.path.abspath(__file__))
    default_log = os.path.join(script_dir, "logs", "daily_execution.log")
    default_json = os.path.join(script_dir, "output", "latest_execution.json")

    parser = argparse.ArgumentParser(description="Task 6 — Daily Scheduled Automation Monitor")
    parser.add_argument("--log-file", type=str, default=default_log, help="Path to append log output")
    parser.add_argument("--output-json", type=str, default=default_json, help="Path to write JSON summary")
    parser.add_argument("--target-dir", type=str, default=script_dir, help="Directory path for disk metrics")
    parser.add_argument("--trigger", type=str, default="Daily 15:00 Execution", help="Label describing the execution trigger")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    success = execute_job(
        log_file=args.log_file,
        output_json=args.output_json,
        target_path=args.target_dir,
        trigger_label=args.trigger,
    )
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
