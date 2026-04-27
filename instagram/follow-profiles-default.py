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
CSV_FILE = "instagram-profiles/itsaryan_jay.csv"

DAILY_FOLLOW_LIMIT = 250
BREAK_AFTER = 50
MIN_BREAK_TIME = 33
MAX_BREAK_TIME = 100
MIN_WAIT_BETWEEN = 10
MAX_WAIT_BETWEEN = 30
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
            ('follow_status', ''), ('skip_reason', '')
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

            time.sleep(random.uniform(1.5, 3))

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