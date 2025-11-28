import time
import pandas as pd
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
from selenium_stealth import stealth
from webdriver_manager.chrome import ChromeDriverManager
import random
from datetime import datetime
from creds import INSTAGRAM_USERNAME, INSTAGRAM_PASSWORD

# ======== CONFIGURATION ========
CSV_FILE = "profiles-data/suggested_profiles_2025-11-25.csv"  # Must contain column 'url'
DAILY_STORY_LIKE_LIMIT = 200  # Maximum story likes per day
BREAK_AFTER = 15  # Take a break after this many likes
MIN_BREAK_TIME = 120  # Minimum break time in seconds (2 minutes)
MAX_BREAK_TIME = 300  # Maximum break time in seconds (5 minutes)
MIN_WAIT_BETWEEN_PROFILES = 2  # Minimum wait between profiles (seconds)
MAX_WAIT_BETWEEN_PROFILES = 5  # Maximum wait between profiles (seconds)
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
    
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    chrome_options.add_experimental_option('useAutomationExtension', False)
    chrome_options.add_argument("--disable-blink-features=AutomationControlled")
    
    chrome_options.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')

    driver = webdriver.Chrome(
        service=Service(ChromeDriverManager().install()),
        options=chrome_options
    )

    driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")

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
    
    time.sleep(random.uniform(3, 7))
    
    wait.until(EC.presence_of_element_located((By.NAME, "username")))

    user_input = driver.find_element(By.NAME, "username")
    pass_input = driver.find_element(By.NAME, "password")

    for char in INSTAGRAM_USERNAME:
        user_input.send_keys(char)
        time.sleep(random.uniform(0.1, 0.3))
    
    time.sleep(random.uniform(0.5, 1.5))
    
    for char in INSTAGRAM_PASSWORD:
        pass_input.send_keys(char)
        time.sleep(random.uniform(0.1, 0.3))
    
    time.sleep(random.uniform(0.5, 1))
    pass_input.send_keys(Keys.RETURN)

    time.sleep(random.uniform(8, 12))
    
    # Handle "Save Your Login Info" popup
    try:
        not_now = WebDriverWait(driver, 5).until(
            EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'Not now') or contains(text(), 'Not Now')]"))
        )
        not_now.click()
        time.sleep(2)
    except:
        pass
    
    # Handle notification popup
    try:
        not_now = WebDriverWait(driver, 5).until(
            EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'Not Now')]"))
        )
        not_now.click()
        time.sleep(2)
    except:
        pass
    
    print("✅ Logged in successfully.")


def extract_username_from_url(url):
    """Extract username from Instagram profile URL"""
    parts = url.rstrip('/').split('/')
    if len(parts) > 0:
        return parts[-1]
    return None


def is_public_account(driver, username, wait_time=10):
    """
    Check if the Instagram account is public or private
    Returns: True if public, False if private or unknown
    """
    try:
        # Look for "This Account is Private" message
        private_indicators = [
            "//h2[contains(text(), 'This account is private')]",
            "//h2[contains(text(), 'This Account is Private')]",
            "//*[contains(text(), 'This account is private')]",
            "//span[contains(text(), 'This account is private')]"
        ]
        
        for xpath in private_indicators:
            try:
                private_msg = driver.find_element(By.XPATH, xpath)
                if private_msg and private_msg.is_displayed():
                    print(f"🔒 {username} is a PRIVATE account - skipping")
                    return False
            except:
                continue
        
        # Check for Follow button (if we see follow without following, it's likely public)
        # Also check if we can see posts count (another indicator of public account)
        public_indicators = [
            "//article",  # Posts grid
            "//div[contains(@class, '_ac7v')]",  # Posts section
            "//span[contains(text(), 'posts')]",  # Posts count
        ]
        
        for xpath in public_indicators:
            try:
                element = driver.find_element(By.XPATH, xpath)
                if element:
                    print(f"🔓 {username} is a PUBLIC account")
                    return True
            except:
                continue
        
        # If we can't determine, assume it's private to be safe
        print(f"⚠️  Could not determine if {username} is public or private - treating as private")
        return False
        
    except Exception as e:
        print(f"⚠️  Error checking account privacy for {username}: {e}")
        return False


def check_and_like_story(driver, username, wait_time=10):
    """
    Check if profile has an active story and like it by clicking directly
    Returns: (success, status_message)
    """
    try:
        # Look for story ring/circle around profile picture
        story_indicators = [
            "//canvas[contains(@class, 'xh8yej3')]",
            "//canvas[@style]",
            "//img[contains(@alt, 'profile picture')]/ancestor::span[contains(@class, 'xh8yej3')]",
            "//header//img[contains(@alt, 'profile picture')]/ancestor::button",
            "//header//img[contains(@alt, 'profile picture')]/ancestor::a[contains(@href, '/stories/')]"
        ]
        
        story_element = None
        for xpath in story_indicators:
            try:
                elements = driver.find_elements(By.XPATH, xpath)
                if elements:
                    for elem in elements:
                        try:
                            parent = elem.find_element(By.XPATH, "./ancestor::*[1]")
                            if parent:
                                story_element = parent
                                break
                        except:
                            story_element = elem
                            break
                if story_element:
                    break
            except:
                continue
        
        # Alternative: Look for clickable profile picture in header
        if not story_element:
            try:
                profile_pic_xpaths = [
                    "//header//img[contains(@alt, 'profile picture')]",
                    "//header//button//img",
                ]
                
                for xpath in profile_pic_xpaths:
                    try:
                        pic = driver.find_element(By.XPATH, xpath)
                        if pic:
                            story_element = pic
                            break
                    except:
                        continue
            except:
                pass
        
        if not story_element:
            print(f"📭 No active story found for {username}")
            return False, "no_story"
        
        print(f"📖 Found story for {username} - opening...")
        
        # Click on the story element
        try:
            driver.execute_script("arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});", story_element)
            time.sleep(random.uniform(0.5, 1))
            
            try:
                story_element.click()
            except:
                driver.execute_script("arguments[0].click();", story_element)
            
            # Wait for story to load - simple fixed wait
            print(f"⏳ Waiting 3 seconds for story to load...")
            time.sleep(3)
            
        except Exception as e:
            print(f"⚠️  Could not click story element: {e}")
            return False, "click_failed"
        
        # DIRECT BUTTON CLICK - Find and click the like button by role
        print(f"❤️  Looking for like button...")
        
        try:
            # Multiple strategies to find the like button
            like_button = None
            
            # Strategy 1: Find by the SVG with aria-label="Like"
            try:
                svg = driver.find_element(By.XPATH, "//svg[@aria-label='Like']")
                # Get the clickable parent div with role="button"
                like_button = svg.find_element(By.XPATH, "./ancestor::div[@role='button']")
                print(f"✓ Found like button via SVG")
            except:
                pass
            
            # Strategy 2: Find div with role="button" that contains the like SVG
            if not like_button:
                try:
                    like_button = driver.find_element(By.XPATH, "//div[@role='button'][.//svg[@aria-label='Like']]")
                    print(f"✓ Found like button via role attribute")
                except:
                    pass
            
            # Strategy 3: CSS selector approach
            if not like_button:
                try:
                    like_button = driver.find_element(By.CSS_SELECTOR, "div[role='button'] svg[aria-label='Like']")
                    # Get parent button div
                    like_button = like_button.find_element(By.XPATH, "./ancestor::div[@role='button']")
                    print(f"✓ Found like button via CSS selector")
                except:
                    pass
            
            if not like_button:
                print(f"⚠️  Could not find like button")
                # Close story and return
                try:
                    driver.find_element(By.TAG_NAME, 'body').send_keys(Keys.ESCAPE)
                    time.sleep(0.5)
                except:
                    pass
                return False, "no_like_button"
            
            # Click the like button immediately
            print(f"👆 Clicking like button now...")
            try:
                like_button.click()
                print(f"✅ Like button clicked!")
            except:
                # Try JavaScript click if regular click fails
                driver.execute_script("arguments[0].click();", like_button)
                print(f"✅ Like button clicked (JS)!")
            
            time.sleep(random.uniform(0.5, 1))
            
        except Exception as e:
            print(f"⚠️  Error clicking like button: {e}")
            # Close story and return failure
            try:
                driver.find_element(By.TAG_NAME, 'body').send_keys(Keys.ESCAPE)
                time.sleep(0.5)
            except:
                pass
            return False, "like_click_failed"
        
        # Close the story viewer
        try:
            time.sleep(random.uniform(0.5, 1))
            driver.find_element(By.TAG_NAME, 'body').send_keys(Keys.ESCAPE)
            time.sleep(random.uniform(0.5, 1))
        except:
            try:
                close_btn = driver.find_element(By.XPATH, "//button[@aria-label='Close']")
                close_btn.click()
                time.sleep(0.5)
            except:
                pass
        
        return True, "success"
        
    except Exception as e:
        print(f"❌ Error processing story for {username}: {e}")
        try:
            driver.find_element(By.TAG_NAME, 'body').send_keys(Keys.ESCAPE)
            time.sleep(1)
        except:
            pass
        return False, f"error: {str(e)}"


def process_profile(driver, profile_url, username, wait_time=10):
    """
    Visit profile, check if public, check for story, and like it
    Returns: (success, status)
    """
    try:
        driver.get(profile_url)
        print(f"\n📍 Visiting: {profile_url}")
        time.sleep(random.uniform(2, 4))
        
    except Exception as e:
        print(f"❌ Navigation error to {profile_url}: {e}")
        return False, "navigation_error"
    
    # Check if account is public
    if not is_public_account(driver, username):
        return False, "private_account"
    
    # Small delay before checking story
    time.sleep(random.uniform(1, 2))
    
    # Check and like story
    success, status = check_and_like_story(driver, username)
    
    return success, status


def take_random_break():
    """Take a random break between actions"""
    break_time = random.uniform(MIN_BREAK_TIME, MAX_BREAK_TIME)
    minutes = break_time / 60
    print(f"\n☕ Taking a break for {minutes:.1f} minutes...")
    time.sleep(break_time)
    print("✅ Break completed, resuming...\n")


def main():
    # Read profiles from CSV
    try:
        df = pd.read_csv(CSV_FILE)
        df.columns = df.columns.str.strip()
        print("📁 CSV columns detected:", df.columns.tolist())

        # Add tracking columns if they don't exist
        if 'story_liked' not in df.columns:
            df['story_liked'] = False
        
        if 'story_like_date' not in df.columns:
            df['story_like_date'] = ''
        
        if 'story_status' not in df.columns:
            df['story_status'] = ''
        
        if 'is_public' not in df.columns:
            df['is_public'] = None

        if "url" not in df.columns:
            raise ValueError("CSV must contain a column named 'url'.")
        
        # If userName column doesn't exist, extract from URL
        if 'userName' not in df.columns:
            df['userName'] = df['url'].apply(extract_username_from_url)

        # Filter only profiles that haven't had story liked yet
        profiles_to_process = df[df['story_liked'] == False].copy()
        
        print(f"\n🔗 Total profiles in CSV: {len(df)}")
        print(f"✅ Already processed: {len(df[df['story_liked'] == True])}")
        print(f"⏳ Remaining to process: {len(profiles_to_process)}")
        
        # Apply daily limit
        if len(profiles_to_process) > DAILY_STORY_LIKE_LIMIT:
            print(f"⚠️  Limiting to {DAILY_STORY_LIKE_LIMIT} profiles for today")
            profiles_to_process = profiles_to_process.head(DAILY_STORY_LIKE_LIMIT)
        
    except Exception as e:
        print(f"❌ Error reading CSV: {e}")
        return

    driver = setup_driver()
    like_count = 0
    skip_count = 0
    
    try:
        login_instagram(driver)
        
        for idx, row in profiles_to_process.iterrows():
            url = row['url']
            username = row['userName']
            
            # Wait between profiles (human-like behavior)
            if like_count > 0 or skip_count > 0:
                wait_time = random.uniform(MIN_WAIT_BETWEEN_PROFILES, MAX_WAIT_BETWEEN_PROFILES)
                print(f"⏳ Waiting {wait_time:.1f} seconds before next profile...")
                time.sleep(wait_time)
            
            # Process profile
            success, status = process_profile(driver, url, username)
            
            # Update the dataframe
            if status == "private_account":
                df.loc[idx, 'is_public'] = False
                df.loc[idx, 'story_status'] = 'private_account'
                skip_count += 1
            elif status in ["no_story", "no_like_button"]:
                df.loc[idx, 'is_public'] = True
                df.loc[idx, 'story_status'] = status
                skip_count += 1
            elif success:
                like_count += 1
                df.loc[idx, 'story_liked'] = True
                df.loc[idx, 'story_like_date'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                df.loc[idx, 'story_status'] = status
                df.loc[idx, 'is_public'] = True
            else:
                df.loc[idx, 'story_status'] = status
                df.loc[idx, 'is_public'] = True
            
            # Save progress after each attempt
            df.to_csv(CSV_FILE, index=False)
            print(f"📝 Progress saved ({like_count} liked, {skip_count} skipped)")
            
            # Take a break after BREAK_AFTER likes
            if like_count > 0 and like_count % BREAK_AFTER == 0 and like_count < len(profiles_to_process):
                take_random_break()
            
            # Stop if we've reached the daily limit
            if like_count >= DAILY_STORY_LIKE_LIMIT:
                print(f"\n🛑 Reached daily limit of {DAILY_STORY_LIKE_LIMIT} story likes")
                break
                
    except KeyboardInterrupt:
        print("\n⚠️  Script interrupted by user")
    except Exception as e:
        print(f"❌ Error during execution: {e}")
    finally:
        driver.quit()
        print(f"\n🏁 Finished!")
        print(f"❤️  Total stories liked: {like_count}")
        print(f"⏭️  Total profiles skipped: {skip_count}")
        print(f"📊 CSV updated with progress in '{CSV_FILE}'")

if __name__ == "__main__":
    main()