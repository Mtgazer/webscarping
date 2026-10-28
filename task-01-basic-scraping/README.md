# Task 1 — Basic Website Scraping

## Objective
Practice fundamental web scraping techniques in Python by sending HTTP requests, parsing HTML documents, extracting hierarchical text (title, headings, paragraphs), discovering and normalizing hyperlinks, and exporting clean structured data to JSON.

---

## What the Implementation Does
The script [`main.py`](./main.py):
1. Sends an HTTP `GET` request to the target website (`http://books.toscrape.com/`) with custom browser headers and a 10-second timeout.
2. Accurately decodes response content using `apparent_encoding` to preserve UTF-8 symbols (such as currency `£`).
3. Parses the HTML DOM using BeautifulSoup to extract:
   - Cleaned page title (`<title>`).
   - Headings (`<h1>` through `<h6>`) mapped by level and text.
   - Text paragraphs (`<p>`) with leading/trailing whitespace removed.
   - All hyperlinks (`<a href="...">`), skipping in-page anchors (`#`) and `javascript:` pseudo-protocols.
4. Normalizes relative URLs into fully qualified absolute URLs using `urllib.parse.urljoin`.
5. Exports the complete structured dataset to [`output/scraped_content.json`](./output/scraped_content.json).
6. Displays a readable summary directly in the terminal.

---

## Libraries and Tools Used
- **Python 3.14+** (Miniconda project virtual environment)
- **`requests`**: For robust HTTP networking, header configuration, and status code checking.
- **`beautifulsoup4`**: For navigating and extracting data from the HTML parse tree.
- **`urllib.parse`** (Standard Library): For safe URL resolution (`urljoin`).
- **`json`** and **`os`** (Standard Library): For structured data serialization and filesystem path management.
- **`unittest`** (Standard Library): For automated, offline verification with mocked responses.

---

## Installation & Setup
Activate the shared project virtual environment from the repository root:
```bash
# From the repository root
source .venv/bin/activate
```

If needed, verify or install the task dependencies:
```bash
pip install -r task-01-basic-scraping/requirements.txt
```

---

## How to Run the Code

### 1. Run the Scraper
```bash
python task-01-basic-scraping/main.py
```

### 2. Run the Automated Unit Tests
```bash
python task-01-basic-scraping/tests/test_scraper.py -v
```

---

## How the Implementation Works

```text
[Target URL] ---> requests.get(headers, timeout=10)
                      |
                      v
             response.raise_for_status()
             response.encoding = response.apparent_encoding
                      |
                      v
            BeautifulSoup(html, "html.parser")
             /          |          \
            v           v           v
       soup.title   find_all(h1-h6) find_all("a", href=True)
                        |           urljoin(base, href)
                        v                   |
                 Structured Dictionary <----+
                        |
            +-----------+-----------+
            |                       |
            v                       v
    save_to_json(...)       display_summary(...)
    output/scraped_content.json  Terminal Summary
```

- **`fetch_page(url, timeout)`**: Handles HTTP network communication and raises exceptions on HTTP 4xx/5xx codes.
- **`extract_content(html, base_url)`**: Performs purely functional HTML extraction and URL normalization. This separation allows offline unit testing without network dependencies.
- **`save_to_json(data, filepath)`**: Safely creates parent folders and writes indented UTF-8 JSON.
- **`display_summary(data)`**: Formats extraction counts and preview items for user inspection.

---

## Example Output

### Terminal Summary:
```text
============================================================
SCRAPED WEBPAGE SUMMARY
============================================================
Source URL       : http://books.toscrape.com/
Page Title       : All products | Books to Scrape - Sandbox
Total Headings   : 21
Total Paragraphs : 40
Total Links      : 73
------------------------------------------------------------

--- Sample Headings (First 5) ---
  1. [H1] All products
  2. [H3] A Light in the ...
  3. [H3] Tipping the Velvet
  4. [H3] Soumission
  5. [H3] Sharp Objects

--- Sample Paragraphs (First 3) ---
  1. £51.77
  2. In stock
  3. £53.74

--- Sample Normalized Links (First 10) ---
  1. Books to Scrape -> http://books.toscrape.com/index.html
  2. Books -> http://books.toscrape.com/catalogue/category/books_1/index.html
  3. Travel -> http://books.toscrape.com/catalogue/category/books/travel_2/index.html
  4. Mystery -> http://books.toscrape.com/catalogue/category/books/mystery_3/index.html
  5. Historical Fiction -> http://books.toscrape.com/catalogue/category/books/historical-fiction_4/index.html
  6. Sequential Art -> http://books.toscrape.com/catalogue/category/books/sequential-art_5/index.html
  7. Classics -> http://books.toscrape.com/catalogue/category/books/classics_6/index.html
  8. Philosophy -> http://books.toscrape.com/catalogue/category/books/philosophy_7/index.html
  9. Romance -> http://books.toscrape.com/catalogue/category/books/romance_8/index.html
  10. Womens Fiction -> http://books.toscrape.com/catalogue/category/books/womens-fiction_9/index.html
============================================================
```

### Generated JSON (`output/scraped_content.json` excerpt):
```json
{
  "source_url": "http://books.toscrape.com/",
  "title": "All products | Books to Scrape - Sandbox",
  "headings_count": 21,
  "headings": [
    {
      "tag": "h1",
      "text": "All products"
    },
    {
      "tag": "h3",
      "text": "A Light in the ..."
    }
  ],
  "paragraphs_count": 40,
  "paragraphs": [
    "£51.77",
    "In stock"
  ],
  "links_count": 73,
  "links": [
    {
      "text": "Books to Scrape",
      "url": "http://books.toscrape.com/index.html"
    }
  ]
}
```

---

## Web Browser vs. HTTP Scraping
This scraper utilizes `requests` and `BeautifulSoup` to send raw HTTP `GET` requests directly to the web server and parse the received HTML bytes. Because it operates at the network protocol layer:
- It does **not** launch or require a graphical browser to collect data.
- It is significantly faster and consumes fewer system resources than a browser engine.

To inspect the live target webpage visually in your installed Google Chrome browser on Ubuntu, run:
```bash
google-chrome "http://books.toscrape.com/" &
```

---

## Screenshot Evidence & Verification
Under Ubuntu Linux with Wayland (`XDG_SESSION_TYPE=wayland`), background processes cannot take automated desktop screenshots without interactive user portal permissions. To capture authentic screenshot evidence for your submission:
1. Run the scraper interactively in your terminal:
   ```bash
   python task-01-basic-scraping/main.py
   ```
2. Press `Shift + PrintScreen` (or use GNOME Screenshot) to capture your terminal window showing the output summary and the browser displaying the webpage.
3. Save the image inside [`screenshots/`](./screenshots/).

---

## Limitations & Important Notes
1. **Target Site**: `books.toscrape.com` is a dedicated public scraping sandbox designed for educational exercises. It does not enforce aggressive rate limiting or CAPTCHAs.
2. **Dynamic JavaScript**: This implementation uses static HTML parsing (`requests` + `BeautifulSoup`). If targeting Single-Page Applications (SPAs) that render DOM nodes dynamically with client-side JavaScript, a browser automation engine like Selenium (covered in Task 5) would be required.
3. **Anchor Normalization**: In-page anchor fragments (e.g., `#main`) and `javascript:` pseudo-links are intentionally filtered out to ensure all extracted URLs point to navigable web resources.
