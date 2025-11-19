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
from datetime import datetime
from creds import INSTAGRAM_USERNAME, INSTAGRAM_PASSWORD

# ======== CONFIGURATION ========
CSV_FILE = "profiles-data/unfollow_list.csv"  # Must contain column 'url'
DAILY_LIMIT = 75  # Maximum unfollows per day
BREAK_AFTER = 13  # Take a break after this many unfollows
MIN_BREAK_TIME = 60  # Minimum break time in seconds (1 minute)
MAX_BREAK_TIME = 2700  # Maximum break time in seconds (45 minutes)
MIN_WAIT_BETWEEN_PROFILES = 0  # Minimum wait between profiles
MAX_WAIT_BETWEEN_PROFILES = 30  # Maximum wait between profiles
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
    
    # Additional stealth options
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    chrome_options.add_experimental_option('useAutomationExtension', False)
    chrome_options.add_argument("--disable-blink-features=AutomationControlled")
    
    # Set a realistic user agent
    chrome_options.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')

    driver = webdriver.Chrome(
        service=Service(ChromeDriverManager().install()),
        options=chrome_options
    )

    # Remove webdriver property
    driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")

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
    
    # Random wait to simulate human behavior
    time.sleep(random.uniform(3, 7))
    
    wait.until(EC.presence_of_element_located((By.NAME, "username")))

    user_input = driver.find_element(By.NAME, "username")
    pass_input = driver.find_element(By.NAME, "password")

    # Type with human-like delays
    for char in INSTAGRAM_USERNAME:
        user_input.send_keys(char)
        time.sleep(random.uniform(0.1, 0.3))
    
    time.sleep(random.uniform(0.5, 1.5))
    
    for char in INSTAGRAM_PASSWORD:
        pass_input.send_keys(char)
        time.sleep(random.uniform(0.1, 0.3))
    
    time.sleep(random.uniform(0.5, 1))
    pass_input.send_keys(Keys.RETURN)

    # Wait for login to complete
    time.sleep(random.uniform(8, 12))
    print("✅ Logged in successfully.")


def unfollow_user(driver, profile_url, wait_time=15):
    """
    Visit profile_url, click the Following button, wait for the confirmation modal/overlay,
    then click the final Unfollow button.
    """
    wait = WebDriverWait(driver, wait_time)
    try:
        driver.get(profile_url)
    except Exception as e:
        print(f"Navigation error to {profile_url}: {e}")
        return False

    # Human-like wait - random between MIN and MAX
    wait_time = random.uniform(MIN_WAIT_BETWEEN_PROFILES, MAX_WAIT_BETWEEN_PROFILES)
    print(f"⏳ Waiting {wait_time:.1f} seconds before action...")
    time.sleep(wait_time)

    try:
        # Find the "Following" button
        following_xpath = (
            "//button[.//div[normalize-space(text())='Following']"
            " or .//div[normalize-space(text())='Requested']"
            " or .//div[normalize-space(text())='Follow back']]"
        )

        following_btn = wait.until(EC.element_to_be_clickable((By.XPATH, following_xpath)))
        driver.execute_script("arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});", following_btn)
        time.sleep(random.uniform(0.8, 1.5))

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

        # Wait for modal animation
        time.sleep(random.uniform(1.2, 2.0))

        # Find and click the Unfollow confirmation button
        confirm_xpath_candidates = [
            "//span[normalize-space(text())='Unfollow']/ancestor::button[1]",
            "//button[.//span[normalize-space(text())='Unfollow']]",
            "//button[.//div[normalize-space(text())='Unfollow']]",
            "//button[.//div[text()='Unfollow']]"
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
            # Last resort
            try:
                candidate = driver.find_element(By.XPATH, "//*[normalize-space(text())='Unfollow']")
                driver.execute_script("arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});", candidate)
                time.sleep(0.4)
                try:
                    candidate.click()
                    print(f"✅ Successfully unfollowed: {profile_url}")
                    time.sleep(random.uniform(2, 3))
                    return True
                except Exception:
                    driver.execute_script("arguments[0].click();", candidate)
                    print(f"✅ Successfully unfollowed: {profile_url}")
                    time.sleep(random.uniform(2, 3))
                    return True
            except Exception:
                print("Could not locate the Unfollow button/span after clicking Following.")
                time.sleep(random.uniform(2, 3))
                return False

        # Click the confirmation button
        try:
            confirm_btn.click()
            print(f"✅ Successfully unfollowed: {profile_url}")
        except Exception:
            try:
                driver.execute_script("arguments[0].click();", confirm_btn)
                print(f"✅ Successfully unfollowed: {profile_url}")
            except Exception as e:
                print("Failed to click the Unfollow confirmation button:", e)
                time.sleep(random.uniform(2, 3))
                return False

        time.sleep(random.uniform(2, 4))
        return True

    except Exception as e:
        print(f"Exception in unfollow_user for {profile_url}: {e}")
        time.sleep(random.uniform(2, 3))
        return False


def take_random_break():
    """Take a random break between actions"""
    break_time = random.uniform(MIN_BREAK_TIME, MAX_BREAK_TIME)
    minutes = break_time / 60
    print(f"☕ Taking a break for {minutes:.1f} minutes...")
    time.sleep(break_time)
    print("✅ Break completed, resuming...")


def main():
    # Read URLs from CSV
    try:
        df = pd.read_csv(CSV_FILE)
        df.columns = df.columns.str.strip()
        print("📁 CSV columns detected:", df.columns.tolist())

        # Add 'unfollowed' column if it doesn't exist
        if 'unfollowed' not in df.columns:
            df['unfollowed'] = False
        
        # Add 'unfollow_date' column if it doesn't exist
        if 'unfollow_date' not in df.columns:
            df['unfollow_date'] = ''

        if "url" not in df.columns:
            raise ValueError("CSV must contain a column named 'url'.")

        # Filter only profiles that haven't been unfollowed yet
        profiles_to_unfollow = df[df['unfollowed'] == False].copy()
        
        print(f"🔗 Total profiles in CSV: {len(df)}")
        print(f"✅ Already unfollowed: {len(df[df['unfollowed'] == True])}")
        print(f"⏳ Remaining to unfollow: {len(profiles_to_unfollow)}")
        
        # Apply daily limit
        if len(profiles_to_unfollow) > DAILY_LIMIT:
            print(f"⚠️  Limiting to {DAILY_LIMIT} unfollows for today")
            profiles_to_unfollow = profiles_to_unfollow.head(DAILY_LIMIT)
        
    except Exception as e:
        print(f"❌ Error reading CSV: {e}")
        return

    driver = setup_driver()
    unfollow_count = 0
    
    try:
        login_instagram(driver)
        
        for idx, row in profiles_to_unfollow.iterrows():
            url = row['url']
            
            # Attempt to unfollow
            success = unfollow_user(driver, url)
            
            if success:
                unfollow_count += 1
                # Update the dataframe
                df.loc[idx, 'unfollowed'] = True
                df.loc[idx, 'unfollow_date'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                
                # Save progress after each successful unfollow
                df.to_csv(CSV_FILE, index=False)
                print(f"📝 Progress saved ({unfollow_count}/{len(profiles_to_unfollow)})")
                
                # Take a break after BREAK_AFTER unfollows
                if unfollow_count % BREAK_AFTER == 0 and unfollow_count < len(profiles_to_unfollow):
                    take_random_break()
            
            # Stop if we've reached the daily limit
            if unfollow_count >= DAILY_LIMIT:
                print(f"🛑 Reached daily limit of {DAILY_LIMIT} unfollows")
                break
                
    except KeyboardInterrupt:
        print("\n⚠️  Script interrupted by user")
    except Exception as e:
        print(f"❌ Error during execution: {e}")
    finally:
        driver.quit()
        print(f"🏁 Finished. Total unfollowed: {unfollow_count}")
        print(f"📊 CSV updated with progress in '{CSV_FILE}'")

if __name__ == "__main__":
    main()