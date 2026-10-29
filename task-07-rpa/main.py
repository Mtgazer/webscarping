import argparse
import datetime
import json
import os
import re
import sys
import pandas as pd


def clean_currency(val: str | int | float | None) -> float:
    """Strip currency symbols, commas, and whitespace, returning float."""
    if val is None or pd.isna(val):
        return 0.0
    if isinstance(val, (int, float)):
        return float(val)
    cleaned = re.sub(r"[^\d.-]", "", str(val).strip())
    try:
        return float(cleaned)
    except ValueError:
        return 0.0


def ingest_sales_orders(filepath: str, log_messages: list[str]) -> pd.DataFrame:
    """Ingest raw sales orders CSV and map to standardized transactional schema."""
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"Sales orders input file not found: {filepath}")

    df = pd.read_csv(filepath, dtype=str)
    log_messages.append(f"Ingested {len(df)} records from sales orders: {os.path.basename(filepath)}")

    # Clean quantities and unit prices
    df["Quantity"] = df["Quantity"].apply(lambda q: int(clean_currency(q)))
    df["Unit_Price"] = df["Unit_Price"].apply(clean_currency)
    df["gross_amount"] = (df["Quantity"] * df["Unit_Price"]).round(2)

    # Standardize column mapping
    standardized = pd.DataFrame({
        "transaction_id": df["Order_Number"].str.strip(),
        "date": df["Order_Date"].str.strip(),
        "type": "REVENUE",
        "counterparty": df["Customer_Name"].str.strip(),
        "category": df["Item_Category"].str.strip(),
        "gross_amount": df["gross_amount"],
        "status": df["Payment_Status"].str.strip(),
    })
    return standardized


def ingest_supplier_expenses(filepath: str, log_messages: list[str]) -> pd.DataFrame:
    """Ingest raw supplier expenses CSV and map to standardized transactional schema."""
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"Supplier expenses input file not found: {filepath}")

    df = pd.read_csv(filepath, dtype=str)
    log_messages.append(f"Ingested {len(df)} records from supplier expenses: {os.path.basename(filepath)}")

    df["gross_amount"] = df["Total_Amount"].apply(clean_currency)

    # Standardize column mapping
    standardized = pd.DataFrame({
        "transaction_id": df["InvoiceID"].str.strip(),
        "date": df["Date"].str.strip(),
        "type": "EXPENSE",
        "counterparty": df["Vendor"].str.strip(),
        "category": df["Category"].str.strip(),
        "gross_amount": df["gross_amount"],
        "status": df["Status"].str.strip(),
    })
    return standardized


def apply_business_rules(
    df: pd.DataFrame,
    high_value_threshold: float = 5000.0,
    tax_rate: float = 0.14,
    log_messages: list[str] | None = None,
) -> pd.DataFrame:
    """Apply business logic: tax calculation, net balance, and high-value audit flags."""
    df = df.copy()

    # Rule 1: Estimated tax (14% VAT)
    df["estimated_tax"] = (df["gross_amount"] * tax_rate).round(2)

    # Rule 2: Net balance (positive for revenue, negative for expense)
    df["net_balance"] = df.apply(
        lambda row: row["gross_amount"] if row["type"] == "REVENUE" else -row["gross_amount"],
        axis=1,
    ).round(2)

    # Rule 3: High-value transaction audit flag
    df["flagged_high_value"] = df["gross_amount"] >= high_value_threshold

    if log_messages is not None:
        flagged_count = int(df["flagged_high_value"].sum())
        log_messages.append(f"Applied business rules: {flagged_count} transactions flagged >= ${high_value_threshold:,.2f}")

    return df


def reconcile_and_aggregate(
    sales_df: pd.DataFrame,
    expenses_df: pd.DataFrame,
    log_messages: list[str],
) -> tuple[pd.DataFrame, dict]:
    """Reconcile sales and expenses into a unified sorted ledger and compute executive metrics."""
    unified = pd.concat([sales_df, expenses_df], ignore_index=True)

    # Apply rules
    unified = apply_business_rules(unified, log_messages=log_messages)

    # Sort chronologically
    unified = unified.sort_values(by=["date", "transaction_id"]).reset_index(drop=True)

    # Compute aggregates
    total_revenue = round(float(unified[unified["type"] == "REVENUE"]["gross_amount"].sum()), 2)
    total_expenses = round(float(unified[unified["type"] == "EXPENSE"]["gross_amount"].sum()), 2)
    net_cash_flow = round(total_revenue - total_expenses, 2)
    total_tax = round(float(unified["estimated_tax"].sum()), 2)
    flagged_total = int(unified["flagged_high_value"].sum())

    # Category breakdown
    category_totals = (
        unified.groupby(["type", "category"])["gross_amount"]
        .sum()
        .round(2)
        .to_dict()
    )
    # Format category breakdown keys as strings
    cat_summary = {f"{k[0]}: {k[1]}": v for k, v in category_totals.items()}

    summary = {
        "execution_timestamp": datetime.datetime.now().astimezone().strftime("%Y-%m-%d %H:%M:%S %Z"),
        "total_transactions": len(unified),
        "total_revenue": total_revenue,
        "total_expenses": total_expenses,
        "net_cash_flow": net_cash_flow,
        "total_estimated_tax": total_tax,
        "high_value_flagged_count": flagged_total,
        "category_summary": cat_summary,
    }
    log_messages.append(f"Reconciliation complete: Net Cash Flow = ${net_cash_flow:,.2f}")
    return unified, summary


def generate_outputs(
    unified_df: pd.DataFrame,
    summary: dict,
    output_dir: str,
    log_messages: list[str],
) -> dict:
    """Export unified CSV, executive summary JSON, and timestamped audit log."""
    os.makedirs(output_dir, exist_ok=True)

    csv_path = os.path.join(output_dir, "reconciled_ledger.csv")
    json_path = os.path.join(output_dir, "reconciliation_report.json")
    log_path = os.path.join(output_dir, "audit_log.txt")

    # 1. Export CSV
    cols = [
        "transaction_id",
        "date",
        "type",
        "counterparty",
        "category",
        "gross_amount",
        "estimated_tax",
        "net_balance",
        "status",
        "flagged_high_value",
    ]
    unified_df[cols].to_csv(csv_path, index=False, encoding="utf-8")

    # 2. Export JSON
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)

    # 3. Write Audit Log
    ts = summary["execution_timestamp"]
    with open(log_path, "w", encoding="utf-8") as f:
        f.write("=" * 80 + "\n")
        f.write("RPA BOT EXECUTION AUDIT TRAIL — FINANCIAL RECONCILIATION\n")
        f.write("=" * 80 + "\n")
        f.write(f"Execution Started : {ts}\n")
        f.write(f"Output Directory  : {os.path.abspath(output_dir)}\n")
        f.write("-" * 80 + "\n")
        f.write("Execution Steps:\n")
        for idx, msg in enumerate(log_messages, start=1):
            f.write(f"  Step {idx:02d}: {msg}\n")
        f.write("-" * 80 + "\n")
        f.write(f"Transactions Processed : {summary['total_transactions']}\n")
        f.write(f"Total Revenue          : ${summary['total_revenue']:,.2f}\n")
        f.write(f"Total Expenses         : ${summary['total_expenses']:,.2f}\n")
        f.write(f"Net Cash Flow          : ${summary['net_cash_flow']:,.2f}\n")
        f.write(f"Flagged High-Value     : {summary['high_value_flagged_count']}\n")
        f.write("=" * 80 + "\n")
        f.write("Status: COMPLETED SUCCESSFULLY (Zero Errors)\n")

    return {
        "csv": csv_path,
        "json": json_path,
        "log": log_path,
    }


def run_rpa_bot(sales_path: str, expenses_path: str, output_dir: str) -> bool:
    """Execute complete end-to-end RPA financial reconciliation bot workflow."""
    start_time = datetime.datetime.now()
    log_messages = []
    log_messages.append("RPA Bot initiated by automated scheduler/user.")

    try:
        print("=" * 75)
        print("TASK 7 — ROBOTIC PROCESS AUTOMATION (RPA) WORKFLOW BOT")
        print("=" * 75)
        print(f"Sales Input     : {os.path.abspath(sales_path)}")
        print(f"Expenses Input  : {os.path.abspath(expenses_path)}")
        print(f"Output Folder   : {os.path.abspath(output_dir)}")
        print("=" * 75 + "\n")

        print("Executing Step 1: Ingesting sales orders...")
        sales_df = ingest_sales_orders(sales_path, log_messages)

        print("Executing Step 2: Ingesting supplier expenses...")
        expenses_df = ingest_supplier_expenses(expenses_path, log_messages)

        print("Executing Step 3: Applying business rules and reconciling transactions...")
        unified_df, summary = reconcile_and_aggregate(sales_df, expenses_df, log_messages)

        duration = (datetime.datetime.now() - start_time).total_seconds()
        log_messages.append(f"Processing finished in {duration:.3f} seconds.")

        print("Executing Step 4: Generating structured output deliverables...")
        files = generate_outputs(unified_df, summary, output_dir, log_messages)

        # Print executive summary table
        print("\n" + "=" * 75)
        print("RECONCILIATION EXECUTIVE AUDIT SUMMARY")
        print("=" * 75)
        print(f"Total Transactions : {summary['total_transactions']}")
        print(f"Total Gross Revenue: ${summary['total_revenue']:>12,.2f}")
        print(f"Total Expenses     : ${summary['total_expenses']:>12,.2f}")
        print(f"Net Cash Flow      : ${summary['net_cash_flow']:>12,.2f}")
        print(f"Estimated Tax (14%): ${summary['total_estimated_tax']:>12,.2f}")
        print(f"Flagged High-Value : {summary['high_value_flagged_count']} transactions (>= $5,000.00)")
        print("-" * 75)
        print(f"Generated Files:")
        print(f"  - Ledger CSV  : {files['csv']}")
        print(f"  - Report JSON : {files['json']}")
        print(f"  - Audit Log   : {files['log']}")
        print("=" * 75)
        print("RPA Bot Workflow Status: COMPLETED SUCCESSFULLY (0 Errors)")
        return True

    except Exception as exc:
        print(f"Error during RPA bot execution: {exc}", file=sys.stderr)
        return False


def parse_args() -> argparse.Namespace:
    script_dir = os.path.dirname(os.path.abspath(__file__))
    default_sales = os.path.join(script_dir, "data", "inputs", "sales_orders.csv")
    default_expenses = os.path.join(script_dir, "data", "inputs", "supplier_expenses.csv")
    default_output = os.path.join(script_dir, "output")

    parser = argparse.ArgumentParser(description="Task 7 — Robotic Process Automation (RPA) Bot")
    parser.add_argument("--sales", type=str, default=default_sales, help="Path to sales orders CSV")
    parser.add_argument("--expenses", type=str, default=default_expenses, help="Path to supplier expenses CSV")
    parser.add_argument("--output", type=str, default=default_output, help="Path to output directory")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    success = run_rpa_bot(
        sales_path=args.sales,
        expenses_path=args.expenses,
        output_dir=args.output,
    )
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
