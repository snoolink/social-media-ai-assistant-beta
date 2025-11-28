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
CSV_FILE = "profiles-data/suggested_profiles_2025-11-26_02-20-20.csv"  # Must contain columns 'url' and optionally 'userName'
MESSAGE_TEMPLATE = """Hi {name}!

Firstly what a great profile! I am Jay and am building a content creation  platform --> @snoolink. I genuinely loved your content and the vibe you bring… felt super aligned with what we are building.

I am currently working with a exclusive group of creators, and I would love to make a FREE custom reel for you— no commitments, just something cool we can create together.

Have a look at what we are building and share your thoughts! Just let me know, happy to get things rolling!"""

MAX_FOLLOWERS = 35000  # Only message profiles with followers below this threshold
MIN_FOLLOWERS = 1500  # Only message profiles with followers below this threshold

DAILY_DM_LIMIT = 150  # Maximum DMs per day to avoid spam detection
BREAK_AFTER = 10  # Take a break after this many DMs
MIN_BREAK_TIME = 12  # Minimum break time in seconds (2 minutes)
MAX_BREAK_TIME = 44  # Maximum break time in seconds (30 minutes)
MIN_WAIT_BETWEEN_DMS = 1  # Minimum wait between DMs (seconds)
MAX_WAIT_BETWEEN_DMS = 3  # Maximum wait between DMs (seconds)
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
    
    # Handle "Save Your Login Info" popup if it appears
    try:
        not_now = WebDriverWait(driver, 5).until(
            EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'Not now') or contains(text(), 'Not Now')]"))
        )
        not_now.click()
        time.sleep(2)
    except:
        pass
    
    # Handle notification popup if it appears
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
    # Handle URLs like https://www.instagram.com/username/ or https://instagram.com/username
    parts = url.rstrip('/').split('/')
    if len(parts) > 0:
        return parts[-1]
    return "there"  # fallback


def parse_follower_count(follower_text):
    """
    Parse follower count text and return as integer
    Handles formats like: "1,205", "1.2K", "35.5K", "1.5M"
    """
    try:
        # Remove commas and whitespace
        follower_text = follower_text.strip().replace(',', '')
        
        # Handle K (thousands)
        if 'K' in follower_text.upper():
            number = float(follower_text.upper().replace('K', ''))
            return int(number * 1000)
        
        # Handle M (millions)
        elif 'M' in follower_text.upper():
            number = float(follower_text.upper().replace('M', ''))
            return int(number * 1000000)
        
        # Handle regular numbers
        else:
            return int(float(follower_text))
    
    except Exception as e:
        print(f"⚠️  Error parsing follower count '{follower_text}': {e}")
        return None


def scrape_follower_count(driver, username, wait_time=10):
    """
    Scrape the follower count from the Instagram profile page
    Returns the follower count as an integer, or None if not found
    """
    wait = WebDriverWait(driver, wait_time)
    
    try:
        # Multiple XPath patterns to find follower count
        follower_xpaths = [
            # Pattern 1: Look for link to followers page with span containing count
            "//a[contains(@href, '/followers/')]//span[@class='x5n08af x1s688f']",
            "//a[contains(@href, '/followers/')]//span[contains(@class, 'x5n08af')]",
            
            # Pattern 2: Look for the specific structure from your HTML
            "//a[contains(@href, '/followers/')]//span[@class='html-span xdj266r x14z9mp xat24cr x1lziwak xexx8yu xyri2b x18d9i69 x1c1uobl x1hl2dhg x16tdsg8 x1vvkbs']",
            
            # Pattern 3: More general pattern
            "//a[contains(@href, '/followers/')]//span[contains(text(), ',') or contains(text(), 'K') or contains(text(), 'M')]",
            
            # Pattern 4: Look for span with title attribute containing numbers
            "//a[contains(@href, '/followers/')]//span[@title]"
        ]
        
        follower_count = None
        follower_text = None
        
        for xpath in follower_xpaths:
            try:
                elements = driver.find_elements(By.XPATH, xpath)
                
                for element in elements:
                    # Try to get text from title attribute first (more accurate)
                    title = element.get_attribute('title')
                    if title and (title.replace(',', '').replace('.', '').isdigit() or 'K' in title.upper() or 'M' in title.upper()):
                        follower_text = title
                        break
                    
                    # Otherwise get the text content
                    text = element.text.strip()
                    if text and (text.replace(',', '').replace('.', '').isdigit() or 'K' in text.upper() or 'M' in text.upper()):
                        follower_text = text
                        break
                
                if follower_text:
                    break
                    
            except:
                continue
        
        if follower_text:
            follower_count = parse_follower_count(follower_text)
            if follower_count is not None:
                print(f"👥 Found follower count: {follower_count:,} ({follower_text})")
                return follower_count
        
        print(f"⚠️  Could not find follower count for {username}")
        return None
        
    except Exception as e:
        print(f"⚠️  Error scraping follower count for {username}: {e}")
        return None


def scrape_first_name(driver, wait_time=10):
    """
    Scrape the first name from the Instagram profile page
    Returns the first word of the name, or username as fallback
    """
    wait = WebDriverWait(driver, wait_time)
    
    try:
        # Specific selector based on the HTML structure you provided
        name_xpaths = [
            "//span[contains(@class, 'x1lliihq x1plvlek xryxfnj x1n2onr6') and @dir='auto']",
            "//div[contains(@class, 'xdj266r')]//span[contains(@class, 'x1lliihq') and @dir='auto']",
            "//header//span[contains(@class, 'x1lliihq') and @dir='auto']",
            "//span[@dir='auto' and contains(@class, 'x1lliihq')]"
        ]
        
        for xpath in name_xpaths:
            try:
                name_element = driver.find_element(By.XPATH, xpath)
                full_name = name_element.text.strip()
                
                # Check if it's actually a name (not empty, not just username)
                if full_name and len(full_name) > 0 and not full_name.startswith('@'):
                    print(f"👤 Found full name: {full_name}")
                    
                    # Extract first name (first word)
                    first_name = full_name.split()[0]
                    
                    # Remove emojis, special characters, and fancy unicode characters
                    # Keep only basic alphanumeric characters
                    cleaned_name = ''
                    for char in first_name:
                        # Keep only ASCII letters (A-Z, a-z)
                        if char.isalpha() and ord(char) < 128:
                            cleaned_name += char
                    
                    if cleaned_name:
                        print(f"✨ Using first name: {cleaned_name}")
                        return cleaned_name
                    else:
                        # If name has only special characters, try second word
                        words = full_name.split()
                        for word in words:
                            cleaned = ''.join(c for c in word if c.isalpha() and ord(c) < 128)
                            if cleaned:
                                print(f"✨ Using first name: {cleaned}")
                                return cleaned
            except:
                continue
        
        print(f"⚠️  Could not find profile name, will use username")
        return None
        
    except Exception as e:
        print(f"⚠️  Error scraping name: {e}")
        return None


def check_and_follow_if_needed(driver, username, wait_time=10):
    """
    Check if the profile is already followed. If not, follow them.
    Returns True if followed (or already following), False if failed
    """
    wait = WebDriverWait(driver, wait_time)
    
    try:
        # Look for Follow button - if it exists, we're not following them yet
        follow_button_xpaths = [
            "//button//div[text()='Follow']",
            "//button[contains(text(), 'Follow') and not(contains(text(), 'Following'))]",
            "//div[text()='Follow']/ancestor::button",
            "//button[@type='button']//div[text()='Follow']"
        ]
        
        follow_btn = None
        for xpath in follow_button_xpaths:
            try:
                follow_btn = driver.find_element(By.XPATH, xpath)
                if follow_btn and follow_btn.is_displayed():
                    break
            except:
                continue
        
        if follow_btn:
            print(f"🔍 Not following {username} yet - clicking Follow button...")
            
            # Scroll to button and click
            driver.execute_script("arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});", follow_btn)
            time.sleep(random.uniform(0.8, 1.5))
            
            try:
                follow_btn.click()
            except:
                driver.execute_script("arguments[0].click();", follow_btn)
            
            print(f"✅ Successfully followed {username}")
            
            # Wait a bit after following before proceeding to message
            time.sleep(random.uniform(2, 4))
            return True
        else:
            # Check if we're already following
            following_indicators = [
                "//button//div[text()='Following']",
                "//button//div[text()='Requested']",
                "//button//div[text()='Message']"  # If Message button exists, we're likely following
            ]
            
            for xpath in following_indicators:
                try:
                    indicator = driver.find_element(By.XPATH, xpath)
                    if indicator:
                        print(f"✓ Already following {username}")
                        return True
                except:
                    continue
            
            print(f"⚠️  Could not determine follow status for {username}")
            return True  # Proceed anyway
            
    except Exception as e:
        print(f"⚠️  Error checking follow status for {username}: {e}")
        return True  # Proceed anyway


def send_dm(driver, profile_url, username, message, max_followers,min_followers, wait_time=15):
    """
    Visit profile, check follower count, follow if needed, scrape first name, and send DM
    Returns tuple: (success, scraped_name, follower_count, skipped_reason)
    """
    wait = WebDriverWait(driver, wait_time)
    
    try:
        driver.get(profile_url)
        print(f"📍 Visiting: {profile_url}")
    except Exception as e:
        print(f"❌ Navigation error to {profile_url}: {e}")
        return False, None, None, "navigation_error"

    # Human-like wait
    wait_time_human = random.uniform(1, 3)
    time.sleep(wait_time_human)

    # First, scrape the follower count
    follower_count = scrape_follower_count(driver, username)
    
    # Check if follower count exceeds the limit
    if follower_count is not None and follower_count > max_followers or follower_count is not None and follower_count < min_followers:
        print(f"⏭️  SKIPPING {username}: {follower_count:,} followers (exceeds limit)")
        return False, None, follower_count, "exceeds_follower_limit"
    
    if follower_count is None:
        print(f"⚠️  Could not determine follower count for {username}, skipping to be safe")
        return False, None, None, "follower_count_unknown"
    
    print(f"✅ {username} has {follower_count:,} followers (below {max_followers:,} limit) - proceeding...")

    # Check if we need to follow them first
    follow_success = check_and_follow_if_needed(driver, username)
    
    if not follow_success:
        print(f"⚠️  Could not follow {username}, but will try to message anyway")
    
    # Small wait after follow check
    time.sleep(random.uniform(1, 2))

    # Scrape the first name from profile
    first_name = scrape_first_name(driver)
    if not first_name:
        # Fallback to username
        first_name = username
    
    # Personalize message with scraped name
    personalized_message = message.format(name=first_name)

    try:
        # Look for "Message" button - try multiple XPath patterns
        message_button_xpaths = [
            "//div[text()='Message']",
            "//button[contains(text(), 'Message')]",
            "//div[contains(@class, 'x1i10hfl') and text()='Message']",
            "//*[text()='Message' and (self::div or self::button)]"
        ]
        
        message_btn = None
        for xpath in message_button_xpaths:
            try:
                message_btn = wait.until(EC.element_to_be_clickable((By.XPATH, xpath)))
                if message_btn:
                    break
            except:
                continue
        
        if not message_btn:
            print(f"⚠️  Could not find Message button for {username}")
            return False, first_name, follower_count, "no_message_button"
        
        # Scroll to button and click
        driver.execute_script("arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});", message_btn)
        time.sleep(random.uniform(0.8, 1.5))
        
        try:
            message_btn.click()
        except:
            driver.execute_script("arguments[0].click();", message_btn)
        
        print(f"💬 Opened message window for {username}")
        # time.sleep(random.uniform(1, 2))
        
        # Find the message input textarea
        message_input_xpaths = [
            "//textarea[@placeholder='Message...']",
            "//textarea[@aria-label='Message']",
            "//div[@role='textbox']",
            "//textarea[contains(@placeholder, 'Message')]"
        ]
        
        message_input = None
        for xpath in message_input_xpaths:
            try:
                message_input = wait.until(EC.presence_of_element_located((By.XPATH, xpath)))
                if message_input:
                    break
            except:
                continue
        
        if not message_input:
            print(f"⚠️  Could not find message input box for {username}")
            return False, first_name, follower_count, "no_input_box"
        
        # Click on the input to focus
        message_input.click()
        time.sleep(random.uniform(0.2, 0.8))
        
        # Clear any existing text
        message_input.clear()
        time.sleep(0.2)
        
        # Type message with human-like delays, encoding to ASCII to avoid BMP errors
        # Remove emojis and non-ASCII characters that might cause issues
        safe_message = personalized_message.encode('ascii', 'ignore').decode('ascii')
        
        for char in safe_message:
            message_input.send_keys(char)
            # Vary typing speed - faster for regular chars, slower for punctuation
            if char in ['.', '!', '?', '\n']:
                time.sleep(random.uniform(0.3, 0.6))
            else:
                time.sleep(random.uniform(0.05, 0.15))
        
        # time.sleep(random.uniform(1, 2))
        
        # Find and click Send button using the specific structure from your HTML
        send_button_xpaths = [
            "//div[@aria-label='Send' and @role='button']",
            "//div[@aria-label='Send']",
            "//svg[@aria-label='Send']/ancestor::div[@role='button']",
            "//button[text()='Send']",
            "//div[text()='Send']",
            "//button[contains(text(), 'Send')]",
            "//*[text()='Send' and (self::div or self::button)]"
        ]
        
        send_btn = None
        for xpath in send_button_xpaths:
            try:
                send_btn = wait.until(EC.element_to_be_clickable((By.XPATH, xpath)))
                if send_btn:
                    break
            except:
                continue
        
        if not send_btn:
            print(f"⚠️  Could not find Send button for {username}")
            return False, first_name, follower_count, "no_send_button"
        
        try:
            send_btn.click()
        except:
            driver.execute_script("arguments[0].click();", send_btn)
        
        print(f"✅ Successfully sent DM to {username}")
        time.sleep(random.uniform(2, 4))
        return True, first_name, follower_count, "success"
        
    except Exception as e:
        print(f"❌ Exception sending DM to {username}: {e}")
        time.sleep(random.uniform(2, 3))
        return False, first_name, follower_count, f"error: {str(e)}"


def take_random_break():
    """Take a random break between actions"""
    break_time = random.uniform(MIN_BREAK_TIME, MAX_BREAK_TIME)
    minutes = break_time / 60
    print(f"☕ Taking a break for {minutes:.1f} minutes...")
    time.sleep(break_time)
    print("✅ Break completed, resuming...")


def main():
    # Read profiles from CSV
    try:
        df = pd.read_csv(CSV_FILE)
        df.columns = df.columns.str.strip()
        print("📁 CSV columns detected:", df.columns.tolist())

        # Add tracking columns if they don't exist
        if 'dm_sent' not in df.columns:
            df['dm_sent'] = False
        
        if 'dm_date' not in df.columns:
            df['dm_date'] = ''
        
        if 'dm_status' not in df.columns:
            df['dm_status'] = ''
        
        if 'first_name' not in df.columns:
            df['first_name'] = ''
        
        if 'followed' not in df.columns:
            df['followed'] = False
        
        if 'follower_count' not in df.columns:
            df['follower_count'] = None
        
        if 'skip_reason' not in df.columns:
            df['skip_reason'] = ''

        if "url" not in df.columns:
            raise ValueError("CSV must contain a column named 'url'.")
        
        # If userName column doesn't exist, extract from URL
        if 'userName' not in df.columns:
            df['userName'] = df['url'].apply(extract_username_from_url)

        # Filter only profiles that haven't received DM yet
        profiles_to_dm = df[df['dm_sent'] == False].copy()
        
        print(f"🔗 Total profiles in CSV: {len(df)}")
        print(f"✅ Already messaged: {len(df[df['dm_sent'] == True])}")
        print(f"⏭️  Skipped (over {MAX_FOLLOWERS:,} followers): {len(df[df['skip_reason'] == 'exceeds_follower_limit'])}")
        print(f"⏳ Remaining to message: {len(profiles_to_dm)}")
        
        # Apply daily limit
        if len(profiles_to_dm) > DAILY_DM_LIMIT:
            print(f"⚠️  Limiting to {DAILY_DM_LIMIT} DMs for today")
            profiles_to_dm = profiles_to_dm.head(DAILY_DM_LIMIT)
        
    except Exception as e:
        print(f"❌ Error reading CSV: {e}")
        return

    driver = setup_driver()
    dm_count = 0
    skip_count = 0
    
    try:
        login_instagram(driver)
        
        for idx, row in profiles_to_dm.iterrows():
            url = row['url']
            username = row['userName']
            
            # Wait between attempts (human-like behavior)
            if dm_count > 0 or skip_count > 0:
                wait_time = random.uniform(MIN_WAIT_BETWEEN_DMS, MAX_WAIT_BETWEEN_DMS)
                print(f"⏳ Waiting {wait_time:.1f} seconds before next profile...")
                time.sleep(wait_time)
            
            # Attempt to send DM (includes follower count check)
            success, scraped_name, follower_count, skip_reason = send_dm(
                driver, url, username, MESSAGE_TEMPLATE, MAX_FOLLOWERS, MIN_FOLLOWERS
            )
            
            # Update the dataframe
            df.loc[idx, 'follower_count'] = follower_count
            
            if success:
                dm_count += 1
                df.loc[idx, 'dm_sent'] = True
                df.loc[idx, 'dm_date'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                df.loc[idx, 'dm_status'] = 'success'
                df.loc[idx, 'first_name'] = scraped_name if scraped_name else username
                df.loc[idx, 'followed'] = True
                df.loc[idx, 'skip_reason'] = ''
            else:
                if skip_reason == 'exceeds_follower_limit':
                    skip_count += 1
                    df.loc[idx, 'dm_sent'] = False  # Not sent, but checked
                    df.loc[idx, 'dm_status'] = 'skipped'
                    df.loc[idx, 'skip_reason'] = skip_reason
                else:
                    df.loc[idx, 'dm_status'] = 'failed'
                    df.loc[idx, 'skip_reason'] = skip_reason
                
                df.loc[idx, 'first_name'] = scraped_name if scraped_name else ''
            
            # Save progress after each attempt
            df.to_csv(CSV_FILE, index=False)
            print(f"📝 Progress saved ({dm_count} sent, {skip_count} skipped)")
            
            # Take a break after BREAK_AFTER DMs
            if dm_count > 0 and dm_count % BREAK_AFTER == 0 and dm_count < len(profiles_to_dm):
                take_random_break()
            
            # Stop if we've reached the daily limit
            if dm_count >= DAILY_DM_LIMIT:
                print(f"🛑 Reached daily limit of {DAILY_DM_LIMIT} DMs")
                break
                
    except KeyboardInterrupt:
        print("\n⚠️  Script interrupted by user")
    except Exception as e:
        print(f"❌ Error during execution: {e}")
    finally:
        driver.quit()
        print(f"🏁 Finished. Total DMs sent: {dm_count}")
        print(f"⏭️  Total profiles skipped (follower limit): {skip_count}")
        print(f"📊 CSV updated with progress in '{CSV_FILE}'")

if __name__ == "__main__":
    main()