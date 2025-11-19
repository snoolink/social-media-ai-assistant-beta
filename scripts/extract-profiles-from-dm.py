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
import re
from creds import INSTAGRAM_USERNAME, INSTAGRAM_PASSWORD

# ======== CONFIGURATION ========
TARGET_PROFILE = "jaydev_13"  # The profile whose DMs we want to check
OUTPUT_CSV = "extracted_profiles.csv"
MAX_PROFILES_TO_EXTRACT = 10
SCROLL_PAUSE_TIME = 2  # Time to wait after scrolling
MAX_SCROLLS = 50  # Maximum number of scrolls to prevent infinite loops
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


def navigate_to_profile_messages(driver, username):
    """Navigate to a specific user's profile and open their messages"""
    wait = WebDriverWait(driver, 15)
    
    profile_url = f"https://www.instagram.com/{username}/"
    print(f"📍 Navigating to profile: {profile_url}")
    
    driver.get(profile_url)
    time.sleep(random.uniform(3, 5))
    
    # Click on the Message button
    try:
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
        
        print(f"💬 Opened message thread with {username}")
        time.sleep(random.uniform(3, 5))
        return True
        
    except Exception as e:
        print(f"❌ Error opening messages: {e}")
        return False


def extract_profile_links_from_messages(driver, max_profiles=10):
    """
    Scroll through the message thread and extract Instagram profile links
    """
    wait = WebDriverWait(driver, 10)
    profile_links = set()  # Use set to avoid duplicates
    scroll_count = 0
    
    print(f"🔍 Starting to extract profile links (target: {max_profiles} profiles)...")
    
    try:
        # Find the message container - try multiple selectors
        message_container_selectors = [
            "//div[@role='dialog']//div[contains(@class, 'x78zum5')]",
            "//div[@role='dialog']",
            "//div[contains(@class, 'x9f619')]//div[contains(@class, 'x78zum5')]"
        ]
        
        message_container = None
        for selector in message_container_selectors:
            try:
                message_container = driver.find_element(By.XPATH, selector)
                if message_container:
                    break
            except:
                continue
        
        if not message_container:
            print("⚠️  Could not find message container")
            return list(profile_links)
        
        print("✅ Found message container, starting extraction...")
        
        # Scroll to load more messages and extract links
        last_height = 0
        no_new_content_count = 0
        
        while len(profile_links) < max_profiles and scroll_count < MAX_SCROLLS:
            # Get all links in the current view
            try:
                # Find all anchor tags with Instagram profile URLs
                links = driver.find_elements(By.XPATH, "//a[contains(@href, '/')]")
                
                for link in links:
                    try:
                        href = link.get_attribute('href')
                        if href and 'instagram.com' in href:
                            # Extract profile username from URL
                            # Match patterns like: instagram.com/username/ or instagram.com/username
                            match = re.search(r'instagram\.com/([a-zA-Z0-9._]+)/?', href)
                            if match:
                                username = match.group(1)
                                # Filter out non-profile paths
                                excluded_paths = ['p', 'reel', 'tv', 'stories', 'explore', 'direct', 
                                                'accounts', 'about', 'legal', 'privacy', 'safety']
                                if username not in excluded_paths and not username.startswith('_'):
                                    full_url = f"https://www.instagram.com/{username}/"
                                    if full_url not in profile_links:
                                        profile_links.add(full_url)
                                        print(f"✨ Found profile #{len(profile_links)}: {full_url}")
                                        
                                        if len(profile_links) >= max_profiles:
                                            print(f"🎯 Reached target of {max_profiles} profiles!")
                                            break
                    except Exception as e:
                        continue
                
                if len(profile_links) >= max_profiles:
                    break
                
                # Scroll up to load older messages
                driver.execute_script("arguments[0].scrollTo(0, 0);", message_container)
                time.sleep(SCROLL_PAUSE_TIME)
                
                # Check if we've loaded new content
                current_height = driver.execute_script("return arguments[0].scrollHeight", message_container)
                if current_height == last_height:
                    no_new_content_count += 1
                    if no_new_content_count >= 3:
                        print("⚠️  No new messages loading, stopping extraction")
                        break
                else:
                    no_new_content_count = 0
                    last_height = current_height
                
                scroll_count += 1
                print(f"📜 Scroll {scroll_count}/{MAX_SCROLLS} | Profiles found: {len(profile_links)}/{max_profiles}")
                
            except Exception as e:
                print(f"⚠️  Error during extraction: {e}")
                break
        
        print(f"✅ Extraction complete! Found {len(profile_links)} unique profile links")
        return list(profile_links)
        
    except Exception as e:
        print(f"❌ Error extracting profile links: {e}")
        return list(profile_links)


def save_to_csv(profile_links, output_file):
    """Save extracted profile links to CSV"""
    if not profile_links:
        print("⚠️  No profiles to save")
        return
    
    # Extract usernames from URLs
    data = []
    for url in profile_links:
        match = re.search(r'instagram\.com/([a-zA-Z0-9._]+)/?', url)
        username = match.group(1) if match else ""
        data.append({
            'url': url,
            'userName': username
        })
    
    df = pd.DataFrame(data)
    df.to_csv(output_file, index=False)
    print(f"💾 Saved {len(profile_links)} profiles to '{output_file}'")


def main():
    driver = setup_driver()
    
    try:
        # Step 1: Login to Instagram
        login_instagram(driver)
        
        # Step 2: Navigate to target profile and open messages
        if not navigate_to_profile_messages(driver, TARGET_PROFILE):
            print("❌ Failed to open message thread")
            return
        
        # Step 3: Extract profile links from messages
        profile_links = extract_profile_links_from_messages(driver, MAX_PROFILES_TO_EXTRACT)
        
        # Step 4: Save to CSV
        if profile_links:
            save_to_csv(profile_links, OUTPUT_CSV)
        else:
            print("❌ No profile links found in messages")
        
    except KeyboardInterrupt:
        print("\n⚠️  Script interrupted by user")
    except Exception as e:
        print(f"❌ Error during execution: {e}")
        import traceback
        traceback.print_exc()
    finally:
        print("🏁 Closing browser...")
        driver.quit()
        print("✅ Done!")


if __name__ == "__main__":
    main()