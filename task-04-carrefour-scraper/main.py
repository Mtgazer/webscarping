import json
import os
import re
import sys
from urllib.parse import urljoin
from bs4 import BeautifulSoup
import pandas as pd


def clean_price(text: str) -> str:
    """Clean and normalize price text."""
    if not text:
        return "N/A"
    # Normalize spaces
    cleaned = re.sub(r"\s+", " ", text).strip()
    return cleaned if cleaned else "N/A"


def extract_category_name(soup: BeautifulSoup) -> str:
    """Extract page category from breadcrumbs, headings, or title."""
    # 1. Breadcrumbs
    cat_tag = soup.find(id=lambda i: i in ["category-name", "category_name"]) or soup.find(class_=lambda c: c and "category-title" in c)
    if cat_tag:
        name = cat_tag.get_text(strip=True)
        if name:
            return name

    # 2. Page H1
    h1 = soup.find("h1")
    if h1:
        name = h1.get_text(strip=True)
        if name and "carrefour" not in name.lower():
            return name

    # 3. Fallback
    return "Supermarket Products"


def extract_products(html_content: str, base_url: str = "https://www.carrefouregypt.com") -> list[dict]:
    """Extract product records with required and bonus fields from Carrefour category HTML."""
    soup = BeautifulSoup(html_content, "html.parser")
    products = []
    seen_urls = set()

    page_category = extract_category_name(soup)

    # Identify product card containers
    cards = []
    for tag in soup.find_all(["div", "article"]):
        classes = tag.get("class", [])
        testid = tag.get("data-testid", "")
        tag_id = tag.get("id", "")
        if any(c in classes for c in ["product-card", "product-item"]) or any(t in testid for t in ["product-card", "product_card"]) or "product-card" in tag_id:
            cards.append(tag)

    for card in cards:
        # 1. Product Name & Link
        name_tag = (
            card.find(attrs={"data-testid": "product-title"})
            or card.find(attrs={"data-testid": "product_title"})
            or card.find(class_=lambda c: c and any(t in c for t in ["product-title", "product_title", "product-name"]))
            or card.find("a", href=lambda h: h and "/p/" in h)
        )
        if not name_tag:
            continue

        product_name = name_tag.get_text(strip=True)
        if not product_name:
            continue

        # 2. Product URL
        link_tag = name_tag if name_tag.name == "a" and name_tag.get("href") else card.find("a", href=lambda h: h and "/p/" in h)
        if not link_tag or not link_tag.get("href"):
            continue

        product_url = urljoin(base_url, link_tag["href"].strip())
        if product_url in seen_urls:
            continue

        # 3. Product Price (Current Price)
        price_tag = (
            card.find(attrs={"data-testid": "product-price"})
            or card.find(class_=lambda c: c and any(p in c for p in ["product-price", "current-price", "price-new", "price"]))
        )
        product_price = clean_price(price_tag.get_text(strip=True)) if price_tag else "N/A"

        # 4. Bonus: Product Image URL
        img_tag = (
            card.find("img", attrs={"data-testid": "product-image"})
            or card.find("img", class_=lambda c: c and any(m in c for m in ["product-image", "product-img"]))
            or card.find("img", src=True)
        )
        product_image = "N/A"
        if img_tag and img_tag.get("src"):
            product_image = urljoin(base_url, img_tag["src"].strip())

        # 5. Bonus: Discount Price / Original Price (if on sale)
        discount_tag = (
            card.find(attrs={"data-testid": "product-discount-price"})
            or card.find(class_=lambda c: c and any(d in c for d in ["product-discount-price", "old-price", "price-old", "was-price"]))
            or card.find("del")
        )
        discount_price = clean_price(discount_tag.get_text(strip=True)) if discount_tag else "N/A"

        # 6. Bonus: Product Category
        product_category = page_category

        seen_urls.add(product_url)
        products.append({
            "product_name": product_name,
            "product_price": product_price,
            "product_url": product_url,
            "product_image": product_image,
            "discount_price": discount_price,
            "product_category": product_category
        })

    return products


def save_results(products: list[dict], csv_path: str, json_path: str) -> None:
    """Save extracted products to CSV (via Pandas) and JSON."""
    os.makedirs(os.path.dirname(csv_path), exist_ok=True)
    os.makedirs(os.path.dirname(json_path), exist_ok=True)

    # 1. Export CSV with Pandas
    df = pd.DataFrame(products)
    if not df.empty:
        # Standardize column order
        cols = ["product_name", "product_price", "product_url", "product_image", "discount_price", "product_category"]
        df = df[cols]
    df.to_csv(csv_path, index=False, encoding="utf-8")

    # 2. Export JSON
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(products, f, indent=2, ensure_ascii=False)


def display_summary(products: list[dict], source_info: str) -> None:
    """Print readable terminal table and summary statistics."""
    print("=" * 75)
    print("CARREFOUR PRODUCT SCRAPING SUMMARY")
    print("=" * 75)
    print(f"Data Source       : {source_info}")
    print(f"Total Products    : {len(products)}")
    discounted_count = sum(1 for p in products if p["discount_price"] != "N/A")
    print(f"Discounted Items  : {discounted_count}")
    print("-" * 75)
    print(f"{'#':<3} | {'Product Name':<32} | {'Price':<12} | {'Discount':<12}")
    print("-" * 75)

    for idx, p in enumerate(products, start=1):
        name_preview = (p["product_name"][:30] + "..") if len(p["product_name"]) > 32 else p["product_name"]
        print(f"{idx:<3} | {name_preview:<32} | {p['product_price']:<12} | {p['discount_price']:<12}")

    print("=" * 75)


def main() -> None:
    script_dir = os.path.dirname(os.path.abspath(__file__))
    user_file = os.path.join(script_dir, "data", "carrefour_category.html")
    sample_file = os.path.join(script_dir, "data", "sample_carrefour_category.html")
    output_csv = os.path.join(script_dir, "output", "products.csv")
    output_json = os.path.join(script_dir, "output", "products.json")
    output_summary = os.path.join(script_dir, "output", "extraction_summary.json")

    # Select input file (user saved export if available, otherwise sample fixture)
    if os.path.exists(user_file):
        input_path = user_file
        source_type = "user_saved_export"
        print(f"Loading user saved Carrefour category export: {user_file}")
    elif os.path.exists(sample_file):
        input_path = sample_file
        source_type = "sample_fixture"
        print("=" * 75)
        print("NOTICE: No personal Carrefour export found at data/carrefour_category.html.")
        print("Using the verified sample category fixture: data/sample_carrefour_category.html")
        print("To scrape your own category page, open Carrefour in your browser, press Ctrl+S,")
        print(f"and place the saved HTML at: {user_file}")
        print("=" * 75 + "\n")
    else:
        print(f"Error: Neither {user_file} nor {sample_file} could be found.", file=sys.stderr)
        sys.exit(1)

    with open(input_path, "r", encoding="utf-8") as f:
        html_content = f.read()

    print(f"Parsing Carrefour category products using BeautifulSoup...")
    products = extract_products(html_content)
    print(f"Extracted {len(products)} distinct product records.")

    save_results(products, output_csv, output_json)
    print(f"Products successfully exported to:\n  - CSV : {output_csv}\n  - JSON: {output_json}")

    # Save summary metadata
    summary = {
        "input_source": input_path,
        "source_type": source_type,
        "total_products": len(products),
        "discounted_products": sum(1 for p in products if p["discount_price"] != "N/A"),
        "csv_output": output_csv,
        "json_output": output_json
    }
    with open(output_summary, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)

    print()
    display_summary(products, source_info=source_type)


if __name__ == "__main__":
    main()
