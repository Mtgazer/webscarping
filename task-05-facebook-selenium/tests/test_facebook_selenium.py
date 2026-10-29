import os
import sys
import unittest
from unittest.mock import patch
from selenium.webdriver.common.by import By

# Add task directory to sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from main import (
    build_chrome_driver,
    open_post_composer,
    stage_post_text,
    confirm_and_publish,
    is_facebook_login_page,
)


class TestFacebookSelenium(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.script_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        cls.local_html_path = os.path.join(cls.script_dir, "data", "mock_facebook_feed.html")
        cls.local_url = f"file://{cls.local_html_path}"
        cls.driver = build_chrome_driver(headless=True)

    @classmethod
    def tearDownClass(cls):
        if cls.driver:
            try:
                cls.driver.quit()
            except Exception:
                pass

    def setUp(self):
        # Reload the mock fixture before each test to reset DOM state
        self.driver.get(self.local_url)

    def test_driver_initialization(self):
        """Verify WebDriver initializes with title from local fixture."""
        self.assertIn("Facebook", self.driver.title)

    def test_open_post_composer(self):
        """Verify opening post composer modal."""
        opened = open_post_composer(self.driver, is_local=True)
        self.assertTrue(opened)
        overlay = self.driver.find_element(By.ID, "dialog-overlay")
        self.assertEqual(overlay.value_of_css_property("display"), "flex")

    def test_stage_post_text(self):
        """Verify post text staging into contenteditable element."""
        open_post_composer(self.driver, is_local=True)
        test_msg = "Automated test message for Selenium workflow."
        staged = stage_post_text(self.driver, post_text=test_msg, is_local=True)
        self.assertEqual(staged, test_msg)

    def test_empty_post_validation(self):
        """Verify empty or whitespace post message raises ValueError."""
        with self.assertRaises(ValueError):
            stage_post_text(self.driver, post_text="   ", is_local=True)

        with self.assertRaises(ValueError):
            stage_post_text(self.driver, post_text="", is_local=True)

    def test_dry_run_mode_does_not_publish(self):
        """Verify dry-run mode stages the post but does not click publish."""
        open_post_composer(self.driver, is_local=True)
        stage_post_text(self.driver, "Dry run verification post", is_local=True)

        success = confirm_and_publish(
            self.driver,
            post_text="Dry run verification post",
            dry_run=True,
            is_local=True,
        )
        self.assertTrue(success)

        # Confirm status box did not receive published status
        status_box = self.driver.find_element(By.ID, "post-status")
        self.assertNotIn("Post published successfully", status_box.text)

    def test_auto_confirm_publishes_locally(self):
        """Verify auto-confirm clicks publish and achieves success status in mock feed."""
        open_post_composer(self.driver, is_local=True)
        test_text = "Publish confirmed test message"
        stage_post_text(self.driver, test_text, is_local=True)

        success = confirm_and_publish(
            self.driver,
            post_text=test_text,
            dry_run=False,
            auto_confirm=True,
            is_local=True,
        )
        self.assertTrue(success)

        status_box = self.driver.find_element(By.ID, "post-status")
        self.assertIn("Post published successfully", status_box.text)
        self.assertIn(test_text, status_box.text)

    @patch("builtins.input", return_value="no")
    def test_user_decline_cancels_publishing(self, mock_input):
        """Verify typing 'no' at safety gate cancels publishing and closes modal."""
        open_post_composer(self.driver, is_local=True)
        stage_post_text(self.driver, "Cancelled post message", is_local=True)

        success = confirm_and_publish(
            self.driver,
            post_text="Cancelled post message",
            dry_run=False,
            auto_confirm=False,
            is_local=True,
        )
        self.assertFalse(success)

        status_box = self.driver.find_element(By.ID, "post-status")
        self.assertIn("Post cancelled by user", status_box.text)

    def test_login_page_detection(self):
        """Verify login detection returns False for feed and True for login form."""
        # On feed page
        self.assertFalse(is_facebook_login_page(self.driver))

        # Inject mock email login input
        self.driver.execute_script("document.body.innerHTML += '<input id=\"email\" type=\"text\">';")
        self.assertTrue(is_facebook_login_page(self.driver))


if __name__ == "__main__":
    unittest.main()
