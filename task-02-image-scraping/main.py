import json
import os
import re
import sys
from urllib.parse import urljoin, urlparse
import requests
from bs4 import BeautifulSoup


def sanitize_filename(text: str, fallback: str, ext: str = ".jpg") -> str:
    """Create a clean, filesystem-safe filename from text or fallback."""
    # Remove leading/trailing whitespace and convert to lowercase
    cleaned = text.strip().lower()
    # Replace non-alphanumeric characters with hyphens
    cleaned = re.sub(r"[^a-z0-9]+", "-", cleaned).strip("-")
    
    if not cleaned:
        cleaned = re.sub(r"[^a-z0-9]+", "-", fallback.strip().lower()).strip("-")
        
    if not cleaned:
        cleaned = "image"
        
    # Ensure correct extension
    if not ext.startswith("."):
        ext = "." + ext
        
    return f"{cleaned[:50]}{ext}"


def extract_image_urls(html: str, base_url: str) -> list[dict]:
    """Parse HTML and discover all image elements with resolved absolute URLs."""
    soup = BeautifulSoup(html, "html.parser")
    images = []
    seen_urls = set()

    for idx, img in enumerate(soup.find_all("img"), start=1):
        src = img.get("src", "").strip()
        if not src or src.startswith("data:"):
            continue

        absolute_url = urljoin(base_url, src)
        if absolute_url in seen_urls:
            continue
        seen_urls.add(absolute_url)

        alt_text = img.get("alt", "").strip()
        
        # Derive file extension from URL path
        parsed_path = urlparse(absolute_url).path
        _, url_ext = os.path.splitext(parsed_path)
        ext = url_ext if url_ext else ".jpg"

        images.append({
            "index": idx,
            "raw_src": src,
            "absolute_url": absolute_url,
            "alt_text": alt_text,
            "extension": ext
        })

    return images


def download_image(image_url: str, destination_path: str, timeout: int = 10) -> tuple[bool, str, int, str]:
    """Stream download an image file and return status, content-type, byte size, and error message."""
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (X11; Linux x86_64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/124.0.0.0 Safari/537.36"
        )
    }
    try:
        response = requests.get(image_url, headers=headers, timeout=timeout, stream=True)
        response.raise_for_status()
        
        content_type = response.headers.get("Content-Type", "application/octet-stream")
        total_bytes = 0

        os.makedirs(os.path.dirname(destination_path), exist_ok=True)
        with open(destination_path, "wb") as f:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)
                    total_bytes += len(chunk)

        return True, content_type, total_bytes, ""
    except requests.exceptions.RequestException as e:
        return False, "", 0, str(e)


def process_image_downloads(
    images: list[dict],
    images_dir: str,
    target_count: int = 10
) -> list[dict]:
    """Download at least target_count images and build a manifest report."""
    os.makedirs(images_dir, exist_ok=True)
    results = []

    for idx, item in enumerate(images[:target_count], start=1):
        filename = f"{idx:02d}_{sanitize_filename(item['alt_text'], fallback=f'image_{idx}', ext=item['extension'])}"
        local_filepath = os.path.join(images_dir, filename)

        success, content_type, size_bytes, error = download_image(item["absolute_url"], local_filepath)

        record = {
            "index": idx,
            "alt_text": item["alt_text"],
            "raw_src": item["raw_src"],
            "absolute_url": item["absolute_url"],
            "filename": filename,
            "local_path": local_filepath,
            "status": "success" if success else "failed",
            "content_type": content_type,
            "size_bytes": size_bytes
        }
        if not success:
            record["error"] = error

        results.append(record)

    return results


def save_manifest(manifest_data: dict, filepath: str) -> None:
    """Save download manifest to formatted JSON file."""
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(manifest_data, f, indent=2, ensure_ascii=False)


def display_summary(manifest: dict) -> None:
    """Print readable terminal report of downloaded images."""
    print("=" * 65)
    print("IMAGE SCRAPING SUMMARY")
    print("=" * 65)
    print(f"Target URL         : {manifest['source_url']}")
    print(f"Images Discovered  : {manifest['total_discovered']}")
    print(f"Images Downloaded  : {manifest['successful_downloads']}")
    print(f"Output Directory   : {manifest['images_directory']}")
    print("-" * 65)
    print(f"{'#':<3} | {'Filename':<35} | {'Size':<10} | {'Status'}")
    print("-" * 65)

    for item in manifest["downloaded_images"]:
        size_str = f"{item['size_bytes']:,} B" if item["status"] == "success" else "0 B"
        print(f"{item['index']:<3} | {item['filename'][:35]:<35} | {size_str:<10} | {item['status'].upper()}")

    print("=" * 65)


def main() -> None:
    target_url = "http://books.toscrape.com/"
    script_dir = os.path.dirname(os.path.abspath(__file__))
    images_dir = os.path.join(script_dir, "images")
    manifest_path = os.path.join(script_dir, "output", "download_manifest.json")
    required_download_count = 10

    print(f"Fetching page HTML from: {target_url}...")
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (X11; Linux x86_64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/124.0.0.0 Safari/537.36"
        )
    }
    try:
        response = requests.get(target_url, headers=headers, timeout=10)
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        print(f"Failed to fetch {target_url}: {e}", file=sys.stderr)
        sys.exit(1)

    print("Discovering and normalizing image URLs...")
    discovered_images = extract_image_urls(response.text, base_url=target_url)
    print(f"Found {len(discovered_images)} distinct image candidates.")

    if len(discovered_images) < required_download_count:
        print(
            f"Error: Website provided only {len(discovered_images)} images, "
            f"minimum requirement is {required_download_count}.",
            file=sys.stderr
        )
        sys.exit(1)

    print(f"Downloading {required_download_count} images to: {images_dir}...")
    download_records = process_image_downloads(
        discovered_images,
        images_dir=images_dir,
        target_count=required_download_count
    )

    success_count = sum(1 for r in download_records if r["status"] == "success")

    manifest = {
        "source_url": target_url,
        "total_discovered": len(discovered_images),
        "requested_count": required_download_count,
        "successful_downloads": success_count,
        "images_directory": images_dir,
        "downloaded_images": download_records
    }

    save_manifest(manifest, manifest_path)
    print(f"Download manifest saved to: {manifest_path}\n")

    display_summary(manifest)


if __name__ == "__main__":
    main()
