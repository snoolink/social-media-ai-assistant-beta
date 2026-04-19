"""
Instagram Comment Username Scraper
====================================
Extracts all usernames who have commented on a public Instagram post or reel.

Requirements:
    pip install selenium webdriver-manager

Usage:
    python instagram_comment_scraper.py
    python instagram_comment_scraper.py --url https://www.instagram.com/p/XXXXX/
    python instagram_comment_scraper.py --url https://www.instagram.com/reel/XXXXX/ --output usernames.txt
"""

import argparse
import time
import re
import sys
from pathlib import Path

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import (
    TimeoutException,
    NoSuchElementException,
    StaleElementReferenceException,
)
from webdriver_manager.chrome import ChromeDriverManager


# ── Selectors based on observed Instagram HTML structure ─────────────────────
#
# Comment items live in <li class="_a9zj _a9zl ...">
# Inside each comment, the username anchor sits in an <h2> (post author)
# or <h3> (commenter) tag, inside a <div class="_a9zr">.
# The anchor href is always "/username/" (no subdirectory).
#
COMMENT_USERNAME_SELECTORS = [
    # Primary: username link inside the comment body block
    "li._a9zj._a9zl div._a9zr h3 a[href]",
    # Fallback: any anchor inside the comment name block
    "li._a9zj div._a9zr span a[href]",
    # Broader fallback: all anchors inside comment list items
    "li._a9zj a[role='link'][href]",
]

# Post author selector (h2, not h3) — used to exclude the OP from the list
POST_AUTHOR_SELECTOR = "li._a9zj._a9zl div._a9zr h2 a[href]"

# "Load more comments" button — the + icon circle button at the bottom of comments
LOAD_MORE_SELECTORS = [
    # SVG aria-label on the circular + button
    "svg[aria-label='Load more comments']",
    # Its parent button
    "button._abl-",
    # Generic fallbacks
    "button[aria-label*='Load more']",
    "button[aria-label*='more comments']",
]

# "View replies (N)" toggle buttons
VIEW_REPLIES_SELECTOR = "button._aswp._aswq._asw_._asx2"


def build_driver(headless: bool = False) -> webdriver.Chrome:
    """Build and return a configured Chrome WebDriver."""
    options = Options()
    if headless:
        options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option("useAutomationExtension", False)
    options.add_argument(
        "--user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
    )

    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options)
    driver.execute_cdp_cmd(
        "Page.addScriptToEvaluateOnNewDocument",
        {"source": "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"},
    )
    return driver


def is_instagram_url(url: str) -> bool:
    return bool(re.match(r"https?://(www\.)?instagram\.com/(p|reel)/[\w-]+/?", url))


def expand_replies(driver: webdriver.Chrome) -> int:
    """
    Click all visible 'View replies (N)' buttons.
    Returns the number of buttons clicked.
    """
    clicked = 0
    try:
        buttons = driver.find_elements(By.CSS_SELECTOR, VIEW_REPLIES_SELECTOR)
        for btn in buttons:
            try:
                driver.execute_script("arguments[0].click();", btn)
                clicked += 1
                time.sleep(0.4)
            except Exception:
                pass
    except Exception:
        pass
    return clicked


def click_load_more(driver: webdriver.Chrome) -> bool:
    """
    Click the 'Load more comments' circular + button if present.
    Returns True if a button was found and clicked.
    """
    for sel in LOAD_MORE_SELECTORS:
        try:
            buttons = driver.find_elements(By.CSS_SELECTOR, sel)
            for btn in buttons:
                try:
                    # Walk up to the nearest clickable parent if it's an SVG
                    el = btn
                    tag = el.tag_name.lower()
                    if tag in ("svg", "circle", "line"):
                        el = driver.execute_script(
                            "return arguments[0].closest('button');", btn
                        )
                    if el:
                        driver.execute_script("arguments[0].click();", el)
                        time.sleep(1.0)
                        return True
                except Exception:
                    continue
        except Exception:
            continue
    return False


def scroll_comments(driver: webdriver.Chrome, pause: float = 2.0, max_scrolls: int = 50) -> None:
    """
    Scroll through the page to trigger lazy-loading, click 'Load more comments',
    and expand all reply threads.
    """
    print("  Scrolling and expanding comments…")
    prev_count = 0

    for i in range(max_scrolls):
        # 1. Expand any 'View replies' toggles that are now visible
        replied = expand_replies(driver)

        # 2. Click the 'Load more comments' button (circular + at bottom)
        click_load_more(driver)

        # 3. Scroll down the page
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(pause)

        # 4. Also scroll any inner overflow containers (comment UL)
        try:
            for container in driver.find_elements(By.CSS_SELECTOR, "ul._a9zm, ul._a9ym, ul._a9yo"):
                driver.execute_script(
                    "arguments[0].scrollTop = arguments[0].scrollHeight;", container
                )
        except Exception:
            pass

        # 5. Count loaded comment items to detect when nothing new is loading
        try:
            current_count = len(driver.find_elements(By.CSS_SELECTOR, "li._a9zj._a9zl"))
        except Exception:
            current_count = 0

        sys.stdout.write(
            f"\r  Scroll pass {i + 1}/{max_scrolls} | "
            f"comments visible: {current_count} | replies expanded: {replied}   "
        )
        sys.stdout.flush()

        # Early-exit if no new comments loaded for 3 consecutive passes
        if current_count == prev_count and i > 2:
            print(f"\n  No new comments after pass {i + 1} — stopping early.")
            break
        prev_count = current_count

    print()


def extract_usernames(driver: webdriver.Chrome, exclude_author: bool = True) -> set[str]:
    """
    Collect unique commenter usernames from the loaded DOM.

    Instagram comment structure (from observed HTML):
        <li class="_a9zj _a9zl ...">
          <div class="_a9zm">
            ...
            <div class="_a9zr">
              <h3 ...><div>...<a href="/username/">username</a></div></h3>
              <span ...>comment text</span>
            </div>
          </div>
        </li>

    The post author appears in an <h2> inside a similar structure.
    """
    # Paths to skip (Instagram internal routes)
    SKIP_SLUGS = {
        "explore", "reels", "stories", "accounts", "p", "reel",
        "tv", "direct", "login", "legal", "privacy", "about",
        "help", "press", "api", "oauth",
    }

    usernames: set[str] = set()
    author_username: str | None = None

    # Optionally grab the post author to exclude them
    if exclude_author:
        try:
            author_el = driver.find_element(By.CSS_SELECTOR, POST_AUTHOR_SELECTOR)
            href = author_el.get_attribute("href") or ""
            m = re.match(r"https?://(?:www\.)?instagram\.com/([^/?#]+)/?", href)
            if m:
                author_username = m.group(1)
                print(f"  Post author detected: @{author_username} (will be excluded)")
        except NoSuchElementException:
            pass

    # Extract all commenter anchors
    for selector in COMMENT_USERNAME_SELECTORS:
        try:
            elements = driver.find_elements(By.CSS_SELECTOR, selector)
            for el in elements:
                try:
                    href = el.get_attribute("href") or ""
                    m = re.match(
                        r"https?://(?:www\.)?instagram\.com/([^/?#]+)/?", href
                    )
                    if not m:
                        continue
                    username = m.group(1)
                    if username in SKIP_SLUGS:
                        continue
                    if username == author_username:
                        continue
                    usernames.add(username)
                except StaleElementReferenceException:
                    continue
        except Exception:
            continue

    return usernames


def scrape_comments(url: str, scroll_passes: int = 30) -> list[str]:
    """
    Main scraping routine. Opens the Instagram login page, waits for the user
    to log in manually, then navigates to the post and scrapes comments.

    Args:
        url:           Public Instagram post or reel URL.
        scroll_passes: Number of scroll iterations to load more comments.

    Returns:
        Sorted list of unique commenter usernames.
    """
    if not is_instagram_url(url):
        raise ValueError(f"Not a recognised Instagram post/reel URL: {url}")

    print(f"\n[+] Target: {url}")
    print("[+] Launching browser for manual login…")

    driver = build_driver(headless=False)

    try:
        # ── Open login page and wait for the user ────────────────────────────
        driver.get("https://www.instagram.com/accounts/login/")
        print("\n" + "=" * 55)
        print("  Log in to Instagram in the browser window that")
        print("  just opened. Once fully logged in, come back here")
        print("  and press ENTER to start scraping.")
        print("=" * 55)
        input("\n  >>> Press ENTER when logged in: ")

        # ── Navigate to the target post ──────────────────────────────────────
        print("\n[+] Navigating to post…")
        driver.get(url)

        try:
            # Wait for the comment list to appear
            WebDriverWait(driver, 20).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "li._a9zj, article, main"))
            )
        except TimeoutException:
            print("[!] Timed out waiting for post — Instagram may be rate-limiting.")

        time.sleep(3)

        # Dismiss pop-ups (notifications, cookie banners, etc.)
        for dismiss_text in ["Not Now", "Not now", "Allow", "Accept"]:
            try:
                btn = WebDriverWait(driver, 3).until(
                    EC.element_to_be_clickable(
                        (By.XPATH, f"//button[normalize-space(text())='{dismiss_text}']")
                    )
                )
                btn.click()
                time.sleep(1)
            except TimeoutException:
                pass

        # ── Scroll & expand comments ─────────────────────────────────────────
        scroll_comments(driver, pause=2.0, max_scrolls=scroll_passes)

        # Final pass: expand any remaining reply threads
        remaining = expand_replies(driver)
        if remaining:
            print(f"  Expanded {remaining} more reply thread(s) on final pass.")
            time.sleep(2)

        # ── Extract usernames ────────────────────────────────────────────────
        print("[+] Extracting usernames…")
        return sorted(extract_usernames(driver, exclude_author=True))

    finally:
        driver.quit()
        print("[+] Browser closed.")


def save_usernames(usernames: list[str], path: str) -> None:
    out = Path(path)
    out.write_text("\n".join(usernames), encoding="utf-8")
    print(f"[+] Saved {len(usernames)} usernames → {out.resolve()}")


# ── CLI ──────────────────────────────────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Extract comment usernames from a public Instagram post or reel."
    )
    parser.add_argument(
        "--url", "-u",
        help="Instagram post or reel URL",
    )
    parser.add_argument(
        "--output", "-o",
        default="",
        help="Output file path (e.g. usernames.txt). Prints to stdout if omitted.",
    )
    parser.add_argument(
        "--scrolls",
        type=int,
        default=10,
        help="Number of scroll passes to load more comments (default: 10).",
    )
    args = parser.parse_args()

    url = args.url
    if not url:
        url = input("Enter Instagram post/reel URL: ").strip()

    try:
        usernames = scrape_comments(
            url=url,
            scroll_passes=args.scrolls,
        )
    except ValueError as e:
        print(f"[!] Error: {e}")
        sys.exit(1)

    if not usernames:
        print("\n[!] No usernames found.")
        print("    Possible reasons:")
        print("     • Login failed or session expired.")
        print("     • The post is private or age-restricted.")
        print("     • Instagram rate-limited the request — wait and retry.")
        print("     • HTML structure changed — update the selectors at the top of this file.")
        sys.exit(0)

    print(f"\n[✓] Found {len(usernames)} unique commenter(s):\n")
    for u in usernames:
        print(f"    @{u}")

    if args.output:
        save_usernames(usernames, args.output)


if __name__ == "__main__":
    main()