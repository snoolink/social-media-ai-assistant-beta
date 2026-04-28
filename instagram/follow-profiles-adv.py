# the follower count is working but the following count is not being read properly. I have added multiple xpaths to try to capture the following count, but it seems Instagram's HTML structure may have changed. I will need to inspect the page and update the xpaths accordingly. In the meantime, I will add a fallback method to try to parse the following count from any visible text on the page that contains "following". This should help capture the count even if the specific elements have changed.

import time
import pandas as pd
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium_stealth import stealth
from webdriver_manager.chrome import ChromeDriverManager
import random
from datetime import datetime

# ======== CONFIGURATION ========
CSV_FILE = "/Users/jay/Downloads/ig_commenters_2026-04-27.csv"

DAILY_FOLLOW_LIMIT = 250
BREAK_AFTER = 50
MIN_BREAK_TIME = 33
MAX_BREAK_TIME = 100
MIN_WAIT_BETWEEN = 10
MAX_WAIT_BETWEEN = 30

MIN_FOLLOWERS = 100
MIN_FOLLOWING = 100
# ===============================

def setup_driver():
    chrome_options = Options()
    chrome_options.add_argument("--start-maximized")
    chrome_options.add_argument("--disable-blink-features=AutomationControlled")
    chrome_options.add_argument("--disable-infobars")
    chrome_options.add_argument("--disable-notifications")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation", "enable-logging"])
    chrome_options.add_experimental_option('useAutomationExtension', False)
    chrome_options.add_experimental_option("prefs", {
        "profile.default_content_setting_values.notifications": 2,
        "credentials_enable_service": False,
        "profile.password_manager_enabled": False,
    })
    chrome_options.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36')

    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)

    driver.execute_cdp_cmd('Network.setUserAgentOverride', {
        "userAgent": 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36'
    })
    driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
    driver.execute_cdp_cmd('Page.addScriptToEvaluateOnNewDocument', {
        'source': '''
            Object.defineProperty(navigator, 'webdriver', { get: () => undefined });
            Object.defineProperty(navigator, 'languages', { get: () => ['en-US', 'en'] });
            window.chrome = { runtime: {} };
        '''
    })

    stealth(driver, languages=["en-US", "en"], vendor="Google Inc.", platform="Win32",
            webgl_vendor="Intel Inc.", renderer="Intel Iris OpenGL Engine", fix_hairline=True)

    return driver


def login_instagram(driver):
    driver.get("https://www.instagram.com/")
    print("=" * 60)
    print("🔐 MANUAL LOGIN REQUIRED")
    print("Please log in to Instagram in the browser window.")
    print("Press ENTER here once you're on the home page.")
    print("=" * 60)
    input("\n⏸️  Press ENTER after logging in... ")
    print("✅ Proceeding...")
    time.sleep(2)


def extract_username_from_url(url):
    return url.rstrip('/').split('/')[-1]


def parse_count(text):
    try:
        text = text.strip().replace(',', '')
        if 'K' in text.upper():
            return int(float(text.upper().replace('K', '')) * 1000)
        elif 'M' in text.upper():
            return int(float(text.upper().replace('M', '')) * 1_000_000)
        return int(float(text))
    except:
        return None


def scrape_stats(driver, username):
    """
    Returns (follower_count, following_count).
    Handles both public profiles (href-based links) and
    private profiles (span/title-based elements from the HTML).
    Both may be None if scraping fails.
    """
    follower_count = None
    following_count = None

    # ── FOLLOWERS ────────────────────────────────────────────────────────
    follower_xpaths = [
        # Public profile — anchor with /followers/ href
        "//a[contains(@href, '/followers/')]//span[@title]",
        "//a[contains(@href, '/followers/')]//span[contains(text(), ',') or contains(text(), 'K') or contains(text(), 'M')]",
        "//a[contains(@href, '/followers/')]//span[contains(@class, 'x5n08af')]",

        # Private profile — span with title attribute sitting inside
        # the "followers" link-span (title holds the exact numeric value)
        "//a[contains(@role,'link')]//span[@title and string-length(@title) > 0][following-sibling::text()[contains(.,'followers')] or ../following-sibling::*[contains(.,'followers')]]",

        # Private profile — span whose title is a number and whose
        # nearest text sibling says "followers"
        "//span[contains(@class,'x5n08af')][@title][following::text()[normalize-space()='followers'][1]]",

        # Fallback: any span with a numeric title near the word "followers"
        "//span[@title][following-sibling::text()[contains(., 'followers')] or parent::span[contains(., 'followers')]]",
    ]

    for xpath in follower_xpaths:
        try:
            for el in driver.find_elements(By.XPATH, xpath):
                text = el.get_attribute('title') or el.text.strip()
                count = parse_count(text)
                if count is not None:
                    follower_count = count
                    break
        except:
            continue
        if follower_count is not None:
            break

    # ── FOLLOWING ────────────────────────────────────────────────────────
    following_xpaths = [
        # Public profile — anchor with /following/ href
        "//a[contains(@href, '/following/')]//span[@title]",
        "//a[contains(@href, '/following/')]//span[contains(text(), ',') or contains(text(), 'K') or contains(text(), 'M')]",
        "//a[contains(@href, '/following/')]//span[contains(@class, 'x5n08af')]",

        # Private profile — the "following" block uses a plain inner span
        # (no title attr); grab the inner html-span inside the link-span
        "//a[contains(@role,'link')]//span[contains(@class,'x5n08af')]//span[contains(@class,'xdj266r')][following::text()[contains(.,'following')][1]]",

        # Fallback: span that contains a number right before " following" text
        "//span[contains(@class,'x5n08af')]//span[contains(@class,'xdj266r')][following-sibling::text()[normalize-space()='following'] or ../../following-sibling::*[contains(.,'following')]]",
    ]

    for xpath in following_xpaths:
        try:
            for el in driver.find_elements(By.XPATH, xpath):
                text = el.get_attribute('title') or el.text.strip()
                count = parse_count(text)
                if count is not None:
                    following_count = count
                    break
        except:
            continue
        if following_count is not None:
            break

    # ── FINAL FALLBACK: parse all stat blocks in one pass ─────────────
    # Instagram renders stats as: "<number> posts / followers / following"
    # Walk every span that contains one of those keywords and grab the
    # adjacent number span.
    if follower_count is None or following_count is None:
        try:
            stat_blocks = driver.find_elements(
                By.XPATH,
                "//span[contains(.,'followers') or contains(.,'following')]"
                "[not(contains(.,'follow back'))]"
            )
            for block in stat_blocks:
                text = block.text.strip().lower()
                if 'followers' in text and follower_count is None:
                    # Try to extract just the number part
                    number_part = text.replace('followers', '').strip()
                    count = parse_count(number_part)
                    if count is not None:
                        follower_count = count
                if 'following' in text and following_count is None:
                    number_part = text.replace('following', '').strip()
                    count = parse_count(number_part)
                    if count is not None:
                        following_count = count
        except:
            pass

    # ── LOGGING ──────────────────────────────────────────────────────────
    if follower_count is not None:
        print(f"👥 Followers: {follower_count:,}")
    else:
        print(f"⚠️  Could not read follower count for {username}")

    if following_count is not None:
        print(f"➡️  Following: {following_count:,}")
    else:
        print(f"⚠️  Could not read following count for {username}")

    return follower_count, following_count


def wait_for_profile_load(driver, timeout=1.5):
    """
    Wait up to `timeout` seconds for a key profile element to appear.
    If the page doesn't load in time, silently move on.
    """
    try:
        WebDriverWait(driver, timeout).until(
            EC.presence_of_element_located((
                By.XPATH,
                "//span[contains(.,'followers')] | //a[contains(@href,'/followers/')]"
            ))
        )
    except:
        pass  # Timed out — continue anyway


def follow_profile(driver, username, wait_time=10):
    wait = WebDriverWait(driver, wait_time)

    already_following_xpaths = [
        "//button//div[text()='Following']",
        "//button//div[text()='Requested']",
    ]
    for xpath in already_following_xpaths:
        try:
            el = driver.find_element(By.XPATH, xpath)
            if el and el.is_displayed():
                print(f"✓ Already following {username}")
                return False, "already_following"
        except:
            continue

    follow_xpaths = [
        "//button//div[text()='Follow']",
        "//div[text()='Follow']/ancestor::button",
        "//button[@type='button']//div[text()='Follow']",
    ]

    for xpath in follow_xpaths:
        try:
            btn = driver.find_element(By.XPATH, xpath)
            if btn and btn.is_displayed():
                driver.execute_script("arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});", btn)
                time.sleep(random.uniform(0.5, 1.2))
                try:
                    btn.click()
                except:
                    driver.execute_script("arguments[0].click();", btn)
                print(f"✅ Followed {username}")
                time.sleep(random.uniform(1.5, 3))
                return True, "success"
        except:
            continue

    print(f"⚠️  Could not find Follow button for {username}")
    return False, "no_follow_button"


def take_break():
    t = random.uniform(MIN_BREAK_TIME, MAX_BREAK_TIME)
    print(f"☕ Taking a {t/60:.1f} min break...")
    time.sleep(t)
    print("✅ Resuming...")


def main():
    try:
        df = pd.read_csv(CSV_FILE)
        df.columns = df.columns.str.strip()

        if 'url' not in df.columns:
            raise ValueError("CSV must have a 'url' column.")

        if 'userName' not in df.columns:
            df['userName'] = df['url'].apply(extract_username_from_url)

        for col, default in [
            ('followed', False), ('follow_date', ''),
            ('follow_status', ''), ('follower_count', None),
            ('following_count', None), ('skip_reason', '')
        ]:
            if col not in df.columns:
                df[col] = default

        to_follow = df[df['followed'] == False].copy()

        print(f"📋 Total profiles: {len(df)}")
        print(f"✅ Already followed: {len(df[df['followed'] == True])}")
        print(f"⏳ To follow: {len(to_follow)}")

        if len(to_follow) > DAILY_FOLLOW_LIMIT:
            print(f"⚠️  Capping at {DAILY_FOLLOW_LIMIT} follows for today")
            to_follow = to_follow.head(DAILY_FOLLOW_LIMIT)

    except Exception as e:
        print(f"❌ Error reading CSV: {e}")
        return

    driver = setup_driver()
    follow_count = 0
    skip_count = 0

    try:
        login_instagram(driver)

        for idx, row in to_follow.iterrows():
            url = row['url']
            username = row['userName']

            if follow_count > 0 or skip_count > 0:
                wait = random.uniform(MIN_WAIT_BETWEEN, MAX_WAIT_BETWEEN)
                print(f"⏳ Waiting {wait:.1f}s...")
                time.sleep(wait)

            print(f"\n📍 Visiting: {url}")
            try:
                driver.get(url)
            except Exception as e:
                print(f"❌ Navigation error: {e}")
                df.loc[idx, 'follow_status'] = 'navigation_error'
                df.to_csv(CSV_FILE, index=False)
                continue

            # ── Wait up to 1.5s for profile stats to appear, then continue ──
            # wait_for_profile_load(driver, timeout=1.5)
            time.sleep(15)


            # ── Scrape & validate follower/following counts ──────────────────
            follower_count, following_count = scrape_stats(driver, username)

            df.loc[idx, 'follower_count'] = follower_count
            df.loc[idx, 'following_count'] = following_count

            if follower_count is None or following_count is None:
                print(f"⚠️  Skipping {username} — couldn't read stats")
                df.loc[idx, 'follow_status'] = 'skipped'
                df.loc[idx, 'skip_reason'] = 'stats_unknown'
                df.to_csv(CSV_FILE, index=False)
                skip_count += 1
                continue

            if follower_count < MIN_FOLLOWERS:
                print(f"⏭️  Skipping {username} — only {follower_count:,} followers (need ≥{MIN_FOLLOWERS})")
                df.loc[idx, 'follow_status'] = 'skipped'
                df.loc[idx, 'skip_reason'] = 'too_few_followers'
                df.to_csv(CSV_FILE, index=False)
                skip_count += 1
                continue

            if following_count < MIN_FOLLOWING:
                print(f"⏭️  Skipping {username} — only {following_count:,} following (need ≥{MIN_FOLLOWING})")
                df.loc[idx, 'follow_status'] = 'skipped'
                df.loc[idx, 'skip_reason'] = 'too_few_following'
                df.to_csv(CSV_FILE, index=False)
                skip_count += 1
                continue
            # ─────────────────────────────────────────────────────────────────

            success, reason = follow_profile(driver, username)

            df.loc[idx, 'followed'] = success
            df.loc[idx, 'follow_status'] = reason
            df.loc[idx, 'skip_reason'] = '' if success else reason
            if success:
                df.loc[idx, 'follow_date'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                follow_count += 1
            else:
                skip_count += 1

            df.to_csv(CSV_FILE, index=False)
            print(f"📝 Progress: {follow_count} followed, {skip_count} skipped")

            if follow_count > 0 and follow_count % BREAK_AFTER == 0:
                take_break()

            if follow_count >= DAILY_FOLLOW_LIMIT:
                print(f"🛑 Daily follow limit of {DAILY_FOLLOW_LIMIT} reached")
                break

    except KeyboardInterrupt:
        print("\n⚠️  Interrupted by user")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
    finally:
        driver.quit()
        print(f"\n🏁 Done. Followed: {follow_count} | Skipped: {skip_count}")
        print(f"📊 CSV saved to '{CSV_FILE}'")


if __name__ == "__main__":
    main()