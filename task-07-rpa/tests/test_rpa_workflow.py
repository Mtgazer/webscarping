import json
import os
import shutil
import sys
import tempfile
import unittest
import pandas as pd

# Add task directory to sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from main import (
    clean_currency,
    ingest_sales_orders,
    ingest_supplier_expenses,
    apply_business_rules,
    reconcile_and_aggregate,
    generate_outputs,
    run_rpa_bot,
)


class TestRPAWorkflow(unittest.TestCase):
    def setUp(self):
        self.script_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.sales_file = os.path.join(self.script_dir, "data", "inputs", "sales_orders.csv")
        self.expenses_file = os.path.join(self.script_dir, "data", "inputs", "supplier_expenses.csv")
        self.tmp_dir = tempfile.mkdtemp(prefix="test_rpa_")

    def tearDown(self):
        if os.path.exists(self.tmp_dir):
            shutil.rmtree(self.tmp_dir)

    def test_clean_currency(self):
        """Verify currency cleaning and numeric casting."""
        self.assertEqual(clean_currency("$1,200.50"), 1200.50)
        self.assertEqual(clean_currency("  EGP 450.00 "), 450.00)
        self.assertEqual(clean_currency(1500), 1500.0)
        self.assertEqual(clean_currency(None), 0.0)
        self.assertEqual(clean_currency("invalid"), 0.0)

    def test_ingest_sales_orders(self):
        """Verify sales orders ingestion, schema mapping, and line total calculation."""
        logs = []
        df = ingest_sales_orders(self.sales_file, logs)
        self.assertEqual(len(df), 8)
        self.assertIn("transaction_id", df.columns)
        self.assertIn("gross_amount", df.columns)
        self.assertTrue((df["type"] == "REVENUE").all())
        # First row: 5 * 1200.00 = 6000.00
        self.assertEqual(df.iloc[0]["gross_amount"], 6000.00)

    def test_ingest_supplier_expenses(self):
        """Verify supplier expenses ingestion and schema mapping."""
        logs = []
        df = ingest_supplier_expenses(self.expenses_file, logs)
        self.assertEqual(len(df), 8)
        self.assertIn("transaction_id", df.columns)
        self.assertIn("gross_amount", df.columns)
        self.assertTrue((df["type"] == "EXPENSE").all())
        # First row: 1850.00
        self.assertEqual(df.iloc[0]["gross_amount"], 1850.00)

    def test_apply_business_rules(self):
        """Verify business rules: VAT calculation, net balance, and high-value threshold flags."""
        sample_df = pd.DataFrame([
            {"transaction_id": "T1", "gross_amount": 6000.0, "type": "REVENUE"},
            {"transaction_id": "T2", "gross_amount": 1000.0, "type": "EXPENSE"},
        ])
        result = apply_business_rules(sample_df, high_value_threshold=5000.0, tax_rate=0.14)

        # Tax: 6000 * 0.14 = 840.0, 1000 * 0.14 = 140.0
        self.assertEqual(result.iloc[0]["estimated_tax"], 840.0)
        self.assertEqual(result.iloc[1]["estimated_tax"], 140.0)

        # Net balance: +6000.0 for revenue, -1000.0 for expense
        self.assertEqual(result.iloc[0]["net_balance"], 6000.0)
        self.assertEqual(result.iloc[1]["net_balance"], -1000.0)

        # High-value flag: T1 >= 5000 (True), T2 < 5000 (False)
        self.assertTrue(result.iloc[0]["flagged_high_value"])
        self.assertFalse(result.iloc[1]["flagged_high_value"])

    def test_reconcile_and_aggregate(self):
        """Verify unified reconciliation, chronological sorting, and metric aggregation."""
        logs = []
        sales_df = ingest_sales_orders(self.sales_file, logs)
        expenses_df = ingest_supplier_expenses(self.expenses_file, logs)

        unified, summary = reconcile_and_aggregate(sales_df, expenses_df, logs)
        self.assertEqual(len(unified), 16)
        self.assertEqual(summary["total_transactions"], 16)
        self.assertEqual(summary["total_revenue"], 37981.0)
        self.assertEqual(summary["total_expenses"], 15365.5)
        self.assertEqual(summary["net_cash_flow"], 22615.5)
        self.assertEqual(summary["high_value_flagged_count"], 4)

        # Verify chronological order
        dates = list(unified["date"])
        self.assertEqual(dates, sorted(dates))

    def test_generate_outputs(self):
        """Verify generation of reconciled CSV, JSON report, and audit log."""
        logs = ["Init", "Step A", "Complete"]
        sales_df = ingest_sales_orders(self.sales_file, logs)
        expenses_df = ingest_supplier_expenses(self.expenses_file, logs)
        unified, summary = reconcile_and_aggregate(sales_df, expenses_df, logs)

        files = generate_outputs(unified, summary, self.tmp_dir, logs)
        self.assertTrue(os.path.exists(files["csv"]))
        self.assertTrue(os.path.exists(files["json"]))
        self.assertTrue(os.path.exists(files["log"]))

        # Validate CSV contents
        df_out = pd.read_csv(files["csv"])
        self.assertEqual(len(df_out), 16)

        # Validate JSON contents
        with open(files["json"], "r", encoding="utf-8") as f:
            report = json.load(f)
        self.assertEqual(report["total_transactions"], 16)
        self.assertEqual(report["net_cash_flow"], 22615.5)

        # Validate Audit Log contents
        with open(files["log"], "r", encoding="utf-8") as f:
            log_text = f.read()
        self.assertIn("RPA BOT EXECUTION AUDIT TRAIL", log_text)
        self.assertIn("Status: COMPLETED SUCCESSFULLY", log_text)

    def test_run_rpa_bot_end_to_end(self):
        """Verify full end-to-end execution of run_rpa_bot."""
        success = run_rpa_bot(
            sales_path=self.sales_file,
            expenses_path=self.expenses_file,
            output_dir=self.tmp_dir,
        )
        self.assertTrue(success)
        self.assertTrue(os.path.exists(os.path.join(self.tmp_dir, "reconciled_ledger.csv")))
        self.assertTrue(os.path.exists(os.path.join(self.tmp_dir, "reconciliation_report.json")))
        self.assertTrue(os.path.exists(os.path.join(self.tmp_dir, "audit_log.txt")))


if __name__ == "__main__":
    unittest.main()
