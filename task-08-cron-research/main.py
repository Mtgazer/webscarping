import argparse
import datetime
import hashlib
import json
import os
import sys
import tarfile


def get_local_timestamp() -> str:
    """Return ISO-like local timestamp with timezone code."""
    now = datetime.datetime.now().astimezone()
    tz_name = now.tzname() or "Local"
    return f"{now.strftime('%Y-%m-%d %H:%M:%S')} {tz_name}"


def calculate_sha256(filepath: str) -> str:
    """Calculate SHA-256 hash of a file for integrity verification."""
    sha256 = hashlib.sha256()
    with open(filepath, "rb") as f:
        while chunk := f.read(65536):
            sha256.update(chunk)
    return sha256.hexdigest()


def create_backup_archive(source_dir: str, backup_dir: str) -> dict:
    """Create a timestamped compressed .tar.gz archive of source_dir."""
    if not os.path.exists(source_dir):
        raise FileNotFoundError(f"Source directory not found: {source_dir}")

    os.makedirs(backup_dir, exist_ok=True)
    timestamp_tag = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    archive_name = f"backup_{timestamp_tag}.tar.gz"
    archive_path = os.path.join(backup_dir, archive_name)

    # Count files to archive
    file_count = 0
    with tarfile.open(archive_path, "w:gz") as tar:
        for root, _, files in os.walk(source_dir):
            for file in files:
                abs_file = os.path.join(root, file)
                rel_path = os.path.relpath(abs_file, source_dir)
                tar.add(abs_file, arcname=rel_path)
                file_count += 1

    file_size_bytes = os.path.getsize(archive_path)
    sha256_hash = calculate_sha256(archive_path)

    return {
        "archive_name": archive_name,
        "archive_path": os.path.abspath(archive_path),
        "source_dir": os.path.abspath(source_dir),
        "files_archived": file_count,
        "size_bytes": file_size_bytes,
        "sha256": sha256_hash,
        "created_at": get_local_timestamp(),
    }


def rotate_backups(backup_dir: str, max_backups: int = 7) -> list[str]:
    """Scan backup_dir for .tar.gz archives and prune those exceeding max_backups."""
    if not os.path.exists(backup_dir):
        return []

    archives = []
    for f in os.listdir(backup_dir):
        if f.startswith("backup_") and f.endswith(".tar.gz"):
            full_path = os.path.join(backup_dir, f)
            archives.append((os.path.getmtime(full_path), full_path))

    # Sort descending by modification time (newest first)
    archives.sort(key=lambda x: x[0], reverse=True)

    pruned = []
    if len(archives) > max_backups:
        to_prune = archives[max_backups:]
        for _, path in to_prune:
            try:
                os.remove(path)
                pruned.append(os.path.basename(path))
            except OSError as err:
                print(f"Warning: Could not prune {path}: {err}", file=sys.stderr)

    return pruned


def append_log(log_path: str, message: str, level: str = "INFO") -> None:
    """Append structured timestamped line to log file."""
    os.makedirs(os.path.dirname(os.path.abspath(log_path)), exist_ok=True)
    ts = get_local_timestamp()
    log_line = f"[{ts}] [{level}] {message}\n"
    with open(log_path, "a", encoding="utf-8") as f:
        f.write(log_line)


def save_manifest(manifest_path: str, backup_info: dict, active_backups: list[str], pruned: list[str]) -> None:
    """Save structured manifest of the latest backup and rotation state."""
    os.makedirs(os.path.dirname(os.path.abspath(manifest_path)), exist_ok=True)
    data = {
        "latest_backup": backup_info,
        "active_backups_count": len(active_backups),
        "active_backups": active_backups,
        "pruned_in_this_run": pruned,
    }
    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)


def run_backup_rotator(
    source_dir: str,
    backup_dir: str,
    log_file: str,
    manifest_file: str,
    max_backups: int = 7,
    trigger_label: str = "Daily Cron Backup",
) -> bool:
    """Execute end-to-end backup, checksum calculation, retention rotation, and logging."""
    try:
        append_log(log_file, f"Backup job started (Trigger: {trigger_label})", "INFO")
        append_log(log_file, f"Archiving source: {source_dir}", "INFO")

        # 1. Create archive
        backup_info = create_backup_archive(source_dir, backup_dir)
        append_log(
            log_file,
            f"Created archive: {backup_info['archive_name']} "
            f"({backup_info['files_archived']} files, {backup_info['size_bytes']} bytes, SHA-256: {backup_info['sha256'][:12]}...)",
            "SUCCESS",
        )

        # 2. Rotate old backups
        pruned = rotate_backups(backup_dir, max_backups=max_backups)
        if pruned:
            append_log(log_file, f"Retention policy enforced: pruned {len(pruned)} old archive(s): {', '.join(pruned)}", "ROTATION")
        else:
            append_log(log_file, f"Retention policy checked: 0 archives pruned (within {max_backups} limit)", "INFO")

        # 3. List active backups
        active = [
            f for f in sorted(os.listdir(backup_dir), reverse=True)
            if f.startswith("backup_") and f.endswith(".tar.gz")
        ]

        # 4. Save manifest
        save_manifest(manifest_file, backup_info, active, pruned)
        append_log(log_file, f"Backup job finished successfully. Active archives: {len(active)}", "SUCCESS")

        # Console summary
        print("=" * 75)
        print("TASK 8 — AUTONOMOUS BACKUP & LOG ROTATION JOB")
        print("=" * 75)
        print(f"Trigger         : {trigger_label}")
        print(f"Source Path     : {backup_info['source_dir']}")
        print(f"Archive Created : {backup_info['archive_name']}")
        print(f"Archive Path    : {backup_info['archive_path']}")
        print(f"Archive Size    : {backup_info['size_bytes']} bytes ({backup_info['files_archived']} files)")
        print(f"SHA-256 Hash    : {backup_info['sha256']}")
        print(f"Pruned Archives : {len(pruned)} (Retention limit: {max_backups})")
        print(f"Active Archives : {len(active)}")
        print(f"Log File        : {os.path.abspath(log_file)}")
        print(f"Manifest JSON   : {os.path.abspath(manifest_file)}")
        print("=" * 75)
        print("Status: SUCCESS (Archive created and verified)")
        return True

    except Exception as exc:
        err_msg = f"Backup job failed: {exc}"
        print(f"Error: {err_msg}", file=sys.stderr)
        append_log(log_file, err_msg, "ERROR")
        return False


def parse_args() -> argparse.Namespace:
    script_dir = os.path.dirname(os.path.abspath(__file__))
    default_source = os.path.join(script_dir, "data", "sample_payload")
    default_backup_dir = os.path.join(script_dir, "backups")
    default_log = os.path.join(script_dir, "logs", "backup_rotation.log")
    default_manifest = os.path.join(script_dir, "output", "backup_manifest.json")

    parser = argparse.ArgumentParser(description="Task 8 — Automated Cron Backup & Rotation Bot")
    parser.add_argument("--source", type=str, default=default_source, help="Source directory to archive")
    parser.add_argument("--backup-dir", type=str, default=default_backup_dir, help="Directory to store archives")
    parser.add_argument("--log-file", type=str, default=default_log, help="Log file path")
    parser.add_argument("--manifest", type=str, default=default_manifest, help="JSON manifest output path")
    parser.add_argument("--max-backups", type=int, default=7, help="Maximum number of backup archives to retain")
    parser.add_argument("--trigger", type=str, default="Daily Cron Backup", help="Trigger label")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    success = run_backup_rotator(
        source_dir=args.source,
        backup_dir=args.backup_dir,
        log_file=args.log_file,
        manifest_file=args.manifest,
        max_backups=args.max_backups,
        trigger_label=args.trigger,
    )
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
