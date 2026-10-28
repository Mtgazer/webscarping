import json
import os
import re
import sys
from urllib.parse import urljoin
from bs4 import BeautifulSoup
import pandas as pd


def parse_youtube_subscriptions(html_content: str, base_url: str = "https://www.youtube.com") -> list[dict]:
    """Parse authorized YouTube subscriptions HTML and extract channel names, URLs, and public subscriber counts."""
    soup = BeautifulSoup(html_content, "html.parser")
    channels = []
    seen_urls = set()

    # Pattern to detect subscriber count strings (e.g., "11.9M subscribers", "621K subscribers")
    sub_pattern = re.compile(r"(\d+(?:\.\d+)?\s*[KMBkmb]?\s*subscribers?)", re.IGNORECASE)

    # 1. Parse standard YouTube web renderer elements (<ytd-channel-renderer>) and subscription divs
    renderers = soup.find_all("ytd-channel-renderer") + soup.find_all("div", class_=lambda c: c and any(k in c for k in ["subscription-item", "channel-item", "ytd-channel-renderer"]))

    for item in renderers:
        # Locate the primary channel link
        link_tag = item.find("a", href=True)
        if not link_tag:
            continue

        raw_href = link_tag.get("href", "").strip()
        if not raw_href or raw_href == "#":
            continue

        # Filter out non-channel links
        if not any(pattern in raw_href for pattern in ["/@", "/channel/", "/user/", "/c/"]):
            continue

        channel_url = urljoin(base_url, raw_href)
        if channel_url in seen_urls:
            continue

        # Channel name extraction (including native YouTube <yt-formatted-string> web components)
        name_tag = item.find(["span", "h3", "div", "yt-formatted-string"], id=lambda i: i in ["text", "channel-title", "title"])
        if name_tag:
            channel_name = name_tag.get_text(strip=True)
        else:
            channel_name = link_tag.get_text(strip=True)

        if not channel_name:
            continue

        # Subscriber count extraction (where publicly shown)
        subscriber_count = "N/A"
        sub_tag = item.find(["span", "div", "yt-formatted-string"], id=lambda i: i in ["subscribers", "video-count"]) or item.find(class_=lambda c: c and "sub" in c)
        if sub_tag:
            text = sub_tag.get_text(strip=True)
            match = sub_pattern.search(text)
            if match:
                subscriber_count = match.group(1).strip()
        else:
            # Search within whole item text for subscriber pattern
            match = sub_pattern.search(item.get_text())
            if match:
                subscriber_count = match.group(1).strip()

        seen_urls.add(channel_url)
        channels.append({
            "channel_name": channel_name,
            "channel_url": channel_url,
            "subscriber_count": subscriber_count
        })

    # 2. Fallback: Parse generic standalone <a> anchor lists (e.g. bookmarks or simplified HTML)
    if not channels:
        for a in soup.find_all("a", href=True):
            href = a.get("href", "").strip()
            if any(pattern in href for pattern in ["/@", "/channel/", "/user/", "/c/"]):
                channel_url = urljoin(base_url, href)
                if channel_url in seen_urls:
                    continue
                channel_name = a.get_text(strip=True)
                if not channel_name:
                    continue

                seen_urls.add(channel_url)
                channels.append({
                    "channel_name": channel_name,
                    "channel_url": channel_url,
                    "subscriber_count": "N/A"
                })

    return channels


def create_subscriptions_dataframe(records: list[dict]) -> pd.DataFrame:
    """Convert raw channel records into a cleaned, sorted Pandas DataFrame."""
    if not records:
        return pd.DataFrame(columns=["channel_name", "channel_url", "subscriber_count"])

    df = pd.DataFrame(records)
    # Ensure correct columns and order
    df = df[["channel_name", "channel_url", "subscriber_count"]]
    # Clean whitespace
    df["channel_name"] = df["channel_name"].astype(str).str.strip()
    df["channel_url"] = df["channel_url"].astype(str).str.strip()
    df["subscriber_count"] = df["subscriber_count"].astype(str).str.strip()
    # Sort alphabetically by channel name
    df = df.sort_values(by="channel_name", key=lambda col: col.str.lower()).reset_index(drop=True)
    return df


def export_dataframe_to_csv(df: pd.DataFrame, filepath: str) -> None:
    """Export DataFrame to a clean CSV file."""
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    df.to_csv(filepath, index=False, encoding="utf-8")


def main() -> None:
    script_dir = os.path.dirname(os.path.abspath(__file__))
    user_file = os.path.join(script_dir, "data", "subscriptions.html")
    sample_file = os.path.join(script_dir, "data", "sample_subscriptions.html")
    output_csv = os.path.join(script_dir, "output", "youtube_subscriptions.csv")
    output_summary = os.path.join(script_dir, "output", "extraction_summary.json")

    # Select input file (user export if present, otherwise sample fixture)
    if os.path.exists(user_file):
        input_path = user_file
        source_type = "user_authorized_export"
        print(f"Loading authorized user export: {user_file}")
    elif os.path.exists(sample_file):
        input_path = sample_file
        source_type = "sample_fixture"
        print("=" * 70)
        print("NOTICE: No personal subscriptions file found at data/subscriptions.html.")
        print("Using the safe verified sample fixture: data/sample_subscriptions.html")
        print("To parse your own account subscriptions, export and save your HTML to:")
        print(f"  {user_file}")
        print("=" * 70 + "\n")
    else:
        print(f"Error: Neither {user_file} nor {sample_file} could be found.", file=sys.stderr)
        sys.exit(1)

    with open(input_path, "r", encoding="utf-8") as f:
        html_content = f.read()

    print(f"Parsing YouTube subscription channels using BeautifulSoup...")
    records = parse_youtube_subscriptions(html_content)
    print(f"Extracted {len(records)} distinct channel records.")

    print("Constructing and sorting Pandas DataFrame...")
    df = create_subscriptions_dataframe(records)

    export_dataframe_to_csv(df, output_csv)
    print(f"Results successfully saved to CSV: {output_csv}")

    # Save summary metadata
    with_subs = int((df["subscriber_count"] != "N/A").sum())
    summary = {
        "input_source": input_path,
        "source_type": source_type,
        "total_channels": len(df),
        "channels_with_subscriber_count": with_subs,
        "channels_without_subscriber_count": len(df) - with_subs,
        "csv_output": output_csv
    }
    with open(output_summary, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)

    # Display clean table
    print("\n" + "=" * 70)
    print("EXTRACTED YOUTUBE SUBSCRIPTIONS (Pandas DataFrame)")
    print("=" * 70)
    print(df.to_string(index=True))
    print("=" * 70)
    print(f"Total Channels: {len(df)} | Public Subscriber Counts Available: {with_subs}")
    print("=" * 70 + "\n")


if __name__ == "__main__":
    main()
