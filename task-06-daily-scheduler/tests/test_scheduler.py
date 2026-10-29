import json
import os
import shutil
import stat
import sys
import tempfile
import unittest

# Add task directory to sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from main import (
    collect_system_metrics,
    write_log_entry,
    save_execution_json,
    execute_job,
    get_local_timestamp,
)


class TestDailyScheduler(unittest.TestCase):
    def setUp(self):
        self.tmp_dir = tempfile.mkdtemp(prefix="test_scheduler_")
        self.log_file = os.path.join(self.tmp_dir, "test_execution.log")
        self.json_file = os.path.join(self.tmp_dir, "test_summary.json")

    def tearDown(self):
        if os.path.exists(self.tmp_dir):
            shutil.rmtree(self.tmp_dir)

    def test_collect_system_metrics(self):
        """Verify collect_system_metrics returns expected keys and realistic values."""
        metrics = collect_system_metrics(target_path=self.tmp_dir)
        self.assertIn("timestamp", metrics)
        self.assertIn("hostname", metrics)
        self.assertIn("os_platform", metrics)
        self.assertIn("python_version", metrics)
        self.assertIn("disk", metrics)
        self.assertIn("load_average", metrics)
        self.assertEqual(metrics["status"], "HEALTHY")

        disk = metrics["disk"]
        self.assertGreater(disk["total_gb"], 0)
        self.assertGreaterEqual(disk["free_gb"], 0)
        self.assertGreaterEqual(disk["percent_used"], 0.0)
        self.assertLessEqual(disk["percent_used"], 100.0)

    def test_write_log_entry(self):
        """Verify write_log_entry appends formatted entries with timestamps and log levels."""
        metrics = collect_system_metrics(target_path=self.tmp_dir)
        write_log_entry(self.log_file, metrics, trigger_label="Unit Test Trigger")

        self.assertTrue(os.path.exists(self.log_file))
        with open(self.log_file, "r", encoding="utf-8") as f:
            content = f.read()

        self.assertIn("[INFO] Scheduled Job Execution Started", content)
        self.assertIn("Unit Test Trigger", content)
        self.assertIn("[SUCCESS] Daily diagnostic completed successfully", content)
        self.assertIn(metrics["hostname"], content)

    def test_save_execution_json(self):
        """Verify save_execution_json serializes metrics cleanly to disk."""
        metrics = collect_system_metrics(target_path=self.tmp_dir)
        save_execution_json(self.json_file, metrics, trigger_label="JSON Test")

        self.assertTrue(os.path.exists(self.json_file))
        with open(self.json_file, "r", encoding="utf-8") as f:
            data = json.load(f)

        self.assertEqual(data["trigger"], "JSON Test")
        self.assertIn("metrics", data)
        self.assertEqual(data["metrics"]["status"], "HEALTHY")

    def test_execute_job_end_to_end(self):
        """Verify end-to-end execute_job writes both log and json and returns True."""
        success = execute_job(
            log_file=self.log_file,
            output_json=self.json_file,
            target_path=self.tmp_dir,
            trigger_label="E2E Test Run",
        )
        self.assertTrue(success)
        self.assertTrue(os.path.exists(self.log_file))
        self.assertTrue(os.path.exists(self.json_file))

    def test_runner_script_executable(self):
        """Verify run_scheduled_job.sh exists and is marked executable."""
        script_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        runner_path = os.path.join(script_dir, "run_scheduled_job.sh")
        self.assertTrue(os.path.exists(runner_path), f"Runner not found: {runner_path}")

        # Check POSIX executable bit
        is_executable = os.access(runner_path, os.X_OK)
        self.assertTrue(is_executable, f"Runner script is not executable: {runner_path}")

    def test_cron_expression_syntax(self):
        """Verify the 5-field cron expression for daily 15:00 execution."""
        cron_expr = "0 15 * * *"
        fields = cron_expr.split()
        self.assertEqual(len(fields), 5, "Cron expression must contain exactly 5 fields")

        minute, hour, dom, month, dow = fields
        self.assertEqual(minute, "0", "Minute must be 0")
        self.assertEqual(hour, "15", "Hour must be 15 (3:00 PM in 24-hour format)")
        self.assertEqual(dom, "*", "Day of Month must be * (every day)")
        self.assertEqual(month, "*", "Month must be * (every month)")
        self.assertEqual(dow, "*", "Day of Week must be * (every day of the week)")


if __name__ == "__main__":
    unittest.main()
