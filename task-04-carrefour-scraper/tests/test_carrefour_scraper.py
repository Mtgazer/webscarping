import csv
import json
import os
import sys
import unittest
import pandas as pd

# Add task directory to sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from main import (
    clean_price,
    extract_products,
    save_results,
)

MINI_HTML = """
<!DOCTYPE html>
<html>
<body>
  <h1>Snacks & Confectionery</h1>
  <div class="product-card">
    <a href="/mafegy/en/snacks/chips-chili-100g/p/999111" class="product-title">Doritos Sweet Chili 100g</a>
    <span class="product-price">20.00 EGP</span>
    <img src="images/chips.jpg" class="product-image">
    <span class="product-discount-price"><del>25.00 EGP</del></span>
  </div>
  <!-- Standard item without discount -->
  <div class="product-card">
    <a href="/mafegy/en/snacks/crackers-salted-150g/p/999222" class="product-title">TUC Salted Crackers 150g</a>
    <span class="product-price">18.50 EGP</span>
    <img src="images/crackers.jpg" class="product-image">
  </div>
  <!-- Duplicate item -->
  <div class="product-card">
    <a href="/mafegy/en/snacks/chips-chili-100g/p/999111" class="product-title">Doritos Sweet Chili 100g</a>
    <span class="product-price">20.00 EGP</span>
  </div>
</body>
</html>
"""


class TestCarrefourScraper(unittest.TestCase):
    def setUp(self):
        self.script_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.sample_html_path = os.path.join(self.script_dir, "data", "sample_carrefour_category.html")
        self.tmp_dir = os.path.join(self.script_dir, "tests", "tmp")
        os.makedirs(self.tmp_dir, exist_ok=True)

    def tearDown(self):
        if os.path.exists(self.tmp_dir):
            for f in os.listdir(self.tmp_dir):
                os.remove(os.path.join(self.tmp_dir, f))
            os.rmdir(self.tmp_dir)

    def test_clean_price(self):
        self.assertEqual(clean_price("  12.50   EGP  "), "12.50 EGP")
        self.assertEqual(clean_price(""), "N/A")
        self.assertEqual(clean_price(None), "N/A")

    def test_extract_products_sample_fixture(self):
        with open(self.sample_html_path, "r", encoding="utf-8") as f:
            html = f.read()

        products = extract_products(html)
        self.assertEqual(len(products), 10)

        # Check required fields on all products
        for p in products:
            self.assertTrue(len(p["product_name"]) > 0)
            self.assertTrue(len(p["product_price"]) > 0)
            self.assertTrue(p["product_url"].startswith("https://www.carrefouregypt.com/"))

    def test_bonus_fields_extracted(self):
        with open(self.sample_html_path, "r", encoding="utf-8") as f:
            html = f.read()

        products = extract_products(html)
        first_product = products[0]

        # First product (Nestle Water) has discount
        self.assertEqual(first_product["product_name"], "Nestle Pure Life Mineral Water 1.5L")
        self.assertEqual(first_product["product_price"], "12.50 EGP")
        self.assertEqual(first_product["discount_price"], "15.00 EGP")
        self.assertTrue(first_product["product_image"].startswith("https://"))
        self.assertEqual(first_product["product_category"], "Beverages & Pantry")

        # Second product (Juhayna Milk) has no discount
        second_product = products[1]
        self.assertEqual(second_product["discount_price"], "N/A")

    def test_deduplication(self):
        products = extract_products(MINI_HTML)
        # Should extract 2 items (skipping duplicate Doritos)
        self.assertEqual(len(products), 2)
        urls = [p["product_url"] for p in products]
        self.assertEqual(len(set(urls)), 2)

    def test_url_normalization(self):
        products = extract_products(MINI_HTML, base_url="https://www.carrefouregypt.com")
        self.assertEqual(products[0]["product_url"], "https://www.carrefouregypt.com/mafegy/en/snacks/chips-chili-100g/p/999111")
        self.assertEqual(products[0]["product_image"], "https://www.carrefouregypt.com/images/chips.jpg")

    def test_save_results_csv_and_json(self):
        sample_records = [
            {
                "product_name": "Test Item",
                "product_price": "10.00 EGP",
                "product_url": "https://www.carrefouregypt.com/p/1",
                "product_image": "https://www.carrefouregypt.com/img.jpg",
                "discount_price": "12.00 EGP",
                "product_category": "Snacks"
            }
        ]
        csv_path = os.path.join(self.tmp_dir, "test.csv")
        json_path = os.path.join(self.tmp_dir, "test.json")

        save_results(sample_records, csv_path, json_path)

        self.assertTrue(os.path.exists(csv_path))
        self.assertTrue(os.path.exists(json_path))

        # Validate CSV
        df = pd.read_csv(csv_path)
        self.assertEqual(len(df), 1)
        self.assertEqual(df.iloc[0]["product_name"], "Test Item")

        # Validate JSON
        with open(json_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]["product_name"], "Test Item")


if __name__ == "__main__":
    unittest.main()
