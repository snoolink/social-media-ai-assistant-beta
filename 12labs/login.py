from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.action_chains import ActionChains
import time
import random

def random_sleep(min_seconds=1, max_seconds=3):
    """Random sleep to mimic human behavior"""
    time.sleep(random.uniform(min_seconds, max_seconds))

def setup_undetected_driver():
    """Configure Chrome to avoid detection as automated software"""
    chrome_options = Options()
    
    # Disable automation flags
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    chrome_options.add_experimental_option('useAutomationExtension', False)
    
    # Disable blink features that reveal automation
    chrome_options.add_argument('--disable-blink-features=AutomationControlled')
    
    # Add user agent to appear more like a real browser
    chrome_options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
    
    # Additional stealth options
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--start-maximized')
    
    # Create driver
    driver = webdriver.Chrome(options=chrome_options)
    
    # Remove webdriver property
    driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
    
    # Override the navigator.plugins to make it look more realistic
    driver.execute_cdp_cmd('Network.setUserAgentOverride', {
        "userAgent": 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    })
    
    # Add more realistic navigator properties
    driver.execute_script("""
        Object.defineProperty(navigator, 'languages', {
            get: () => ['en-US', 'en']
        });
        Object.defineProperty(navigator, 'plugins', {
            get: () => [1, 2, 3, 4, 5]
        });
    """)
    
    return driver

def human_typing(element, text, min_delay=0.05, max_delay=0.15):
    """Simulate human-like typing with random delays"""
    for char in text:
        element.send_keys(char)
        time.sleep(random.uniform(min_delay, max_delay))

def crawl_website(driver):
    """
    Navigate to the index page and perform video search
    """
    print("\n" + "="*60)
    print("STARTING WEBSITE CRAWLING")
    print("="*60 + "\n")
    
    wait = WebDriverWait(driver, 15)
    
    try:
        # Navigate to the specific index URL
        target_url = "https://playground.twelvelabs.io/indexes/6931b2a67a1ec630b5fa1d24/"
        print(f"Navigating to: {target_url}")
        driver.get(target_url)
        random_sleep(3, 5)
        
        print(f"Current URL: {driver.current_url}")
        print(f"Page Title: {driver.title}")
        
        # First, click on the Search tab
        print("\nLooking for Search tab button...")
        try:
            # Find the Search tab using data-testid
            search_tab = wait.until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, 'a[data-testid="index-tab-search"]'))
            )
            print("Found Search tab!")
            random_sleep(0.5, 1.5)
            search_tab.click()
            print("Clicked on Search tab!")
            random_sleep(2, 4)
            
        except TimeoutException:
            print("Could not find Search tab using data-testid")
            # Try alternative selector
            try:
                search_tab = wait.until(
                    EC.element_to_be_clickable((By.XPATH, '//a[contains(@href, "/search")]//button[contains(text(), "Search")]'))
                )
                search_tab.click()
                print("Clicked Search tab using XPath!")
                random_sleep(2, 4)
            except:
                print("Failed to find Search tab with alternative methods")
                return
        
        # Search query
        search_query = """Search through the entire video and extract only the scenes that clearly show a river, water body, or waterfront area. Prioritize frames where a water taxi, water cruise, or boat is visible on the river. Look for wide, cinematic views capturing flowing water, reflections, and movement of the boats. Exclude all scenes that do not contain the river. Return only the timestamps of the best 1–3 river-focused clips that would look visually appealing in a travel Instagram reel."""
        
        # Find the search input box using the contenteditable div
        print("\nLooking for search input box...")
        try:
            # Try to find the contenteditable div
            search_box = wait.until(
                EC.presence_of_element_located((By.CSS_SELECTOR, 'div[contenteditable="true"][data-slate-editor="true"]'))
            )
            print("Found search input box (contenteditable)")
            
            # Click on the search box to focus it
            random_sleep(0.5, 1)
            search_box.click()
            random_sleep(0.5, 1)
            
            # Clear any existing content
            search_box.clear()
            random_sleep(0.3, 0.7)
            
            # Type the search query with human-like typing
            print("Typing search query...")
            human_typing(search_box, search_query, 0.03, 0.08)
            random_sleep(1, 2)
            
            print("Search query entered successfully!")
            
        except TimeoutException:
            print("Could not find the search input box using contenteditable selector")
            # Try alternative selector
            try:
                search_box = wait.until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, 'div[data-slate-node="value"]'))
                )
                print("Found search box using alternative selector")
                search_box.click()
                random_sleep(0.5, 1)
                human_typing(search_box, search_query, 0.03, 0.08)
                random_sleep(1, 2)
            except:
                print("Failed to find search box with alternative methods")
                return
        
        # Find and click the search button
        print("\nLooking for search button...")
        try:
            # Try to find the search button by aria-label
            search_button = wait.until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, 'button[aria-label="Search"]'))
            )
            print("Found search button!")
            random_sleep(0.5, 1.5)
            
            # Click the search button
            search_button.click()
            print("Clicked search button!")
            random_sleep(3, 5)
            
            print("\nSearch submitted successfully!")
            print("Waiting for results to load...")
            random_sleep(5, 8)
            
        except TimeoutException:
            print("Could not find search button")
            # Try alternative approach - find button with search icon SVG
            try:
                search_button = driver.find_element(By.XPATH, '//button[@aria-label="Search"]')
                search_button.click()
                print("Clicked search button using XPath!")
                random_sleep(5, 8)
            except:
                print("Failed to click search button")
        
        print("\n" + "="*60)
        print("SEARCH COMPLETED - Results should be loading")
        print("="*60 + "\n")
        
    except Exception as e:
        print(f"Error during crawling: {str(e)}")
        import traceback
        traceback.print_exc()

def main():
    # Initialize the undetected Chrome driver
    driver = setup_undetected_driver()
    
    try:
        # Navigate to the URL
        print("Navigating to https://playground.twelvelabs.io/")
        driver.get("https://playground.twelvelabs.io/")
        random_sleep(2, 4)
        
        # Wait for manual login
        print("\n" + "="*60)
        print("MANUAL LOGIN REQUIRED")
        print("="*60)
        print("\nPlease complete the following steps manually:")
        print("1. Click on 'Continue with Google' (or any login method)")
        print("2. Enter your credentials")
        print("3. Complete any CAPTCHA or verification steps")
        print("4. Wait until you're fully logged in and on the main page")
        print("\nOnce you're successfully logged in, press ENTER here...")
        print("="*60 + "\n")
        
        # Wait for user confirmation that login is complete
        input("Press ENTER after you've confirmed successful sign-in: ")
        
        print("\nSign-in confirmed! Starting crawling operations...")
        random_sleep(1, 2)
        
        # Perform crawling operations
        crawl_website(driver)
        
    except Exception as e:
        print(f"An error occurred: {str(e)}")
    
    finally:
        # Keep the browser open for observation
        print("\n" + "="*60)
        input("Press ENTER to close the browser and exit...")
        driver.quit()

if __name__ == "__main__":
    main()