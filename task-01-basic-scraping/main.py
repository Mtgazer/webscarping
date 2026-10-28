import json
import os
import sys
from urllib.parse import urljoin
import requests
from bs4 import BeautifulSoup


def fetch_page(url: str, timeout: int = 10) -> str:
    """Fetch webpage HTML using requests with a realistic user-agent and timeout."""
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (X11; Linux x86_64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/124.0.0.0 Safari/537.36"
        )
    }
    response = requests.get(url, headers=headers, timeout=timeout)
    response.raise_for_status()
    # Ensure correct text decoding, preferring detected charset over fallback
    response.encoding = response.apparent_encoding or "utf-8"
    return response.text


def extract_content(html: str, base_url: str) -> dict:
    """Extract and clean title, headings, paragraphs, and normalized links."""
    soup = BeautifulSoup(html, "html.parser")

    # Page title
    title = soup.title.get_text(strip=True) if soup.title else "No Title Found"

    # Headings (h1 through h6)
    headings = []
    for tag in soup.find_all(["h1", "h2", "h3", "h4", "h5", "h6"]):
        text = tag.get_text(strip=True)
        if text:
            headings.append({
                "tag": tag.name,
                "text": text
            })

    # Paragraphs
    paragraphs = []
    for p in soup.find_all("p"):
        text = p.get_text(strip=True)
        if text:
            paragraphs.append(text)

    # Links (normalized to absolute URLs)
    links = []
    seen_urls = set()
    for a in soup.find_all("a", href=True):
        href = a.get("href", "").strip()
        if not href or href.startswith("javascript:") or href.startswith("#"):
            continue
        absolute_url = urljoin(base_url, href)
        if absolute_url not in seen_urls:
            seen_urls.add(absolute_url)
            link_text = a.get_text(strip=True) or "[No Anchor Text]"
            links.append({
                "text": link_text,
                "url": absolute_url
            })

    return {
        "source_url": base_url,
        "title": title,
        "headings_count": len(headings),
        "headings": headings,
        "paragraphs_count": len(paragraphs),
        "paragraphs": paragraphs,
        "links_count": len(links),
        "links": links
    }


def save_to_json(data: dict, filepath: str) -> None:
    """Save extracted data to a formatted JSON file."""
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def display_summary(data: dict, link_limit: int = 10, heading_limit: int = 5) -> None:
    """Print a clean, readable terminal summary of the scraped content."""
    print("=" * 60)
    print("SCRAPED WEBPAGE SUMMARY")
    print("=" * 60)
    print(f"Source URL       : {data['source_url']}")
    print(f"Page Title       : {data['title']}")
    print(f"Total Headings   : {data['headings_count']}")
    print(f"Total Paragraphs : {data['paragraphs_count']}")
    print(f"Total Links      : {data['links_count']}")
    print("-" * 60)

    print(f"\n--- Sample Headings (First {min(heading_limit, data['headings_count'])}) ---")
    for idx, h in enumerate(data["headings"][:heading_limit], start=1):
        print(f"  {idx}. [{h['tag'].upper()}] {h['text']}")

    print(f"\n--- Sample Paragraphs (First {min(3, data['paragraphs_count'])}) ---")
    for idx, p in enumerate(data["paragraphs"][:3], start=1):
        preview = (p[:80] + "...") if len(p) > 80 else p
        print(f"  {idx}. {preview}")

    print(f"\n--- Sample Normalized Links (First {min(link_limit, data['links_count'])}) ---")
    for idx, link in enumerate(data["links"][:link_limit], start=1):
        print(f"  {idx}. {link['text']} -> {link['url']}")

    print("\n" + "=" * 60)


def main() -> None:
    target_url = "http://books.toscrape.com/"
    script_dir = os.path.dirname(os.path.abspath(__file__))
    output_path = os.path.join(script_dir, "output", "scraped_content.json")

    print(f"Sending HTTP request to: {target_url}...")
    try:
        html = fetch_page(target_url, timeout=10)
    except requests.exceptions.RequestException as e:
        print(f"Network error while requesting {target_url}: {e}", file=sys.stderr)
        sys.exit(1)

    print("Extracting page title, headings, paragraphs, and links...")
    data = extract_content(html, base_url=target_url)

    if data["links_count"] < 5:
        print(f"Warning: Expected at least 5 links, but found {data['links_count']}.")

    save_to_json(data, output_path)
    print(f"Results successfully saved to: {output_path}")

    display_summary(data)


if __name__ == "__main__":
    main()
