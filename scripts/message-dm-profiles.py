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
CSV_FILE = "profiles-data/dm_list.csv"  # Must contain columns 'url' and optionally 'userName'
MESSAGE_TEMPLATE = """Hi {name}! 👋

I came across your profile and loved your content. Would love to connect!"""

DAILY_DM_LIMIT = 50  # Maximum DMs per day to avoid spam detection
BREAK_AFTER = 10  # Take a break after this many DMs
MIN_BREAK_TIME = 120  # Minimum break time in seconds (2 minutes)
MAX_BREAK_TIME = 1800  # Maximum break time in seconds (30 minutes)
MIN_WAIT_BETWEEN_DMS = 15  # Minimum wait between DMs (seconds)
MAX_WAIT_BETWEEN_DMS = 45  # Maximum wait between DMs (seconds)
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


def send_dm(driver, profile_url, username, message, wait_time=15):
    """
    Visit profile, scrape first name, click Message button, and send DM
    """
    wait = WebDriverWait(driver, wait_time)
    
    try:
        driver.get(profile_url)
        print(f"📍 Visiting: {profile_url}")
    except Exception as e:
        print(f"❌ Navigation error to {profile_url}: {e}")
        return False, None

    # Human-like wait
    wait_time_human = random.uniform(3, 6)
    time.sleep(wait_time_human)

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
            return False
        
        # Scroll to button and click
        driver.execute_script("arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});", message_btn)
        time.sleep(random.uniform(0.8, 1.5))
        
        try:
            message_btn.click()
        except:
            driver.execute_script("arguments[0].click();", message_btn)
        
        print(f"💬 Opened message window for {username}")
        time.sleep(random.uniform(2, 4))
        
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
            return False
        
        # Click on the input to focus
        message_input.click()
        time.sleep(random.uniform(0.5, 1))
        
        # Clear any existing text
        message_input.clear()
        time.sleep(0.3)
        
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
        
        time.sleep(random.uniform(1, 2))
        
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
            return False
        
        try:
            send_btn.click()
        except:
            driver.execute_script("arguments[0].click();", send_btn)
        
        print(f"✅ Successfully sent DM to {username}")
        time.sleep(random.uniform(2, 4))
        return True, first_name
        
    except Exception as e:
        print(f"❌ Exception sending DM to {username}: {e}")
        time.sleep(random.uniform(2, 3))
        return False, first_name


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

        if "url" not in df.columns:
            raise ValueError("CSV must contain a column named 'url'.")
        
        # If userName column doesn't exist, extract from URL
        if 'userName' not in df.columns:
            df['userName'] = df['url'].apply(extract_username_from_url)

        # Filter only profiles that haven't received DM yet
        profiles_to_dm = df[df['dm_sent'] == False].copy()
        
        print(f"🔗 Total profiles in CSV: {len(df)}")
        print(f"✅ Already messaged: {len(df[df['dm_sent'] == True])}")
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
    
    try:
        login_instagram(driver)
        
        for idx, row in profiles_to_dm.iterrows():
            url = row['url']
            username = row['userName']
            
            # Wait between DMs (human-like behavior)
            if dm_count > 0:
                wait_time = random.uniform(MIN_WAIT_BETWEEN_DMS, MAX_WAIT_BETWEEN_DMS)
                print(f"⏳ Waiting {wait_time:.1f} seconds before next DM...")
                time.sleep(wait_time)
            
            # Attempt to send DM (message will be personalized inside send_dm function)
            success, scraped_name = send_dm(driver, url, username, MESSAGE_TEMPLATE)
            
            if success:
                dm_count += 1
                # Update the dataframe
                df.loc[idx, 'dm_sent'] = True
                df.loc[idx, 'dm_date'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                df.loc[idx, 'dm_status'] = 'success'
                df.loc[idx, 'first_name'] = scraped_name if scraped_name else username
            else:
                df.loc[idx, 'dm_status'] = 'failed'
                df.loc[idx, 'first_name'] = scraped_name if scraped_name else ''
            
            # Save progress after each attempt
            df.to_csv(CSV_FILE, index=False)
            print(f"📝 Progress saved ({dm_count}/{len(profiles_to_dm)} successful)")
            
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
        print(f"📊 CSV updated with progress in '{CSV_FILE}'")

if __name__ == "__main__":
    main()