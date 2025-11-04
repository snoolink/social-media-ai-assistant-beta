import time
import pandas as pd
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium_stealth import stealth
from webdriver_manager.chrome import ChromeDriverManager
import random
from creds import INSTAGRAM_USERNAME, INSTAGRAM_PASSWORD

# Now use these variables anywhere below
print("Logging in as:", INSTAGRAM_USERNAME)
# ======== CONFIGURATION ========
# INSTAGRAM_USERNAME = "snook@gmail.com"
# INSTAGRAM_PASSWORD = "Alink"
CSV_FILE = "profiles-data/unfollow_list.csv"  # Must contain column 'url'
DELAY_BETWEEN_ACTIONS = 5  # seconds
# ===============================


def setup_driver():
    chrome_options = Options()
    chrome_options.add_argument("--start-maximized")
    chrome_options.add_argument("--disable-blink-features=AutomationControlled")
    chrome_options.add_argument("--disable-infobars")
    chrome_options.add_argument("--disable-notifications")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-gpu")
    # Optional headless mode for background operation:
    # chrome_options.add_argument("--headless=new")

    driver = webdriver.Chrome(
        service=Service(ChromeDriverManager().install()),
        options=chrome_options
    )

    # --- Stealth mode setup ---
    stealth(
        driver,
        languages=["en-US", "en"],
        vendor="Google Inc.",
        platform="Win32",
        webgl_vendor="Intel Inc.",
        renderer="Intel Iris OpenGL Engine",
        fix_hairline=True,
    )

    return driver


def login_instagram(driver):
    driver.get("https://www.instagram.com/")
    wait = WebDriverWait(driver, 15)

    print("🔐 Logging into Instagram...")
    wait.until(EC.presence_of_element_located((By.NAME, "username")))

    user_input = driver.find_element(By.NAME, "username")
    pass_input = driver.find_element(By.NAME, "password")

    user_input.send_keys(INSTAGRAM_USERNAME)
    pass_input.send_keys(INSTAGRAM_PASSWORD)
    pass_input.send_keys(Keys.RETURN)

    # Wait for login to complete
    time.sleep(8)
    print("✅ Logged in successfully.")
def unfollow_user(driver, profile_url, wait_time=15):
    """
    Visit profile_url, click the Following button, wait for the confirmation modal/overlay,
    then click the final Unfollow button (targeting the span->ancestor::button).
    Sleeps 2.5 seconds before returning.
    """
    wait = WebDriverWait(driver, wait_time)
    try:
        driver.get(profile_url)
    except Exception as e:
        print(f"Navigation error to {profile_url}: {e}")
        return False

    # small human-like wait
    time.sleep(random.uniform(2.0, 4.0))

    try:
        # Find the "Following" (or related) button whose text is nested inside child div/span
        following_xpath = (
            "//button[.//div[normalize-space(text())='Following']"
            " or .//div[normalize-space(text())='Requested']"
            " or .//div[normalize-space(text())='Follow back']]"
        )

        following_btn = wait.until(EC.element_to_be_clickable((By.XPATH, following_xpath)))
        driver.execute_script("arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});", following_btn)
        time.sleep(random.uniform(0.6, 1.1))

        # Try normal click, fallback to JS click
        try:
            following_btn.click()
        except Exception:
            try:
                driver.execute_script("arguments[0].click();", following_btn)
            except Exception as e:
                print("Failed to click Following button:", e)
                return False

        print(f"Clicked 'Following' on {profile_url}")

        # small pause for overlay/modal animation
        time.sleep(random.uniform(0.8, 1.4))

        # Wait for the Unfollow option/span to appear — target the span text then get its ancestor button
        # This matches the HTML you pasted: <span>Unfollow</span> inside nested divs -> ancestor button
        confirm_xpath_candidates = [
            "//span[normalize-space(text())='Unfollow']/ancestor::button[1]",
            "//button[.//span[normalize-space(text())='Unfollow']]",
            "//button[.//div[normalize-space(text())='Unfollow']]",
            "//button[.//div[text()='Unfollow']]"  # fallback
        ]

        confirm_btn = None
        for xp in confirm_xpath_candidates:
            try:
                confirm_btn = WebDriverWait(driver, 8).until(EC.element_to_be_clickable((By.XPATH, xp)))
                if confirm_btn:
                    break
            except Exception:
                confirm_btn = None

        if not confirm_btn:
            # As a last resort, try to find a clickable element whose inner text contains 'Unfollow'
            try:
                candidate = driver.find_element(By.XPATH, "//*[normalize-space(text())='Unfollow']")
                driver.execute_script("arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});", candidate)
                time.sleep(0.4)
                try:
                    candidate.click()
                    print(f"Clicked Unfollow (direct element) for {profile_url}")
                    time.sleep(2.5)
                    return True
                except Exception:
                    driver.execute_script("arguments[0].click();", candidate)
                    print(f"JS-clicked Unfollow (direct element) for {profile_url}")
                    time.sleep(2.5)
                    return True
            except Exception:
                print("Could not locate the Unfollow button/span after clicking Following.")
                time.sleep(2.5)
                return False

        # Click the confirmation button (normal click with JS fallback)
        try:
            confirm_btn.click()
            print(f"✅ Successfully clicked Unfollow for {profile_url}")
        except Exception:
            try:
                driver.execute_script("arguments[0].click();", confirm_btn)
                print(f"✅ Successfully JS-clicked Unfollow for {profile_url}")
            except Exception as e:
                print("Failed to click the Unfollow confirmation button:", e)
                time.sleep(2.5)
                return False

        # final short pause before moving to next profile
        time.sleep(2.5)
        return True

    except Exception as e:
        print(f"Exception in unfollow_user for {profile_url}: {e}")
        # ensure small pause even on error
        time.sleep(2.5)
        return False

# def unfollow_user(driver, profile_url):
#     driver.get(profile_url)
#     wait = WebDriverWait(driver, 15)
#     time.sleep(4)

#     try:
#         # Look for "Following" or "Requested" button
#         unfollow_btn = wait.until(
#             EC.presence_of_element_located((
#                 By.XPATH,
#                 "//button[contains(text(), 'Following') or contains(text(), 'Requested')]"
#             ))
#         )
#         unfollow_btn.click()
#         print(f"⚙️ Clicked unfollow button on: {profile_url}")
#         time.sleep(2)

#         # Confirm unfollow in popup
#         confirm_btn = wait.until(
#             EC.presence_of_element_located((By.XPATH, "//button[contains(text(), 'Unfollow')]"))
#         )
#         confirm_btn.click()
#         print(f"✅ Successfully unfollowed: {profile_url}")

#     except Exception as e:
#         print(f"⚠️ Could not unfollow {profile_url}: {e}")

#     time.sleep(DELAY_BETWEEN_ACTIONS)


def main():
    # Read URLs from CSV
    try:
        df = pd.read_csv(CSV_FILE)
        df.columns = df.columns.str.strip().str.lower()
        print("📁 CSV columns detected:", df.columns.tolist())

        if "url" not in df.columns:
            raise ValueError("CSV must contain a column named 'url'.")

        profile_urls = df["url"].dropna().tolist()
        print(f"🔗 Found {len(profile_urls)} profiles to unfollow.")
    except Exception as e:
        print(f"❌ Error reading CSV: {e}")
        return

    driver = setup_driver()
    try:
        login_instagram(driver)
        for url in profile_urls:
            unfollow_user(driver, url)
    finally:
        driver.quit()
        print("🏁 Finished all unfollow actions.")


if __name__ == "__main__":
    main()
