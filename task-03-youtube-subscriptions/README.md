# Task 3 — YouTube Subscription Information

## Objective
Extract YouTube channel subscription metadata from an authorized HTML export using **BeautifulSoup**, organize and clean the data inside a **Pandas DataFrame**, and export the structured dataset to a clean CSV file.

---

## Authorized Access & Ethical Compliance
YouTube's Subscriptions page (`https://www.youtube.com/feed/channels`) requires an authenticated user session. In strict adherence to assignment requirements:
- **No Credential Scraping**: We do not automate Google login, store user passwords, or inject private session cookies into scripts.
- **No Bot Bypass**: We do not attempt to bypass CAPTCHAs or Google anti-bot systems.
- **Authorized Export Input**: The script parses an authorized HTML document saved directly by the user while logged into their own browser account, or uses the verified educational sample fixture provided in [`data/sample_subscriptions.html`](./data/sample_subscriptions.html).

---

## How to Obtain & Place Your Authorized Export

To process your personal YouTube subscriptions:

1. Open your web browser where you are already signed in to your YouTube account.
2. Navigate to your subscriptions management page:
   ```text
   https://www.youtube.com/feed/channels
   ```
3. Press **`Ctrl + S`** (Save Page As), select **"Webpage, HTML Only"** or **"Webpage, Complete"**, and save the file.
4. Rename and place the saved file at:
   ```text
   task-03-youtube-subscriptions/data/subscriptions.html
   ```
5. Run [`main.py`](./main.py). The script automatically detects `data/subscriptions.html` and parses your authorized data.

*(Note: If `data/subscriptions.html` is not present, the script automatically uses [`data/sample_subscriptions.html`](./data/sample_subscriptions.html) to demonstrate full parsing, deduplication, and CSV generation functionality).*

---

## What the Implementation Does
The script [`main.py`](./main.py):
1. Loads the authorized HTML file (`data/subscriptions.html` if available, otherwise `data/sample_subscriptions.html`).
2. Traverses the DOM using BeautifulSoup to extract:
   - **`channel_name`**: Extracted from `#text`, `#channel-title`, or anchor labels.
   - **`channel_url`**: Normalized to a fully qualified URL (`https://www.youtube.com/@handle` or `https://www.youtube.com/channel/UC...`) via `urllib.parse.urljoin`.
   - **`subscriber_count`**: Extracted using regex matching (e.g. `11.9M subscribers`, `621K subscribers`) where publicly visible. If the count is private or omitted from the export, it is recorded cleanly as `"N/A"`, **never fabricated**.
3. Deduplicates entries by normalized channel URL.
4. Loads cleaned records into a **Pandas DataFrame** and sorts channels alphabetically.
5. Exports the DataFrame to [`output/youtube_subscriptions.csv`](./output/youtube_subscriptions.csv).
6. Writes audit metadata to [`output/extraction_summary.json`](./output/extraction_summary.json).
7. Displays a formatted ASCII table directly in the terminal.

---

## Libraries and Tools Used
- **Python 3.14+** (Miniconda project virtual environment)
- **`beautifulsoup4`**: For resilient parsing of YouTube's HTML structures.
- **`pandas`**: For tabular data structures, sorting, and CSV serialization.
- **`re`**, **`urllib.parse`**, **`os`**, **`json`** (Standard Library): For text matching, URL normalization, and path management.
- **`unittest`** (Standard Library): For offline testing without network or authentication dependencies.

---

## Installation & Setup
Activate the shared project virtual environment from the repository root:
```bash
# From repository root
source .venv/bin/activate
```

Verify or install required dependencies:
```bash
pip install -r task-03-youtube-subscriptions/requirements.txt
```

---

## How to Run the Code

### 1. Run the YouTube Subscriptions Extractor
```bash
python task-03-youtube-subscriptions/main.py
```

### 2. Run the Automated Unit Tests
```bash
python task-03-youtube-subscriptions/tests/test_youtube_parser.py -v
```

### 3. Inspect the Generated CSV File
```bash
cat task-03-youtube-subscriptions/output/youtube_subscriptions.csv
```

---

## Example Output

### Terminal Output:
```text
Parsing YouTube subscription channels using BeautifulSoup...
Extracted 8 distinct channel records.
Constructing and sorting Pandas DataFrame...
Results successfully saved to CSV: .../task-03-youtube-subscriptions/output/youtube_subscriptions.csv

======================================================================
EXTRACTED YOUTUBE SUBSCRIPTIONS (Pandas DataFrame)
======================================================================
                     channel_name                                               channel_url   subscriber_count
0                     3Blue1Brown                      https://www.youtube.com/@3blue1brown  8.65M subscribers
1                   Computerphile                    https://www.youtube.com/@Computerphile  2.45M subscribers
2                freeCodeCamp.org                     https://www.youtube.com/@freecodecamp  11.9M subscribers
3           Google for Developers                 https://www.youtube.com/@GoogleDevelopers  2.67M subscribers
4                 Jeremy's IT Lab                     https://www.youtube.com/@JeremysITLab   621K subscribers
5              MIT OpenCourseWare  https://www.youtube.com/channel/UCEBb1b_L6zDS3xTUrIALZOw   5.2M subscribers
6                         sentdex                          https://www.youtube.com/@sentdex  1.44M subscribers
7  The Python Software Foundation                           https://www.youtube.com/@ThePSF                N/A
======================================================================
Total Channels: 8 | Public Subscriber Counts Available: 7
======================================================================
```

### Generated CSV (`output/youtube_subscriptions.csv`):
```csv
channel_name,channel_url,subscriber_count
3Blue1Brown,https://www.youtube.com/@3blue1brown,8.65M subscribers
Computerphile,https://www.youtube.com/@Computerphile,2.45M subscribers
freeCodeCamp.org,https://www.youtube.com/@freecodecamp,11.9M subscribers
Google for Developers,https://www.youtube.com/@GoogleDevelopers,2.67M subscribers
Jeremy's IT Lab,https://www.youtube.com/@JeremysITLab,621K subscribers
MIT OpenCourseWare,https://www.youtube.com/channel/UCEBb1b_L6zDS3xTUrIALZOw,5.2M subscribers
sentdex,https://www.youtube.com/@sentdex,1.44M subscribers
The Python Software Foundation,https://www.youtube.com/@ThePSF,N/A
```

---

## Screenshot Evidence & Verification
Under Ubuntu Linux with Wayland, capture authentic evidence using:
1. Run the script in your terminal:
   ```bash
   python task-03-youtube-subscriptions/main.py
   ```
2. Open the CSV in your terminal or text editor:
   ```bash
   column -s, -t < task-03-youtube-subscriptions/output/youtube_subscriptions.csv
   ```
3. Press **`Shift + PrintScreen`** on Ubuntu to capture the terminal showing the output DataFrame and CSV verification.
4. Save the screenshot directly inside [`screenshots/`](./screenshots/).

---

## Privacy Precautions & Limitations
1. **Zero Secret Storage**: Never commit `data/subscriptions.html` if it contains private bookmarks or personally identifiable account email headers. The `.gitignore` file is configured to protect sensitive exports.
2. **Missing Subscriber Counts**: Some creators hide their subscriber counts, and some export structures only record channel names and URLs. The script strictly records `"N/A"` when subscriber metrics are omitted, adhering to assignment ethics.
3. **URL Variants**: YouTube channels can have custom handles (`/@handle`), standard channel IDs (`/channel/UC...`), or legacy user URLs (`/user/...`). All forms are normalized to fully qualified URLs.
