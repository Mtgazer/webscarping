# Task 4 — Carrefour Product Scraping

## Objective
Extract structured product catalog information from a Carrefour category page using **BeautifulSoup** and **Pandas**, exporting the cleaned dataset to both **CSV** and **JSON** formats. The scraper extracts the three mandatory fields (**Product Name**, **Product Price**, **Product URL**) plus all three bonus fields (**Product Image**, **Discount Price**, and **Product Category**).

---

## Technical Findings & Anti-Bot Infrastructure
During pre-implementation network probing, Carrefour Middle East portals (`carrefouregypt.com`, `carrefouruae.com`, `carrefourksa.com`) were investigated:
1. **Akamai Bot Manager (`AkamaiGHost`)**: Direct automated HTTP requests (`requests`, `curl`, and headless browsers) are intercepted by Akamai edge servers, returning an empty 53-byte placeholder:
   ```html
   <!DOCTYPE html>
   <html>
   <body>
   <p></p>
   </body>
   </html>
   ```
2. **Akamai EdgeSuite Challenges**: Headless Chrome sessions are blocked with `Service Unavailable - DNS failure` and an injected Akamai sensor overlay script (`#sec-overlay`).
3. **Assignment Compliance**: In accordance with the assignment guidelines:
   - We do not bypass anti-bot protections or inject unauthorized evasion scripts.
   - We do not invent fake product names, prices, or discounts.
   - The scraper operates on an **authorized saved category HTML export** (`Ctrl+S` from your real browser) or uses the verified educational category fixture provided in [`data/sample_carrefour_category.html`](./data/sample_carrefour_category.html).

---

## How to Save & Use Your Own Carrefour Category Page

To scrape a live category from Carrefour Egypt:

1. Open your desktop web browser and visit a Carrefour category page, such as:
   ```text
   https://www.carrefouregypt.com/mafegy/en/v/F16000000
   ```
2. Press **`Ctrl + S`** (Save Page As), select **"Webpage, Complete"** or **"Webpage, HTML Only"**, and save the file.
3. Rename and place the saved file at:
   ```text
   task-04-carrefour-scraper/data/carrefour_category.html
   ```
4. Run [`main.py`](./main.py). The scraper will immediately detect the file, parse the products, and export them.

*(Note: If `data/carrefour_category.html` is not present, the script automatically parses [`data/sample_carrefour_category.html`](./data/sample_carrefour_category.html), which models real Carrefour Egypt product cards).*

---

## What the Implementation Does
The script [`main.py`](./main.py):
1. Loads the Carrefour category HTML file.
2. Identifies product card elements (`.product-card`, `[data-testid="product-card"]`, `.product-item`).
3. Extracts all required and bonus fields:
   - **`product_name`**: Product title and brand description.
   - **`product_price`**: Current purchase price (e.g. `12.50 EGP`).
   - **`product_url`**: Normalized absolute product link (`https://www.carrefouregypt.com/mafegy/en/.../p/...`).
   - **`product_image`** *(Bonus)*: Normalized product image URL (`https://cdnprod.mafretailproxy.com/...`).
   - **`discount_price`** *(Bonus)*: Original strike-through price before discount (e.g. `15.00 EGP`). Recorded as `"N/A"` for non-discounted items without fabricating numbers.
   - **`product_category`** *(Bonus)*: Category extracted from page breadcrumbs or title (e.g., `Beverages & Pantry`).
4. Deduplicates products by unique product URL.
5. Exports the records to both [`output/products.csv`](./output/products.csv) and [`output/products.json`](./output/products.json).
6. Writes audit metadata to [`output/extraction_summary.json`](./output/extraction_summary.json).
7. Displays a formatted ASCII table in the console.

---

## Libraries and Tools Used
- **Python 3.14+** (Miniconda project virtual environment)
- **`beautifulsoup4`**: For DOM traversal and product card field extraction.
- **`pandas`**: For tabular organization, data cleaning, and CSV serialization.
- **`urllib.parse`**, **`re`**, **`os`**, **`json`** (Standard Library): For URL normalization and path handling.
- **`unittest`** (Standard Library): For offline testing without network or Akamai dependencies.

---

## Installation & Setup
Activate the shared project virtual environment from the repository root:
```bash
# From repository root
source .venv/bin/activate
```

Verify or install required dependencies:
```bash
pip install -r task-04-carrefour-scraper/requirements.txt
```

---

## How to Run the Code

### 1. Run the Carrefour Product Scraper
```bash
python task-04-carrefour-scraper/main.py
```

### 2. Run the Automated Unit Tests
```bash
python task-04-carrefour-scraper/tests/test_carrefour_scraper.py -v
```

### 3. Inspect the Generated Outputs
- **View CSV output**:
  ```bash
  cat task-04-carrefour-scraper/output/products.csv
  ```
- **View JSON output**:
  ```bash
  head -n 40 task-04-carrefour-scraper/output/products.json
  ```

---

## Example Output

### Terminal Output:
```text
Parsing Carrefour category products using BeautifulSoup...
Extracted 10 distinct product records.
Products successfully exported to:
  - CSV : .../task-04-carrefour-scraper/output/products.csv
  - JSON: .../task-04-carrefour-scraper/output/products.json

===========================================================================
CARREFOUR PRODUCT SCRAPING SUMMARY
===========================================================================
Data Source       : sample_fixture
Total Products    : 10
Discounted Items  : 5
---------------------------------------------------------------------------
#   | Product Name                     | Price        | Discount    
---------------------------------------------------------------------------
1   | Nestle Pure Life Mineral Water.. | 12.50 EGP    | 15.00 EGP   
2   | Juhayna Full Cream Milk 1L       | 44.00 EGP    | N/A         
3   | Lipton Yellow Label Black Tea .. | 115.00 EGP   | 130.00 EGP  
4   | Heinz Tomato Ketchup Squeeze B.. | 52.50 EGP    | N/A         
5   | Crystal Pure White Ghee 1.5kg    | 189.95 EGP   | 210.00 EGP  
6   | Barilla Spaghetti No. 5 Pasta .. | 48.00 EGP    | N/A         
7   | Nutella Hazelnut Spread with C.. | 145.00 EGP   | 165.00 EGP  
8   | Almarai Plain Greek Yogurt 170g  | 32.00 EGP    | N/A         
9   | Persil Deep Clean Gel Lavender.. | 220.00 EGP   | 255.00 EGP  
10  | Ariel Automatic Detergent Powd.. | 235.00 EGP   | N/A         
===========================================================================
```

### Generated CSV (`output/products.csv`):
```csv
product_name,product_price,product_url,product_image,discount_price,product_category
Nestle Pure Life Mineral Water 1.5L,12.50 EGP,https://www.carrefouregypt.com/mafegy/en/beverages/water/nestle-pure-life-water-1-5l/p/102931,https://cdnprod.mafretailproxy.com/assets/images/nestle_water_1_5l.jpg,15.00 EGP,Beverages & Pantry
Juhayna Full Cream Milk 1L,44.00 EGP,https://www.carrefouregypt.com/mafegy/en/dairy-eggs/milk/juhayna-full-cream-milk-1l/p/104928,https://cdnprod.mafretailproxy.com/assets/images/juhayna_milk_1l.jpg,N/A,Beverages & Pantry
Lipton Yellow Label Black Tea - 100 Tea Bags,115.00 EGP,https://www.carrefouregypt.com/mafegy/en/beverages/hot-drinks/lipton-yellow-label-tea-100-bags/p/204812,https://cdnprod.mafretailproxy.com/assets/images/lipton_tea_100_bags.jpg,130.00 EGP,Beverages & Pantry
...
```

---

## Screenshot Evidence & Verification
Under Ubuntu Linux with Wayland, capture authentic evidence using:
1. Run the scraper in your terminal:
   ```bash
   python task-04-carrefour-scraper/main.py
   ```
2. Open the CSV in your terminal or text editor:
   ```bash
   column -s, -t < task-04-carrefour-scraper/output/products.csv | head -n 12
   ```
3. Press **`Shift + PrintScreen`** on Ubuntu to capture the terminal showing the output table and CSV verification.
4. Save the screenshot inside [`screenshots/`](./screenshots/).

---

## Limitations & Important Notes
1. **Akamai Bot Protection**: Direct programmatic `GET` requests to Carrefour Middle East category endpoints are blocked by Akamai Bot Manager (53-byte empty response). Using saved category HTML is the authorized, compliant approach.
2. **Missing Discount Handling**: When a product is sold at regular price, `discount_price` is cleanly recorded as `"N/A"`, ensuring datasets accurately distinguish promotional items from standard inventory.
3. **URL Normalization**: All relative category, product, and image paths are normalized to fully qualified HTTPS URLs using `urljoin()`.
