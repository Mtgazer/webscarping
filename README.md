# Session 10 — Python Automation Assignment

Comprehensive practical implementation of the eight tasks for Session 10, covering web scraping, media harvesting, data processing with Pandas, dynamic browser automation with Selenium, system task scheduling with Linux Cron, and Robotic Process Automation (RPA).

---

## Repository Overview

```text
session-10-automation/
├── .gitignore                      # Git ignore rules for venv, caches, and secrets
├── README.md                       # Main repository documentation & guide
├── PROGRESS.md                     # Development roadmap and verification tracker
├── requirements.txt                # Unified project dependencies
├── task-01-basic-scraping/         # Task 1: Basic Web Scraping (requests + BS4)
├── task-02-image-scraping/         # Task 2: Web Image Downloader (relative/absolute URLs)
├── task-03-youtube-subscriptions/  # Task 3: YouTube Channel Subscriptions to Pandas DataFrame
├── task-04-carrefour-scraper/      # Task 4: E-Commerce Product Catalog Scraper
├── task-05-facebook-selenium/      # Task 5: Facebook Browser Automation with Safety Approval
├── task-06-daily-scheduler/        # Task 6: 15:00 Daily Cron Execution & Logging
├── task-07-rpa/                    # Task 7: RPA Research & Practical Business Workflow
└── task-08-cron-research/          # Task 8: Cron Jobs Research, Setup & Automated Backups
```

---

## Environment Setup & Installation

This project utilizes a single, isolated virtual environment (`.venv`) created from Miniconda Python.

### 1. Prerequisites
- Linux OS (Ubuntu 26.04 LTS or compatible)
- Miniconda / Anaconda Python (Python 3.10+)
- Git 2.40+
- Google Chrome or Chromium (for Selenium tasks)

### 2. Create the Virtual Environment
Create the project-wide `.venv` in the repository root using the Miniconda Python interpreter:
```bash
"$HOME/miniconda3/bin/python" -m venv .venv
```

### 3. Activate the Environment
Always activate the environment before running any project scripts:
```bash
source .venv/bin/activate
```

Verify your active Python and pip:
```bash
which python
# Should point to: .../webscarpingse/.venv/bin/python

python --version
# Should output: Python 3.14.x
```

### 4. Install Dependencies
Install the project dependencies using pip from within the active environment:
```bash
python -m pip install -r requirements.txt
```

---

## Task Summary & Navigation

| Task | Directory | Focus & Technologies | Key Deliverables |
| :--- | :--- | :--- | :--- |
| **Task 1** | [task-01-basic-scraping](./task-01-basic-scraping/) | Requests, BeautifulSoup4, HTML Parsing | Page title, headings, paragraphs, and $\ge 5$ normalized links saved to structured JSON. |
| **Task 2** | [task-02-image-scraping](./task-02-image-scraping/) | Media Extraction, Stream I/O | $\ge 10$ downloaded images with meaningful filenames and download manifest. |
| **Task 3** | [task-03-youtube-subscriptions](./task-03-youtube-subscriptions/) | BeautifulSoup4, Pandas, CSV Export | Subscribed channel names, URLs, and subscriber counts exported to CSV. |
| **Task 4** | [task-04-carrefour-scraper](./task-04-carrefour-scraper/) | E-commerce Scraping, Dynamic Data | Product names, prices, URLs, and bonus attributes exported to CSV & JSON. |
| **Task 5** | [task-05-facebook-selenium](./task-05-facebook-selenium/) | Selenium, Browser Automation | Authenticated navigation and post preparation with mandatory user approval gate. |
| **Task 6** | [task-06-daily-scheduler](./task-06-daily-scheduler/) | Linux Cron, System Automation | Autonomous daily task scheduled at 15:00 (3:00 PM) with persistent logging. |
| **Task 7** | [task-07-rpa](./task-07-rpa/) | RPA Concepts, Business Workflow | In-depth RPA research report and automated multi-file audit/data reorganization bot. |
| **Task 8** | [task-08-cron-research](./task-08-cron-research/) | Linux Crontab, System Maintenance | Complete Cron research (5 fields explained) and automated backup script. |

---

## Safety & Ethics Standards

1. **No Hardcoded Credentials**: Passwords, tokens, or private session cookies are never committed. Templates are provided as `.env.example`.
2. **Interactive Confirmation Gates**: Automation that modifies external state (such as social media posting) requires explicit user confirmation before action.
3. **Respectful Scraping**: All scrapers use polite headers (`User-Agent`), reasonable request delays, timeouts, and error handling.
4. **Verifiable Results**: No fake outputs or fabricated evidence. Every generated file and screenshot reflects genuine program execution.

---

## Git Workflow

Development follows an incremental commit workflow using Conventional Commits. Each feature, test, and documentation milestone is committed separately on the `feature/session-10-automation` branch.
