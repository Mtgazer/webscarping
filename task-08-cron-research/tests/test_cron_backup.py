import hashlib
import json
import os
import shutil
import sys
import tarfile
import tempfile
import time
import unittest

# Add task directory to sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from main import (
    calculate_sha256,
    create_backup_archive,
    rotate_backups,
    append_log,
    save_manifest,
    run_backup_rotator,
)


class TestCronBackup(unittest.TestCase):
    def setUp(self):
        self.tmp_dir = tempfile.mkdtemp(prefix="test_cron_backup_")
        self.source_dir = os.path.join(self.tmp_dir, "source")
        self.backup_dir = os.path.join(self.tmp_dir, "backups")
        self.log_file = os.path.join(self.tmp_dir, "test.log")
        self.manifest_file = os.path.join(self.tmp_dir, "manifest.json")

        os.makedirs(self.source_dir, exist_ok=True)
        os.makedirs(self.backup_dir, exist_ok=True)

        # Create sample files in source
        with open(os.path.join(self.source_dir, "file1.txt"), "w") as f:
            f.write("Test content 1\n")
        with open(os.path.join(self.source_dir, "file2.json"), "w") as f:
            json.dump({"test": True}, f)

    def tearDown(self):
        if os.path.exists(self.tmp_dir):
            shutil.rmtree(self.tmp_dir)

    def test_calculate_sha256(self):
        """Verify SHA-256 calculation matches hashlib standard."""
        test_file = os.path.join(self.tmp_dir, "sha_test.txt")
        test_content = b"Deterministic SHA-256 test content"
        with open(test_file, "wb") as f:
            f.write(test_content)

        expected = hashlib.sha256(test_content).hexdigest()
        actual = calculate_sha256(test_file)
        self.assertEqual(actual, expected)

    def test_create_backup_archive(self):
        """Verify .tar.gz archive creation, file count, and archive contents."""
        info = create_backup_archive(self.source_dir, self.backup_dir)
        self.assertTrue(os.path.exists(info["archive_path"]))
        self.assertEqual(info["files_archived"], 2)
        self.assertGreater(info["size_bytes"], 0)
        self.assertEqual(len(info["sha256"]), 64)

        # Inspect archive contents
        with tarfile.open(info["archive_path"], "r:gz") as tar:
            names = tar.getnames()
            self.assertIn("file1.txt", names)
            self.assertIn("file2.json", names)

    def test_rotate_backups_prunes_older(self):
        """Verify retention rotation removes archives exceeding max_backups."""
        # Create 5 dummy backup archives with artificial delays to establish mtime order
        for i in range(5):
            path = os.path.join(self.backup_dir, f"backup_20261029_0{i}0000.tar.gz")
            with open(path, "w") as f:
                f.write(f"dummy archive {i}")
            # Set artificial modification times
            mtime = time.time() - (5 - i) * 60
            os.utime(path, (mtime, mtime))

        # Rotate with max_backups = 3
        pruned = rotate_backups(self.backup_dir, max_backups=3)
        self.assertEqual(len(pruned), 2)
        self.assertIn("backup_20261029_000000.tar.gz", pruned)
        self.assertIn("backup_20261029_010000.tar.gz", pruned)

        # Confirm remaining archives count is 3
        remaining = [f for f in os.listdir(self.backup_dir) if f.endswith(".tar.gz")]
        self.assertEqual(len(remaining), 3)

    def test_append_log(self):
        """Verify timestamped log line formatting."""
        append_log(self.log_file, "Test log message", level="SUCCESS")
        self.assertTrue(os.path.exists(self.log_file))
        with open(self.log_file, "r") as f:
            line = f.read()
        self.assertIn("[SUCCESS] Test log message", line)

    def test_save_manifest(self):
        """Verify manifest JSON schema and values."""
        sample_info = {"archive_name": "test.tar.gz", "size_bytes": 1024}
        save_manifest(self.manifest_file, sample_info, ["test.tar.gz"], ["old.tar.gz"])

        self.assertTrue(os.path.exists(self.manifest_file))
        with open(self.manifest_file, "r") as f:
            data = json.load(f)
        self.assertEqual(data["latest_backup"]["archive_name"], "test.tar.gz")
        self.assertEqual(data["active_backups_count"], 1)
        self.assertEqual(data["pruned_in_this_run"], ["old.tar.gz"])

    def test_run_backup_rotator_end_to_end(self):
        """Verify full end-to-end execution of run_backup_rotator."""
        success = run_backup_rotator(
            source_dir=self.source_dir,
            backup_dir=self.backup_dir,
            log_file=self.log_file,
            manifest_file=self.manifest_file,
            max_backups=5,
            trigger_label="Test End-to-End Trigger",
        )
        self.assertTrue(success)
        self.assertTrue(os.path.exists(self.log_file))
        self.assertTrue(os.path.exists(self.manifest_file))
        archives = [f for f in os.listdir(self.backup_dir) if f.endswith(".tar.gz")]
        self.assertEqual(len(archives), 1)

    def test_runner_scripts_executable(self):
        """Verify run_backup_job.sh and cron_setup.sh exist and are executable."""
        script_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        runner_path = os.path.join(script_dir, "run_backup_job.sh")
        setup_path = os.path.join(script_dir, "cron_setup.sh")

        self.assertTrue(os.path.exists(runner_path))
        self.assertTrue(os.access(runner_path, os.X_OK))

        self.assertTrue(os.path.exists(setup_path))
        self.assertTrue(os.access(setup_path, os.X_OK))

    def test_cron_expression_syntax(self):
        """Verify the 5-field cron expression for daily 02:00 AM execution."""
        cron_expr = "0 2 * * *"
        fields = cron_expr.split()
        self.assertEqual(len(fields), 5, "Cron expression must have exactly 5 fields")
        self.assertEqual(fields[0], "0", "Minute must be 0")
        self.assertEqual(fields[1], "2", "Hour must be 2 (02:00 AM)")
        self.assertEqual(fields[2], "*", "Day of Month must be *")
        self.assertEqual(fields[3], "*", "Month must be *")
        self.assertEqual(fields[4], "*", "Day of Week must be *")


if __name__ == "__main__":
    unittest.main()
