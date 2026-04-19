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
# Note: Manual login is used, so credentials are not needed from creds.py

# ======== CONFIGURATION ========
CSV_FILE = "instagram-profiles/snoolink-val-to-be-reached.csv"  # Must contain columns 'url' and optionally 'userName'
MESSAGE_TEMPLATE = """Hey Girl, We just found your page and your content is honestly is fire!! 

At Snoolink, we help creators turn their photos & clips into scroll-stopping reels.

This Valentine Week, we are doing a little “digital love” for couples or self lovers :P and making FREE reels for creators we vibe with.

If you are down, we are happy to get things rolling and surprise you with a custom reel. No sales, just good content.

Should I make one for you?"""  # Personalize with {name} placeholder
MAX_FOLLOWERS = 35000  # Only message profiles with followers below this threshold
MIN_FOLLOWERS = 1000  # Only message profiles with followers below this threshold

DAILY_DM_LIMIT = 250  # Maximum DMs per day to avoid spam detection
BREAK_AFTER = 55  # Take a break after this many DMs
MIN_BREAK_TIME = 1  # Minimum break time in seconds (2 minutes)
MAX_BREAK_TIME = 6  # Maximum break time in seconds (10 minutes)
MIN_WAIT_BETWEEN_DMS = 1  # Minimum wait between DMs (seconds)
MAX_WAIT_BETWEEN_DMS = 4  # Maximum wait between DMs (seconds)
# ===============================

def human_like_mouse_move(driver, element):
    """Simulate human-like mouse movement to an element"""
    try:
        from selenium.webdriver.common.action_chains import ActionChains
        actions = ActionChains(driver)
        
        # Add some randomness to the movement
        x_offset = random.randint(-5, 5)
        y_offset = random.randint(-5, 5)
        
        actions.move_to_element_with_offset(element, x_offset, y_offset)
        actions.pause(random.uniform(0.1, 0.3))
        actions.perform()
        time.sleep(random.uniform(0.1, 0.3))
    except:
        pass


def random_scroll(driver):
    """Perform random human-like scrolling"""
    try:
        # Random scroll amount
        scroll_amount = random.randint(100, 400)
        direction = random.choice([1, -1])  # Up or down
        
        driver.execute_script(f"window.scrollBy(0, {scroll_amount * direction});")
        time.sleep(random.uniform(0.3, 0.8))
    except:
        pass


def random_mouse_movement(driver):
    """Simulate random mouse movements to appear more human"""
    try:
        from selenium.webdriver.common.action_chains import ActionChains
        actions = ActionChains(driver)
        
        # Random mouse movements
        for _ in range(random.randint(1, 3)):
            x = random.randint(100, 500)
            y = random.randint(100, 500)
            actions.move_by_offset(x, y)
            actions.pause(random.uniform(0.1, 0.2))
        
        actions.perform()
        time.sleep(random.uniform(0.2, 0.5))
    except:
        pass


def setup_driver():
    chrome_options = Options()
    
    # Basic window and display options
    chrome_options.add_argument("--start-maximized")
    chrome_options.add_argument("--disable-blink-features=AutomationControlled")
    chrome_options.add_argument("--disable-infobars")
    chrome_options.add_argument("--disable-notifications")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    
    # Additional anti-detection arguments
    chrome_options.add_argument("--disable-blink-features=AutomationControlled")
    chrome_options.add_argument("--disable-features=IsolateOrigins,site-per-process")
    chrome_options.add_argument("--disable-site-isolation-trials")
    chrome_options.add_argument("--disable-web-security")
    chrome_options.add_argument("--disable-features=VizDisplayCompositor")
    chrome_options.add_argument("--disable-background-networking")
    chrome_options.add_argument("--disable-background-timer-throttling")
    chrome_options.add_argument("--disable-backgrounding-occluded-windows")
    chrome_options.add_argument("--disable-breakpad")
    chrome_options.add_argument("--disable-component-extensions-with-background-pages")
    chrome_options.add_argument("--disable-extensions")
    chrome_options.add_argument("--disable-features=TranslateUI,BlinkGenPropertyTrees")
    chrome_options.add_argument("--disable-ipc-flooding-protection")
    chrome_options.add_argument("--disable-renderer-backgrounding")
    chrome_options.add_argument("--enable-features=NetworkService,NetworkServiceInProcess")
    chrome_options.add_argument("--force-color-profile=srgb")
    chrome_options.add_argument("--hide-scrollbars")
    chrome_options.add_argument("--metrics-recording-only")
    chrome_options.add_argument("--mute-audio")
    
    # Exclude automation switches
    chrome_options.add_experimental_option("excludeSwitches", [
        "enable-automation",
        "enable-logging",
        "disable-popup-blocking"
    ])
    chrome_options.add_experimental_option('useAutomationExtension', False)
    
    # Set realistic preferences
    chrome_options.add_experimental_option("prefs", {
        "profile.default_content_setting_values.notifications": 2,
        "profile.managed_default_content_settings.images": 1,
        "profile.default_content_setting_values.media_stream_mic": 2,
        "profile.default_content_setting_values.media_stream_camera": 2,
        "profile.default_content_setting_values.geolocation": 2,
        "credentials_enable_service": False,
        "profile.password_manager_enabled": False,
        "webrtc.ip_handling_policy": "disable_non_proxied_udp",
        "webrtc.multiple_routes_enabled": False,
        "webrtc.nonproxied_udp_enabled": False
    })
    
    # Set a realistic and recent user agent
    chrome_options.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36')

    driver = webdriver.Chrome(
        service=Service(ChromeDriverManager().install()),
        options=chrome_options
    )

    # Execute advanced anti-detection scripts
    driver.execute_cdp_cmd('Network.setUserAgentOverride', {
        "userAgent": 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36',
        "platform": "Windows",
        "userAgentMetadata": {
            "brands": [
                {"brand": "Google Chrome", "version": "131"},
                {"brand": "Chromium", "version": "131"},
                {"brand": "Not_A Brand", "version": "24"}
            ],
            "fullVersionList": [
                {"brand": "Google Chrome", "version": "131.0.6778.86"},
                {"brand": "Chromium", "version": "131.0.6778.86"},
                {"brand": "Not_A Brand", "version": "24.0.0.0"}
            ],
            "fullVersion": "131.0.6778.86",
            "platform": "Windows",
            "platformVersion": "10.0.0",
            "architecture": "x86",
            "model": "",
            "mobile": False,
            "bitness": "64",
            "wow64": False
        }
    })
    
    # Remove webdriver property and other automation indicators
    driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
    
    # Override navigator properties
    driver.execute_cdp_cmd('Page.addScriptToEvaluateOnNewDocument', {
        'source': '''
            Object.defineProperty(navigator, 'webdriver', {
                get: () => undefined
            });
            
            Object.defineProperty(navigator, 'plugins', {
                get: () => [1, 2, 3, 4, 5]
            });
            
            Object.defineProperty(navigator, 'languages', {
                get: () => ['en-US', 'en']
            });
            
            // Override the permissions API
            const originalQuery = window.navigator.permissions.query;
            window.navigator.permissions.query = (parameters) => (
                parameters.name === 'notifications' ?
                    Promise.resolve({ state: Notification.permission }) :
                    originalQuery(parameters)
            );
            
            // Mock chrome object
            window.chrome = {
                runtime: {}
            };
            
            // Override plugins to look more realistic
            Object.defineProperty(navigator, 'plugins', {
                get: () => {
                    return [
                        {
                            0: {type: "application/x-google-chrome-pdf", suffixes: "pdf", description: "Portable Document Format"},
                            description: "Portable Document Format",
                            filename: "internal-pdf-viewer",
                            length: 1,
                            name: "Chrome PDF Plugin"
                        },
                        {
                            0: {type: "application/pdf", suffixes: "pdf", description: "Portable Document Format"},
                            description: "Portable Document Format", 
                            filename: "mhjfbmdgcfjbbpaeojofohoefgiehjai",
                            length: 1,
                            name: "Chrome PDF Viewer"
                        },
                        {
                            0: {type: "application/x-nacl", suffixes: "", description: "Native Client Executable"},
                            1: {type: "application/x-pnacl", suffixes: "", description: "Portable Native Client Executable"},
                            description: "Native Client",
                            filename: "internal-nacl-plugin",
                            length: 2,
                            name: "Native Client"
                        }
                    ];
                }
            });
            
            // Make languages more realistic
            Object.defineProperty(navigator, 'languages', {
                get: () => ['en-US', 'en']
            });
            
            // WebGL vendor override
            const getParameter = WebGLRenderingContext.prototype.getParameter;
            WebGLRenderingContext.prototype.getParameter = function(parameter) {
                if (parameter === 37445) {
                    return 'Intel Inc.';
                }
                if (parameter === 37446) {
                    return 'Intel Iris OpenGL Engine';
                }
                return getParameter.apply(this, [parameter]);
            };
            
            // Override permissions
            const originalPermissionsQuery = window.navigator.permissions.query;
            window.navigator.permissions.query = (parameters) => (
                parameters.name === 'notifications' ?
                    Promise.resolve({ state: Notification.permission }) :
                    originalPermissionsQuery(parameters)
            );
            
            // Add connection property
            Object.defineProperty(navigator, 'connection', {
                get: () => ({
                    effectiveType: '4g',
                    rtt: 50,
                    downlink: 10,
                    saveData: false
                })
            });
            
            // Battery API mock
            navigator.getBattery = () => Promise.resolve({
                charging: true,
                chargingTime: 0,
                dischargingTime: Infinity,
                level: 1
            });
            
            // Hardware concurrency
            Object.defineProperty(navigator, 'hardwareConcurrency', {
                get: () => 8
            });
            
            // Device memory
            Object.defineProperty(navigator, 'deviceMemory', {
                get: () => 8
            });
            
            // Screen properties to make it look more realistic
            Object.defineProperty(screen, 'availHeight', {
                get: () => 1050
            });
            Object.defineProperty(screen, 'availWidth', {
                get: () => 1920
            });
            Object.defineProperty(screen, 'height', {
                get: () => 1080
            });
            Object.defineProperty(screen, 'width', {
                get: () => 1920
            });
        '''
    })

    # Use selenium-stealth for additional protection
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
    
    print("=" * 60)
    print("🔐 MANUAL LOGIN REQUIRED")
    print("=" * 60)
    print("Please log in to Instagram manually in the browser window.")
    print("After logging in and dismissing any popups:")
    print("  1. Make sure you're on the Instagram home page")
    print("  2. Come back to this terminal")
    print("  3. Press ENTER to continue with the automation")
    print("=" * 60)
    
    # Wait for user to press Enter
    input("\n⏸️  Press ENTER after you have logged in manually... ")
    
    print("✅ Proceeding with automation...")
    time.sleep(2)  # Small delay before starting automation


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


# def scrape_first_name(driver, wait_time=10):
#     """
#     Scrape the first name from the Instagram profile page
#     Returns the first word of the name, or username as fallback
#     """
#     wait = WebDriverWait(driver, wait_time)
    
#     try:
#         # Specific selector based on the HTML structure you provided
#         name_xpaths = [
#             "//span[contains(@class, 'x1lliihq x1plvlek xryxfnj x1n2onr6') and @dir='auto']",
#             "//div[contains(@class, 'xdj266r')]//span[contains(@class, 'x1lliihq') and @dir='auto']",
#             "//header//span[contains(@class, 'x1lliihq') and @dir='auto']",
#             "//span[@dir='auto' and contains(@class, 'x1lliihq')]"
#         ]
        
#         for xpath in name_xpaths:
#             try:
#                 name_element = driver.find_element(By.XPATH, xpath)
#                 full_name = name_element.text.strip()
                
#                 # Check if it's actually a name (not empty, not just username)
#                 if full_name and len(full_name) > 0 and not full_name.startswith('@'):
#                     print(f"👤 Found full name: {full_name}")
                    
#                     # Extract first name (first word)
#                     first_name = full_name.split()[0]
                    
#                     # Remove emojis, special characters, and fancy unicode characters
#                     # Keep only basic alphanumeric characters
#                     cleaned_name = ''
#                     for char in first_name:
#                         # Keep only ASCII letters (A-Z, a-z)
#                         if char.isalpha() and ord(char) < 128:
#                             cleaned_name += char
                    
#                     if cleaned_name:
#                         print(f"✨ Using first name: {cleaned_name}")
#                         return cleaned_name
#                     else:
#                         # If name has only special characters, try second word
#                         words = full_name.split()
#                         for word in words:
#                             cleaned = ''.join(c for c in word if c.isalpha() and ord(c) < 128)
#                             if cleaned:
#                                 print(f"✨ Using first name: {cleaned}")
#                                 return cleaned
#             except:
#                 continue
        
#         print(f"⚠️  Could not find profile name, will use username")
#         return None
        
#     except Exception as e:
#         print(f"⚠️  Error scraping name: {e}")
#         return None

def scrape_first_name(driver, wait_time=10):
    """
    Scrape the first name from the Instagram profile page
    Returns the first word of the name, or username as fallback
    """
    wait = WebDriverWait(driver, wait_time)
    
    try:
        # More specific selectors targeting the profile name section
        name_xpaths = [
            # Target the span with both specific classes AND the inline style attribute
            "//div[contains(@class, 'xdj266r')]//span[contains(@class, 'x1lliihq x1plvlek xryxfnj x1n2onr6') and @dir='auto' and @style]",
            
            # Target span inside the specific header section structure
            "//header//div[contains(@class, 'xdj266r')]//span[@dir='auto' and contains(@class, 'x1lliihq')]",
            
            # Look for span with the exact style attribute pattern
            "//span[@dir='auto' and contains(@style, '--x---base-line-clamp-line-height')]",
            
            # More general but still specific to profile header
            "//section//header//span[contains(@class, 'x1lliihq') and @dir='auto']",
        ]
        
        found_names = []
        
        for xpath in name_xpaths:
            try:
                elements = driver.find_elements(By.XPATH, xpath)
                
                for element in elements:
                    text = element.text.strip()
                    
                    # Filter out common false positives
                    if (text and 
                        len(text) > 0 and 
                        not text.startswith('@') and 
                        text.lower() not in ['home', 'search', 'explore', 'reels', 'messages', 
                                             'notifications', 'create', 'profile', 'more',
                                             'following', 'followers', 'posts']):
                        
                        # Additional check: name should have at least one letter
                        if any(c.isalpha() for c in text):
                            found_names.append(text)
                            print(f"👤 Found potential name: {text}")
                
            except:
                continue
        
        # If we found multiple potential names, take the longest one (likely the full name)
        if found_names:
            # Sort by length and take the longest
            full_name = max(found_names, key=len)
            print(f"✨ Selected full name: {full_name}")
            
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
                print(f"✅ Using first name: {cleaned_name}")
                return cleaned_name
            else:
                # If name has only special characters, try second word
                words = full_name.split()
                for word in words:
                    cleaned = ''.join(c for c in word if c.isalpha() and ord(c) < 128)
                    if cleaned:
                        print(f"✅ Using first name: {cleaned}")
                        return cleaned
        
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
            time.sleep(random.uniform(0.5, 1))
            
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
    # first_name = scrape_first_name(driver)
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