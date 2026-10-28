import json
import os
import shutil
import sys
import unittest
from unittest.mock import patch, MagicMock

# Add task directory to sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from main import (
    sanitize_filename,
    extract_image_urls,
    download_image,
    process_image_downloads,
    save_manifest,
)

SAMPLE_HTML = """
<!DOCTYPE html>
<html>
<body>
    <div class="gallery">
        <img src="media/cache/cover1.jpg" alt="The Great Gatsby!">
        <img src="/media/cache/cover2.png" alt="1984 - George Orwell">
        <img src="https://external.example.com/images/cover3.jpeg" alt="Brave New World">
        <img src="../shared/cover4.webp" alt="">
        <img src="media/cache/cover1.jpg" alt="Duplicate Cover">
        <img src="data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAAB" alt="Data URI">
        <img src="" alt="Empty Src">
    </div>
</body>
</html>
"""


class TestImageScraper(unittest.TestCase):
    def setUp(self):
        self.base_url = "http://books.toscrape.com/catalogue/"
        self.test_tmp_dir = os.path.join(os.path.dirname(__file__), "tmp_test_images")
        os.makedirs(self.test_tmp_dir, exist_ok=True)

    def tearDown(self):
        if os.path.exists(self.test_tmp_dir):
            shutil.rmtree(self.test_tmp_dir)

    def test_sanitize_filename(self):
        self.assertEqual(
            sanitize_filename("The Great Gatsby!", fallback="book", ext=".jpg"),
            "the-great-gatsby.jpg"
        )
        self.assertEqual(
            sanitize_filename("  Sapiens: A Brief History?  ", fallback="book", ext=".png"),
            "sapiens-a-brief-history.png"
        )
        # Empty text falls back to fallback
        self.assertEqual(
            sanitize_filename("", fallback="image_5", ext=".jpg"),
            "image-5.jpg"
        )
        # Only symbols falls back
        self.assertEqual(
            sanitize_filename("???!!!", fallback="custom-fallback", ext=".jpg"),
            "custom-fallback.jpg"
        )

    def test_extract_image_urls_resolution_and_filtering(self):
        images = extract_image_urls(SAMPLE_HTML, self.base_url)

        # Should extract 4 distinct images (skips duplicate, data URI, and empty src)
        self.assertEqual(len(images), 4)

        urls = [img["absolute_url"] for img in images]
        self.assertEqual(urls[0], "http://books.toscrape.com/catalogue/media/cache/cover1.jpg")
        self.assertEqual(urls[1], "http://books.toscrape.com/media/cache/cover2.png")
        self.assertEqual(urls[2], "https://external.example.com/images/cover3.jpeg")
        self.assertEqual(urls[3], "http://books.toscrape.com/shared/cover4.webp")

        self.assertEqual(images[0]["alt_text"], "The Great Gatsby!")
        self.assertEqual(images[0]["extension"], ".jpg")
        self.assertEqual(images[1]["extension"], ".png")

    @patch("requests.get")
    def test_download_image_success(self, mock_get):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.headers = {"Content-Type": "image/jpeg"}
        mock_response.iter_content.return_value = [b"fake_image_bytes_chunk_1", b"fake_image_bytes_chunk_2"]
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response

        dest_file = os.path.join(self.test_tmp_dir, "test_cover.jpg")
        success, content_type, size, err = download_image("http://example.com/cover.jpg", dest_file)

        self.assertTrue(success)
        self.assertEqual(content_type, "image/jpeg")
        self.assertEqual(size, len(b"fake_image_bytes_chunk_1fake_image_bytes_chunk_2"))
        self.assertEqual(err, "")
        self.assertTrue(os.path.exists(dest_file))

    @patch("main.download_image")
    def test_process_image_downloads_batch(self, mock_download):
        mock_download.return_value = (True, "image/jpeg", 5000, "")

        mock_images = [
            {
                "index": i,
                "alt_text": f"Book Title {i}",
                "raw_src": f"media/cover_{i}.jpg",
                "absolute_url": f"http://books.toscrape.com/media/cover_{i}.jpg",
                "extension": ".jpg"
            }
            for i in range(1, 15)
        ]

        results = process_image_downloads(mock_images, self.test_tmp_dir, target_count=10)

        self.assertEqual(len(results), 10)
        self.assertEqual(mock_download.call_count, 10)
        self.assertTrue(all(r["status"] == "success" for r in results))
        self.assertEqual(results[0]["filename"], "01_book-title-1.jpg")
        self.assertEqual(results[9]["filename"], "10_book-title-10.jpg")

    def test_save_manifest(self):
        manifest_data = {
            "source_url": "http://example.com",
            "successful_downloads": 1,
            "downloaded_images": [{"index": 1, "filename": "sample.jpg"}]
        }
        manifest_path = os.path.join(self.test_tmp_dir, "manifest.json")
        save_manifest(manifest_data, manifest_path)

        self.assertTrue(os.path.exists(manifest_path))
        with open(manifest_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        self.assertEqual(data["source_url"], "http://example.com")
        self.assertEqual(data["successful_downloads"], 1)


if __name__ == "__main__":
    unittest.main()
