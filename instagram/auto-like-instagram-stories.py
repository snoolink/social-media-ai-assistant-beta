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
from selenium.webdriver.common.action_chains import ActionChains

# ======== CONFIGURATION ========
CSV_FILE = "instagram-profiles/itsaryan_jay.csv"  # Must contain column 'url'
DAILY_STORY_LIKE_LIMIT = 200  # Maximum story likes per day
BREAK_AFTER = 15  # Take a break after this many likes
MIN_BREAK_TIME = 12  # Minimum break time in seconds (2 minutes)
MAX_BREAK_TIME = 30 # Maximum break time in seconds (5 minutes)
MIN_WAIT_BETWEEN_PROFILES = 8  # Minimum wait between profiles (seconds)
MAX_WAIT_BETWEEN_PROFILES = 20  # Maximum wait between profiles (seconds)
# ===============================

def human_like_mouse_move(driver, element):
    """Simulate human-like mouse movement to an element"""
    try:
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
        
        # Click on the story element with human-like behavior
        try:
            driver.execute_script("arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});", story_element)
            time.sleep(random.uniform(0.8, 1.5))
            
            # Human-like mouse movement
            human_like_mouse_move(driver, story_element)
            
            try:
                story_element.click()
            except:
                driver.execute_script("arguments[0].click();", story_element)
            
            # Wait for story to load with human-like delay
            load_wait = random.uniform(3, 5)
            print(f"⏳ Waiting {load_wait:.1f} seconds for story to load...")
            time.sleep(load_wait)
            
        except Exception as e:
            print(f"⚠️  Could not click story element: {e}")
            return False, "click_failed"
        
        # Occasionally scroll within the story viewer (human behavior)
        if random.random() > 0.7:
            random_scroll(driver)
        
        # DIRECT BUTTON CLICK - Find and click the like button
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
            
            # Human-like pause before clicking like (as if watching the story)
            watch_time = random.uniform(1.5, 3.5)
            print(f"👀 Watching story for {watch_time:.1f} seconds...")
            time.sleep(watch_time)
            
            # Human-like mouse movement to like button
            human_like_mouse_move(driver, like_button)
            
            # Click the like button
            print(f"👆 Clicking like button now...")
            try:
                like_button.click()
                print(f"✅ Like button clicked!")
            except:
                # Try JavaScript click if regular click fails
                driver.execute_script("arguments[0].click();", like_button)
                print(f"✅ Like button clicked (JS)!")
            
            # Brief pause after liking
            time.sleep(random.uniform(0.8, 1.5))
            
        except Exception as e:
            print(f"⚠️  Error clicking like button: {e}")
            # Close story and return failure
            try:
                driver.find_element(By.TAG_NAME, 'body').send_keys(Keys.ESCAPE)
                time.sleep(0.5)
            except:
                pass
            return False, "like_click_failed"
        
        # Close the story viewer with human-like delay
        try:
            time.sleep(random.uniform(1, 2))
            driver.find_element(By.TAG_NAME, 'body').send_keys(Keys.ESCAPE)
            time.sleep(random.uniform(0.8, 1.5))
        except:
            try:
                close_btn = driver.find_element(By.XPATH, "//button[@aria-label='Close']")
                close_btn.click()
                time.sleep(0.8)
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
        
        # Human-like wait time
        wait_time_human = random.uniform(3, 5)
        time.sleep(wait_time_human)
        
        # Occasionally scroll on the profile page
        if random.random() > 0.6:
            random_scroll(driver)
        
    except Exception as e:
        print(f"❌ Navigation error to {profile_url}: {e}")
        return False, "navigation_error"
    
    # Check if account is public
    if not is_public_account(driver, username):
        return False, "private_account"
    
    # Small delay before checking story with human-like variation
    time.sleep(random.uniform(1.5, 3))
    
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

