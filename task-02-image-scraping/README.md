# Task 2 — Image Scraping

## Objective
Learn how to discover, extract, and download image assets from a public webpage using Python. This implementation discovers all `<img>` tags, normalizes both relative and absolute URLs, downloads at least 10 real images to a local directory using chunked stream I/O, assigns meaningful sanitized filenames, and generates an audit manifest JSON.

---

## What the Implementation Does
The script [`main.py`](./main.py):
1. Sends an HTTP request to `http://books.toscrape.com/` with browser-like headers and timeout handling.
2. Parses the HTML DOM with BeautifulSoup to extract all `<img>` elements.
3. Skips invalid sources, inline data URIs (`data:image/...`), and duplicates.
4. Normalizes relative URLs (e.g., `media/cache/...jpg`) to fully qualified URLs using `urllib.parse.urljoin`.
5. Sanitizes each book's `alt` text to generate human-readable, filesystem-safe filenames with index prefixes (e.g., `01_a-light-in-the-attic.jpg`).
6. Stream-downloads 10 distinct images into [`images/`](./images/) in 8KB chunks to maintain low memory overhead.
7. Validates HTTP response headers (`Content-Type: image/jpeg`) and records exact file byte sizes.
8. Writes a comprehensive report to [`output/download_manifest.json`](./output/download_manifest.json).
9. Prints a formatted execution table to the console.

---

## Libraries and Tools Used
- **Python 3.14+** (Miniconda project virtual environment)
- **`requests`**: For HTTP requests and stream content downloading (`stream=True`, `iter_content()`).
- **`beautifulsoup4`**: For DOM parsing and image element discovery.
- **`urllib.parse`** (Standard Library): For URL resolution (`urljoin`, `urlparse`).
- **`re`**, **`os`**, **`json`** (Standard Library): For filename sanitization, directory management, and manifest serialization.
- **`unittest`** (Standard Library): For offline testing with mocked responses and synthetic HTML fixtures.

---

## Installation & Setup
Activate the shared project virtual environment from the repository root:
```bash
# From repository root
source .venv/bin/activate
```

Dependencies are covered by the project root or local `requirements.txt`:
```bash
pip install -r task-02-image-scraping/requirements.txt
```

---

## How to Run the Code

### 1. Run the Image Scraper
```bash
python task-02-image-scraping/main.py
```

### 2. Run the Automated Unit Tests
```bash
python task-02-image-scraping/tests/test_image_scraper.py -v
```

---

## How to Open and View Downloaded Images on Ubuntu

The 10 downloaded images are stored in `task-02-image-scraping/images/`. You can view them using any of the following methods on Ubuntu:

### Option A: Open the Folder in Ubuntu Files (Nautilus)
```bash
xdg-open "task-02-image-scraping/images"
```
Or:
```bash
nautilus "task-02-image-scraping/images" &
```

### Option B: Open with Ubuntu's Default Image Viewer (Loupe)
```bash
loupe "task-02-image-scraping/images/01_a-light-in-the-attic.jpg" &
```

### Option C: View File Details in Terminal
```bash
ls -lh task-02-image-scraping/images/
file task-02-image-scraping/images/*.jpg
```

---

## How the Implementation Works

```text
[Webpage URL] ---> requests.get()
                         |
                         v
              BeautifulSoup DOM Parsing
                         |
                         v
             Find <img> tags: src, alt
                         |
           urljoin(base_url, relative_src)
                         |
                         v
              Absolute Image URL List
                         |
     +-------------------+-------------------+
     |                                       |
     v                                       v
Sanitize alt text:                   requests.get(stream=True)
"01_a-light-in-the-attic.jpg"                 |
                                    Write 8KB chunks to:
                                  images/01_a-light-in-the-attic.jpg
                                             |
                                             v
                                  Record size, MIME type,
                                  and status into Manifest
                                             |
                                             v
                                output/download_manifest.json
```

- **`sanitize_filename(text, fallback, ext)`**: Removes special characters, converts to lowercase, replaces spaces with hyphens, and truncates to 50 characters to prevent filesystem errors.
- **`extract_image_urls(html, base_url)`**: Traverses the DOM, filters data URIs, resolves URLs with `urljoin`, and dedupes sources.
- **`download_image(image_url, destination_path)`**: Streams image bytes in 8KB chunks, ensuring reliable writes and capturing byte counts.
- **`process_image_downloads(images, images_dir, target_count)`**: Coordinates the batch download of at least 10 images and compiles metadata.

---

## Example Output

### Terminal Execution:
```text
Fetching page HTML from: http://books.toscrape.com/...
Discovering and normalizing image URLs...
Found 20 distinct image candidates.
Downloading 10 images to: .../task-02-image-scraping/images...
Download manifest saved to: .../task-02-image-scraping/output/download_manifest.json

=================================================================
IMAGE SCRAPING SUMMARY
=================================================================
Target URL         : http://books.toscrape.com/
Images Discovered  : 20
Images Downloaded  : 10
Output Directory   : .../task-02-image-scraping/images
-----------------------------------------------------------------
#   | Filename                            | Size       | Status
-----------------------------------------------------------------
1   | 01_a-light-in-the-attic.jpg         | 9,876 B    | SUCCESS
2   | 02_tipping-the-velvet.jpg           | 7,095 B    | SUCCESS
3   | 03_soumission.jpg                   | 4,062 B    | SUCCESS
4   | 04_sharp-objects.jpg                | 8,442 B    | SUCCESS
5   | 05_sapiens-a-brief-history-of-human | 7,986 B    | SUCCESS
6   | 06_the-requiem-red.jpg              | 9,798 B    | SUCCESS
7   | 07_the-dirty-little-secrets-of-gett | 10,740 B   | SUCCESS
8   | 08_the-coming-woman-a-novel-based-o | 9,693 B    | SUCCESS
9   | 09_the-boys-in-the-boat-nine-americ | 8,783 B    | SUCCESS
10  | 10_the-black-maria.jpg              | 3,915 B    | SUCCESS
=================================================================
```

### Generated Manifest (`output/download_manifest.json` excerpt):
```json
{
  "source_url": "http://books.toscrape.com/",
  "total_discovered": 20,
  "requested_count": 10,
  "successful_downloads": 10,
  "downloaded_images": [
    {
      "index": 1,
      "alt_text": "A Light in the Attic",
      "raw_src": "media/cache/2c/da/2cdad67c44b002e7ead0cc35693c0e8b.jpg",
      "absolute_url": "http://books.toscrape.com/media/cache/2c/da/2cdad67c44b002e7ead0cc35693c0e8b.jpg",
      "filename": "01_a-light-in-the-attic.jpg",
      "local_path": ".../task-02-image-scraping/images/01_a-light-in-the-attic.jpg",
      "status": "success",
      "content_type": "image/jpeg",
      "size_bytes": 9876
    }
  ]
}
```

---

## Screenshot Evidence & Verification
Under Ubuntu Linux with Wayland, desktop screen grabs require interactive permissions. To capture screenshot evidence for your submission:
1. Run the script in your terminal:
   ```bash
   python task-02-image-scraping/main.py
   ```
2. Open the image folder in Files:
   ```bash
   xdg-open "task-02-image-scraping/images"
   ```
3. Press **`Shift + PrintScreen`** on Ubuntu to capture the terminal report side-by-side with the opened image folder showing thumbnails.
4. Save the image inside [`screenshots/`](./screenshots/).

---

## Limitations & Important Notes
1. **Stream I/O**: Stream downloading avoids loading entire image files into memory at once, which is critical when scraping large media collections.
2. **Path Sanitization**: `alt` tags often contain punctuation (colons, slashes, exclamation points). Sanitizing alt text into slugified strings prevents invalid filesystem path errors.
3. **Data URIs**: Base64 data URIs (`data:image/...`) are filtered out during extraction to ensure only network-fetchable image assets are downloaded.
