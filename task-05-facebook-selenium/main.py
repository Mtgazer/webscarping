import argparse
import os
import sys
import time
from urllib.parse import urljoin
from dotenv import load_dotenv
from selenium import webdriver
from selenium.common.exceptions import (
    NoSuchElementException,
    TimeoutException,
    WebDriverException,
)
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

# Load optional .env file
load_dotenv()


def build_chrome_driver(
    user_data_dir: str | None = None,
    headless: bool = False,
    chrome_binary: str = "/usr/bin/google-chrome",
) -> WebDriver:
    """Initialize Google Chrome WebDriver with custom profile and anti-bot mitigation flags."""
    options = Options()

    if os.path.exists(chrome_binary):
        options.binary_location = chrome_binary

    options.add_argument("--disable-notifications")
    options.add_argument("--disable-popup-blocking")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--start-maximized")

    if user_data_dir:
        abs_profile = os.path.abspath(user_data_dir)
        os.makedirs(abs_profile, exist_ok=True)
        options.add_argument(f"--user-data-dir={abs_profile}")

    if headless:
        options.add_argument("--headless=new")
        options.add_argument("--window-size=1920,1080")

    return webdriver.Chrome(options=options)


def is_facebook_login_page(driver: WebDriver) -> bool:
    """Check if current page presents a Facebook login form."""
    login_indicators = [
        (By.ID, "email"),
        (By.NAME, "email"),
        (By.NAME, "login"),
        (By.XPATH, "//button[@name='login']"),
        (By.XPATH, "//input[@data-testid='royal_email']"),
    ]
    for by, selector in login_indicators:
        try:
            elem = driver.find_element(by, selector)
            if elem.is_displayed():
                return True
        except NoSuchElementException:
            continue
    return False


def wait_for_manual_login(driver: WebDriver, timeout_seconds: int = 300) -> bool:
    """Prompt the user in terminal to complete manual login in the visible browser."""
    print("\n" + "=" * 75)
    print("MANUAL FACEBOOK LOGIN REQUIRED")
    print("=" * 75)
    print("Security & Integrity Principle:")
    print("  - Passwords and 2FA tokens must NEVER be automated, stored, or committed.")
    print("  - Please log in manually in the opened Chrome browser window.")
    print("  - Your session will be preserved locally in your local profile directory.")
    print("=" * 75)

    try:
        input("Press ENTER in this terminal once you have successfully logged in to Facebook... ")
    except (EOFError, KeyboardInterrupt):
        print("\nLogin prompt cancelled by user.")
        return False

    return not is_facebook_login_page(driver)


def open_post_composer(driver: WebDriver, timeout: int = 15, is_local: bool = False) -> bool:
    """Find and click the 'What's on your mind?' trigger to open the post dialog."""
    wait = WebDriverWait(driver, timeout)

    if is_local:
        selectors = [
            (By.ID, "create-post-trigger"),
            (By.CSS_SELECTOR, "[aria-label='Create a post']"),
            (By.XPATH, "//*[@id='trigger-input-placeholder']"),
        ]
    else:
        selectors = [
            (By.XPATH, "//span[contains(text(), \"What's on your mind\")]"),
            (By.XPATH, "//div[@role='button']//span[contains(text(), \"What's on your mind\")]"),
            (By.CSS_SELECTOR, "div[role='button'][aria-label*=\"What's on your mind\"]"),
            (By.CSS_SELECTOR, "div[data-testid='status-attachment-mentions-input']"),
            (By.CSS_SELECTOR, "div[role='button'][aria-label='Create a post']"),
        ]

    for by, selector in selectors:
        try:
            trigger = wait.until(EC.element_to_be_clickable((by, selector)))
            trigger.click()
            time.sleep(1.0)
            return True
        except (TimeoutException, NoSuchElementException):
            continue

    return False


def stage_post_text(driver: WebDriver, post_text: str, timeout: int = 15, is_local: bool = False) -> str | None:
    """Locate the post contenteditable textbox, focus, and type post text."""
    if not post_text or not post_text.strip():
        raise ValueError("Post text cannot be empty or whitespace only.")

    wait = WebDriverWait(driver, timeout)

    if is_local:
        textbox_selectors = [
            (By.ID, "post-composer-textbox"),
            (By.CSS_SELECTOR, "[role='textbox'][contenteditable='true']"),
        ]
    else:
        textbox_selectors = [
            (By.CSS_SELECTOR, "div[role='dialog'] div[role='textbox'][contenteditable='true']"),
            (By.CSS_SELECTOR, "div[role='textbox'][aria-label*=\"What's on your mind\"]"),
            (By.CSS_SELECTOR, "div[role='textbox'][contenteditable='true']"),
            (By.XPATH, "//div[@role='dialog']//div[@contenteditable='true']"),
        ]

    textbox = None
    for by, selector in textbox_selectors:
        try:
            textbox = wait.until(EC.visibility_of_element_located((by, selector)))
            break
        except (TimeoutException, NoSuchElementException):
            continue

    if not textbox:
        return None

    # Focus and enter text
    textbox.click()
    time.sleep(0.5)

    # Use send_keys to simulate typing
    textbox.send_keys(post_text)
    time.sleep(1.0)

    # Retrieve staged text to verify
    staged_text = textbox.text.strip()
    if not staged_text:
        # Fallback query for innerText
        staged_text = driver.execute_script("return arguments[0].innerText || arguments[0].textContent;", textbox)
        if staged_text:
            staged_text = staged_text.strip()

    return staged_text


def confirm_and_publish(
    driver: WebDriver,
    post_text: str,
    dry_run: bool = True,
    interactive: bool = True,
    auto_confirm: bool = False,
    is_local: bool = False,
    timeout: int = 15,
) -> bool:
    """Safety confirmation gate before publishing the post."""
    print("\n" + "=" * 75)
    print("POST STAGING SAFETY GATE (CONFIRMATION REQUIRED)")
    print("=" * 75)
    print(f"Target Environment : {'Local HTML Fixture' if is_local else 'Live Facebook UI'}")
    print(f"Execution Mode     : {'DRY-RUN (Safe Simulation)' if dry_run else 'LIVE PUBLISH'}")
    print(f"Staged Post Text   :\n  \"{post_text}\"")
    print("=" * 75)

    if dry_run:
        print("\n[DRY-RUN MODE ACTIVE]")
        print("  - The post content has been staged and verified in the DOM.")
        print("  - The publish button was NOT clicked.")
        print("  - No post was published. Safe exit.")
        return True

    # User confirmation check
    if not auto_confirm:
        print("\nWARNING: You are about to publish a REAL post.")
        print("Please review the staged draft in the visible Chrome window.")
        try:
            confirm = input("Type 'yes' or 'CONFIRM' to publish this post (anything else to cancel): ").strip()
        except (EOFError, KeyboardInterrupt):
            confirm = "no"

        if confirm.lower() not in ["yes", "confirm", "y"]:
            print("\n[ABORTED BY USER] Publishing was cancelled. Discarding draft.")
            _discard_draft(driver, is_local=is_local)
            return False

    print("\n[CONFIRMED] Publishing post...")
    wait = WebDriverWait(driver, timeout)

    if is_local:
        publish_selectors = [
            (By.ID, "publish-post-button"),
            (By.CSS_SELECTOR, "button[aria-label='Post']"),
        ]
    else:
        publish_selectors = [
            (By.CSS_SELECTOR, "div[role='dialog'] div[role='button'][aria-label='Post']"),
            (By.XPATH, "//div[@role='dialog']//div[@role='button']//span[text()='Post']"),
            (By.XPATH, "//div[@role='dialog']//span[text()='Post']/ancestor::div[@role='button']"),
        ]

    for by, selector in publish_selectors:
        try:
            btn = wait.until(EC.element_to_be_clickable((by, selector)))
            btn.click()
            time.sleep(2.0)
            print("Post published successfully.")
            return True
        except (TimeoutException, NoSuchElementException):
            continue

    print("Error: Could not locate the publish button.")
    return False


def _discard_draft(driver: WebDriver, is_local: bool = False) -> None:
    """Discard post modal safely."""
    close_selectors = [
        (By.ID, "dialog-close-btn"),
        (By.CSS_SELECTOR, "[aria-label='Close']"),
        (By.XPATH, "//div[@role='dialog']//div[@aria-label='Close']"),
    ]
    for by, selector in close_selectors:
        try:
            btn = driver.find_element(by, selector)
            if btn.is_displayed():
                btn.click()
                time.sleep(0.5)
                return
        except NoSuchElementException:
            continue


def run_facebook_workflow(
    post_text: str,
    target_mode: str = "local",
    dry_run: bool = True,
    headless: bool = False,
    user_data_dir: str | None = None,
    auto_confirm: bool = False,
) -> bool:
    """Execute complete end-to-end Facebook Selenium workflow with safety checks."""
    script_dir = os.path.dirname(os.path.abspath(__file__))
    is_local = target_mode.lower() in ["local", "mock", "offline"]

    driver = None
    try:
        print("=" * 75)
        print("TASK 5 — FACEBOOK AUTOMATION USING SELENIUM")
        print("=" * 75)
        print(f"Target Mode       : {target_mode}")
        print(f"Dry Run           : {dry_run}")
        print(f"Headless          : {headless}")
        print(f"Profile Directory : {user_data_dir or 'Default (Temporary)'}")
        print("=" * 75 + "\n")

        print("Initializing Google Chrome with Selenium WebDriver...")
        driver = build_chrome_driver(user_data_dir=user_data_dir, headless=headless)

        if is_local:
            local_html_path = os.path.join(script_dir, "data", "mock_facebook_feed.html")
            target_url = f"file://{local_html_path}"
            print(f"Navigating to local mock Facebook feed:\n  {target_url}")
            driver.get(target_url)
        else:
            target_url = "https://www.facebook.com"
            print(f"Navigating to Facebook:\n  {target_url}")
            driver.get(target_url)

            # Check login status
            if is_facebook_login_page(driver):
                if headless or auto_confirm:
                    print("Error: Facebook login required, but running in non-interactive/headless mode.")
                    print("To log in, run the script visibly without --headless to authenticate once.")
                    return False

                logged_in = wait_for_manual_login(driver)
                if not logged_in:
                    print("Error: Could not verify Facebook login. Aborting safely.")
                    return False

        time.sleep(1.5)

        print("Opening post composer dialog...")
        opened = open_post_composer(driver, is_local=is_local)
        if not opened:
            print("Error: Could not open the post composer dialog. The layout or selectors may have changed.")
            return False

        print("Staging post text...")
        staged = stage_post_text(driver, post_text=post_text, is_local=is_local)
        if not staged:
            print("Error: Failed to enter text into the post editor.")
            return False

        print(f"Post text successfully staged in composer: \"{staged}\"")

        # Confirmation gate
        success = confirm_and_publish(
            driver,
            post_text=post_text,
            dry_run=dry_run,
            interactive=not auto_confirm,
            auto_confirm=auto_confirm,
            is_local=is_local,
        )

        return success

    except WebDriverException as e:
        print(f"WebDriver error: {e}", file=sys.stderr)
        return False
    finally:
        if driver:
            try:
                driver.quit()
            except Exception:
                pass


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Facebook Automation with Selenium (Task 5)")
    parser.add_argument(
        "--text",
        type=str,
        default=os.getenv("FB_POST_TEXT", "Hello from Python & Selenium automation!"),
        help="Text message to post",
    )
    parser.add_argument(
        "--mode",
        choices=["local", "facebook"],
        default=os.getenv("TARGET_MODE", "local"),
        help="Target environment: 'local' (offline mock fixture) or 'facebook' (live Facebook)",
    )
    parser.add_argument(
        "--profile-dir",
        type=str,
        default=os.getenv("CHROME_USER_DATA_DIR", "chrome_profile"),
        help="Persistent Chrome user profile directory",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        default=os.getenv("DRY_RUN", "true").lower() in ["true", "1", "yes"],
        help="Run without publishing (draft staging only)",
    )
    parser.add_argument(
        "--no-dry-run",
        action="store_false",
        dest="dry_run",
        help="Disable dry-run mode (requires explicit terminal confirmation to publish)",
    )
    parser.add_argument(
        "--headless",
        action="store_true",
        default=False,
        help="Run Chrome in headless mode",
    )
    parser.add_argument(
        "--auto-confirm",
        action="store_true",
        default=False,
        help="Auto-confirm publishing (intended for automated local testing)",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    success = run_facebook_workflow(
        post_text=args.text,
        target_mode=args.mode,
        dry_run=args.dry_run,
        headless=args.headless,
        user_data_dir=args.profile_dir if args.mode == "facebook" else None,
        auto_confirm=args.auto_confirm,
    )
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
