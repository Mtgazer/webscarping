import json
import os
import sys
import unittest
from unittest.mock import patch, MagicMock

# Add task directory to sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from main import extract_content, save_to_json, fetch_page

SAMPLE_HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>Sample Bookstore Test Page</title>
</head>
<body>
    <h1>Main Catalog</h1>
    <h2>Featured Books</h2>
    <h3>Fiction</h3>
    
    <p>Welcome to our online bookstore catalogue.</p>
    <p>   Discover exciting stories and timeless classics.   </p>
    <p></p>  <!-- Empty paragraph that should be stripped -->

    <div class="links">
        <a href="/catalogue/book1.html">Book One</a>
        <a href="category/fiction.html">Fiction Category</a>
        <a href="https://external.example.com/partner">External Partner</a>
        <a href="../contact.html">Contact Us</a>
        <a href="faq.html">FAQ</a>
        <a href="terms.html">Terms & Conditions</a>
        <a href="#section">Jump Anchor</a>
        <a href="javascript:void(0)">JS Link</a>
    </div>
</body>
</html>
"""


class TestScraper(unittest.TestCase):
    def setUp(self):
        self.base_url = "http://books.toscrape.com/catalogue/"
        self.data = extract_content(SAMPLE_HTML, self.base_url)

    def test_page_title_extraction(self):
        self.assertEqual(self.data["title"], "Sample Bookstore Test Page")

    def test_headings_extraction(self):
        headings = self.data["headings"]
        self.assertEqual(self.data["headings_count"], 3)
        self.assertEqual(headings[0], {"tag": "h1", "text": "Main Catalog"})
        self.assertEqual(headings[1], {"tag": "h2", "text": "Featured Books"})
        self.assertEqual(headings[2], {"tag": "h3", "text": "Fiction"})

    def test_paragraphs_extraction_and_cleaning(self):
        paragraphs = self.data["paragraphs"]
        self.assertEqual(self.data["paragraphs_count"], 2)
        self.assertIn("Welcome to our online bookstore catalogue.", paragraphs)
        self.assertIn("Discover exciting stories and timeless classics.", paragraphs)

    def test_links_count_and_normalization(self):
        links = self.data["links"]
        # Should exclude # anchor and javascript link
        self.assertGreaterEqual(self.data["links_count"], 5)
        self.assertEqual(self.data["links_count"], 6)

        urls = [link["url"] for link in links]
        # Normalization checks
        self.assertIn("http://books.toscrape.com/catalogue/book1.html", urls)
        self.assertIn("http://books.toscrape.com/catalogue/category/fiction.html", urls)
        self.assertIn("https://external.example.com/partner", urls)
        self.assertIn("http://books.toscrape.com/contact.html", urls)

    def test_save_to_json(self):
        test_file = os.path.join(os.path.dirname(__file__), "tmp_test_output.json")
        try:
            save_to_json(self.data, test_file)
            self.assertTrue(os.path.exists(test_file))

            with open(test_file, "r", encoding="utf-8") as f:
                loaded = json.load(f)

            self.assertEqual(loaded["title"], self.data["title"])
            self.assertEqual(loaded["links_count"], self.data["links_count"])
        finally:
            if os.path.exists(test_file):
                os.remove(test_file)

    @patch("requests.get")
    def test_fetch_page_mocked(self, mock_get):
        mock_response = MagicMock()
        mock_response.text = SAMPLE_HTML
        mock_response.apparent_encoding = "utf-8"
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response

        html = fetch_page("http://books.toscrape.com/mock")
        self.assertIn("Sample Bookstore Test Page", html)
        mock_get.assert_called_once()


if __name__ == "__main__":
    unittest.main()
