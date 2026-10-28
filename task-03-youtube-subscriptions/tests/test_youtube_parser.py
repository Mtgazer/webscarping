import csv
import os
import sys
import unittest
import pandas as pd

# Add task directory to sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from main import (
    parse_youtube_subscriptions,
    create_subscriptions_dataframe,
    export_dataframe_to_csv,
)

MINI_HTML = """
<!DOCTYPE html>
<html>
<body>
  <ytd-channel-renderer>
    <a href="/@TestChannelA">
      <span id="text">Alpha Academy</span>
      <span id="subscribers">100K subscribers</span>
    </a>
  </ytd-channel-renderer>
  <ytd-channel-renderer>
    <a href="/@TestChannelB">
      <span id="text">Beta Labs</span>
    </a>
  </ytd-channel-renderer>
  <!-- Duplicate Alpha Academy -->
  <ytd-channel-renderer>
    <a href="/@TestChannelA">
      <span id="text">Alpha Academy Duplicate</span>
      <span id="subscribers">100K subscribers</span>
    </a>
  </ytd-channel-renderer>
</body>
</html>
"""


class TestYouTubeParser(unittest.TestCase):
    def setUp(self):
        self.script_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.sample_html_path = os.path.join(self.script_dir, "data", "sample_subscriptions.html")

    def test_parse_sample_fixture_count(self):
        with open(self.sample_html_path, "r", encoding="utf-8") as f:
            html = f.read()

        records = parse_youtube_subscriptions(html)
        # Should extract 8 unique channels (deduping freeCodeCamp)
        self.assertEqual(len(records), 8)

    def test_deduplication(self):
        records = parse_youtube_subscriptions(MINI_HTML)
        self.assertEqual(len(records), 2)
        urls = [r["channel_url"] for r in records]
        self.assertEqual(urls, ["https://www.youtube.com/@TestChannelA", "https://www.youtube.com/@TestChannelB"])

    def test_native_yt_formatted_string_support(self):
        polymer_html = """
        <ytd-channel-renderer>
          <a href="/@PolymerTech">
            <yt-formatted-string id="text">Polymer Tech</yt-formatted-string>
            <yt-formatted-string id="video-count">3.5M subscribers</yt-formatted-string>
          </a>
        </ytd-channel-renderer>
        """
        records = parse_youtube_subscriptions(polymer_html)
        self.assertEqual(len(records), 1)
        self.assertEqual(records[0]["channel_name"], "Polymer Tech")
        self.assertEqual(records[0]["subscriber_count"], "3.5M subscribers")
        self.assertEqual(records[0]["channel_url"], "https://www.youtube.com/@PolymerTech")

    def test_subscriber_count_handling(self):
        records = parse_youtube_subscriptions(MINI_HTML)
        self.assertEqual(records[0]["subscriber_count"], "100K subscribers")
        # Missing subscriber count should be N/A, never invented
        self.assertEqual(records[1]["subscriber_count"], "N/A")

    def test_url_normalization(self):
        records = parse_youtube_subscriptions(MINI_HTML)
        self.assertTrue(records[0]["channel_url"].startswith("https://www.youtube.com/"))
        self.assertTrue(records[1]["channel_url"].startswith("https://www.youtube.com/"))

    def test_dataframe_creation_and_sorting(self):
        records = [
            {"channel_name": "Zulu Tech", "channel_url": "https://www.youtube.com/@zulu", "subscriber_count": "10K subscribers"},
            {"channel_name": "Alpha Coding", "channel_url": "https://www.youtube.com/@alpha", "subscriber_count": "50K subscribers"}
        ]
        df = create_subscriptions_dataframe(records)

        self.assertIsInstance(df, pd.DataFrame)
        self.assertEqual(list(df.columns), ["channel_name", "channel_url", "subscriber_count"])
        # Should be sorted alphabetically (Alpha before Zulu)
        self.assertEqual(df.iloc[0]["channel_name"], "Alpha Coding")
        self.assertEqual(df.iloc[1]["channel_name"], "Zulu Tech")

    def test_csv_export(self):
        records = [
            {"channel_name": "Demo Channel", "channel_url": "https://www.youtube.com/@demo", "subscriber_count": "1K subscribers"}
        ]
        df = create_subscriptions_dataframe(records)
        tmp_csv = os.path.join(self.script_dir, "output", "test_tmp.csv")

        try:
            export_dataframe_to_csv(df, tmp_csv)
            self.assertTrue(os.path.exists(tmp_csv))

            with open(tmp_csv, "r", encoding="utf-8") as f:
                reader = list(csv.reader(f))

            self.assertEqual(reader[0], ["channel_name", "channel_url", "subscriber_count"])
            self.assertEqual(reader[1], ["Demo Channel", "https://www.youtube.com/@demo", "1K subscribers"])
        finally:
            if os.path.exists(tmp_csv):
                os.remove(tmp_csv)


if __name__ == "__main__":
    unittest.main()
