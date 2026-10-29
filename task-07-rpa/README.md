# Task 7 — Robotic Process Automation (RPA) Research & Practical Workflow

## Overview
This task fulfills both the **Research** and **Practical Task** requirements of Session 10 for Robotic Process Automation (RPA):
1. **In-Depth Original Research Report** ([`research.md`](./research.md)): A comprehensive analysis answering all seven core RPA questions with academic and industry citations and access dates.
2. **Practical Process Automation Bot** ([`main.py`](./main.py)): A fully automated, robust Python-based software bot that ingests, cleans, standardizes, validates, reconciles, and reports on multi-source financial CSV records, complete with a detailed process specification ([`workflow.md`](./workflow.md)).

---

## 1. Research Summary

The complete research report is documented in [`research.md`](./research.md), addressing:
- **What is RPA**: Software agents ("bots") emulating human digital interactions at the presentation layer (UI/desktop) without changing underlying software architecture.
- **Problems Solved**: Human data-entry error, high operational labor costs, legacy system integration bottlenecks, slow processing turnaround, and regulatory compliance gaps.
- **Main Characteristics**: Rule-based, deterministic, non-invasive (surface-level), highly scalable, and auditable.
- **RPA vs. Traditional Software Automation**: Detailed comparative matrix contrasting presentation-layer UI automation vs. backend/API software engineering.
- **Three Real-World Examples**:
  1. *Accounts Payable Reconciliation* in Corporate Finance.
  2. *Patient Intake & Insurance Eligibility Verification* in Healthcare.
  3. *Employee Provisioning & Credential Setup* in Human Resources.
- **Advantages & Disadvantages**: High accuracy and rapid deployment vs. fragility to UI changes and lack of cognitive reasoning without AI.
- **Popular RPA Tools**: UiPath, Automation Anywhere, Microsoft Power Automate, SS&C Blue Prism, and Robot Framework.
- **References & Sources**: Gartner, IEEE Computer Society, IBM Cloud, UiPath Docs, and ACM Digital Library (accessed October 29, 2026).

---

## 2. Practical RPA Bot: Multi-Source Financial Reconciliation

### Business Problem
A finance department receives separate monthly CSV exports:
- **`data/inputs/sales_orders.csv`**: Revenue records with order numbers, customer names, product categories, quantities, unit prices, and payment statuses.
- **`data/inputs/supplier_expenses.csv`**: Operational vendor expenses with invoice numbers, dates, vendor names, expense categories, messy currency formatting (`$`, `EGP`, commas), and payment statuses.

Manually cross-referencing, stripping symbols, computing line totals, applying business rules, flagging high-value items, and compiling an executive summary takes hours of repetitive clerk labor.

### The RPA Solution
The bot ([`main.py`](./main.py)) automates the entire process in under 15 milliseconds:
1. **Ingestion & Schema Standardization**: Normalizes disparate header names into a unified schema (`transaction_id`, `date`, `counterparty`, `category`, `gross_amount`).
2. **Currency Cleaning**: Strips currency symbols and commas, casting all values to floating-point numbers.
3. **Business Rule Enforcement**:
   - Computes estimated Value Added Tax (14% VAT).
   - Computes net balance (+ for revenue, - for expenses).
   - Flags high-value transactions (`gross_amount >= $5,000.00`) for management review.
4. **Chronological Ledger Unification**: Combines and sorts all transactions chronologically.
5. **Output Generation & Audit Logging**:
   - Standardized Ledger CSV: [`output/reconciled_ledger.csv`](./output/reconciled_ledger.csv)
   - Executive Audit JSON: [`output/reconciliation_report.json`](./output/reconciliation_report.json)
   - Timestamped Audit Trail: [`output/audit_log.txt`](./output/audit_log.txt)

---

## Project Structure
```text
task-07-rpa/
├── README.md                  # Comprehensive task documentation
├── research.md                # In-depth original research report with citations
├── workflow.md                # Detailed process specification & Mermaid flowchart
├── main.py                    # RPA reconciliation bot engine
├── data/
│   └── inputs/
│       ├── sales_orders.csv      # Raw incoming sales data
│       └── supplier_expenses.csv # Raw incoming expenses data
├── output/
│   ├── reconciled_ledger.csv     # Unified standardized ledger CSV
│   ├── reconciliation_report.json# Executive JSON audit summary
│   └── audit_log.txt             # Timestamped step-by-step audit log
├── tests/
│   └── test_rpa_workflow.py   # 7 automated unit tests
└── screenshots/
    └── .gitkeep               # Evidence directory for Wayland desktop screenshots
```

---

## Installation & Setup

Activate the project virtual environment from the repository root:
```bash
source .venv/bin/activate
```

Dependencies (`pandas`) are already installed and synchronized in the root `.venv`. No additional packages are required.

---

## How to Run the Code

### 1. Execute the RPA Bot
```bash
.venv/bin/python task-07-rpa/main.py
```

### 2. Run the Automated Unit Tests
```bash
.venv/bin/python task-07-rpa/tests/test_rpa_workflow.py -v
```

### 3. Inspect Generated Output Files
- **View unified ledger CSV**:
  ```bash
  cat task-07-rpa/output/reconciled_ledger.csv
  ```
- **View executive JSON report**:
  ```bash
  cat task-07-rpa/output/reconciliation_report.json
  ```
- **View execution audit log**:
  ```bash
  cat task-07-rpa/output/audit_log.txt
  ```

---

## Example Execution Output

### Console Output:
```text
===========================================================================
TASK 7 — ROBOTIC PROCESS AUTOMATION (RPA) WORKFLOW BOT
===========================================================================
Sales Input     : .../task-07-rpa/data/inputs/sales_orders.csv
Expenses Input  : .../task-07-rpa/data/inputs/supplier_expenses.csv
Output Folder   : .../task-07-rpa/output
===========================================================================

Executing Step 1: Ingesting sales orders...
Executing Step 2: Ingesting supplier expenses...
Executing Step 3: Applying business rules and reconciling transactions...
Executing Step 4: Generating structured output deliverables...

===========================================================================
RECONCILIATION EXECUTIVE AUDIT SUMMARY
===========================================================================
Total Transactions : 16
Total Gross Revenue: $   37,981.00
Total Expenses     : $   15,365.50
Net Cash Flow      : $   22,615.50
Estimated Tax (14%): $    7,468.51
Flagged High-Value : 4 transactions (>= $5,000.00)
---------------------------------------------------------------------------
Generated Files:
  - Ledger CSV  : .../task-07-rpa/output/reconciled_ledger.csv
  - Report JSON : .../task-07-rpa/output/reconciliation_report.json
  - Audit Log   : .../task-07-rpa/output/audit_log.txt
===========================================================================
RPA Bot Workflow Status: COMPLETED SUCCESSFULLY (0 Errors)
```

---

## Screenshot Evidence Capture (Ubuntu Wayland)

1. Run the RPA bot in your terminal.
2. Press **`Shift + PrintScreen`** to capture a genuine screenshot of the executive summary output or the opened output CSV.
3. Save the image to:
   ```text
   task-07-rpa/screenshots/rpa_execution_evidence.png
   ```
