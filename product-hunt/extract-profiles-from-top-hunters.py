import time
import csv
import random
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from selenium.webdriver.common.action_chains import ActionChains
import pandas as pd

def setup_driver():
    """Setup Chrome driver with stealth options"""
    options = webdriver.ChromeOptions()
    
    # Stealth options to avoid detection
    options.add_argument('--start-maximized')
    options.add_argument('--disable-blink-features=AutomationControlled')
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option('useAutomationExtension', False)
    
    # Additional stealth options
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-gpu')
    
    # Set user agent to look like a real browser
    options.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36')
    
    # Add preferences to make it look more human
    prefs = {
        "profile.default_content_setting_values.notifications": 2,
        "credentials_enable_service": False,
        "profile.password_manager_enabled": False
    }
    options.add_experimental_option("prefs", prefs)
    
    driver = webdriver.Chrome(options=options)
    
    # Execute CDP commands to hide webdriver
    driver.execute_cdp_cmd('Network.setUserAgentOverride', {
        "userAgent": 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36'
    })
    
    # Hide webdriver property
    driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
    
    # Override chrome property
    driver.execute_script("""
        Object.defineProperty(navigator, 'plugins', {
            get: () => [1, 2, 3, 4, 5]
        });
    """)
    
    # Override languages
    driver.execute_script("""
        Object.defineProperty(navigator, 'languages', {
            get: () => ['en-US', 'en']
        });
    """)
    
    return driver

def human_like_delay(min_seconds=1, max_seconds=3):
    """Add random delay to simulate human behavior"""
    time.sleep(random.uniform(min_seconds, max_seconds))

def human_like_scroll(driver):
    """Scroll like a human would"""
    # Random scroll
    scroll_pause = random.uniform(0.5, 1.5)
    
    # Get scroll height
    last_height = driver.execute_script("return document.body.scrollHeight")
    
    # Scroll down in steps
    current_position = 0
    scroll_step = random.randint(300, 500)
    
    while current_position < last_height:
        current_position += scroll_step
        driver.execute_script(f"window.scrollTo(0, {current_position});")
        time.sleep(scroll_pause)
        
        # Sometimes scroll back up a bit (human-like)
        if random.random() < 0.2:
            driver.execute_script(f"window.scrollBy(0, -{random.randint(50, 150)});")
            time.sleep(random.uniform(0.3, 0.7))

def human_like_mouse_movement(driver, element):
    """Move mouse in a human-like way before clicking"""
    actions = ActionChains(driver)
    
    # Move to element with some randomness
    x_offset = random.randint(-5, 5)
    y_offset = random.randint(-5, 5)
    
    actions.move_to_element_with_offset(element, x_offset, y_offset)
    actions.pause(random.uniform(0.1, 0.3))
    actions.perform()
    
    human_like_delay(0.3, 0.7)

def wait_for_login(driver):
    """Navigate to ProductHunt and wait for user to login"""
    print("Opening ProductHunt...")
    driver.get("https://www.producthunt.com")
    
    # Add human-like delay
    human_like_delay(2, 4)
    
    print("\n" + "="*50)
    print("Please login to ProductHunt in the browser window")
    print("Once logged in, press ENTER here to continue...")
    print("="*50 + "\n")
    
    input()
    print("Login confirmed! Proceeding with scraping...")

    human_like_delay(1, 2)

def extract_profile_links(driver, target_count=400):
    """Scroll intelligently until target_count profiles are collected"""
    
    print("\nNavigating to Visit Streaks page...")
    driver.get("https://www.producthunt.com/visit-streaks?ref=header_nav")

    human_like_delay(3, 5)

    profile_links = set()
    last_height = driver.execute_script("return document.body.scrollHeight")
    stagnant_scrolls = 0

    print(f"Collecting up to {target_count} profiles...\n")

    while len(profile_links) < target_count and stagnant_scrolls < 3:
        # Collect profiles currently loaded
        elements = driver.find_elements(
            By.CSS_SELECTOR, "a[href*='/users/'], a[href*='/@']"
        )

        before_count = len(profile_links)

        for el in elements:
            href = el.get_attribute("href")
            if not href:
                continue

            if ('/users/' in href or '/@' in href):
                if not any(x in href for x in ['?', '#', 'posts', 'comments', 'upvotes']):
                    profile_links.add(href)

        after_count = len(profile_links)
        print(f"Profiles collected: {after_count}")

        # Check if new profiles were added
        if after_count == before_count:
            stagnant_scrolls += 1
        else:
            stagnant_scrolls = 0

        # Scroll down (human-like)
        scroll_amount = random.randint(600, 900)
        driver.execute_script(f"window.scrollBy(0, {scroll_amount});")

        # Proper interval pause (important)
        human_like_delay(2.5, 4.5)

        # Check page height
        new_height = driver.execute_script("return document.body.scrollHeight")
        if new_height == last_height:
            stagnant_scrolls += 1
        else:
            last_height = new_height

    print(f"\n✅ Finished collecting {len(profile_links)} profiles\n")
    return list(profile_links)[:target_count]


# def extract_profile_links(driver):
#     """Extract all profile links from the visit streaks page"""
#     print("\nNavigating to Visit Streaks page...")
#     driver.get("https://www.producthunt.com/visit-streaks?ref=header_nav")
    
#     # Wait for page to load with human-like delay
#     human_like_delay(3, 5)
    
#     profile_links = []
    
#     try:
#         # Wait for profiles to load
#         WebDriverWait(driver, 10).until(
#             EC.presence_of_all_elements_located((By.CSS_SELECTOR, "a[href*='/users/']"))
#         )
        
#         # Scroll down to load more profiles (human-like)
#         human_like_scroll(driver)
#         human_like_delay(1, 2)
        
#         # Find all profile links
#         profile_elements = driver.find_elements(By.CSS_SELECTOR, "a[href*='/users/'], a[href*='/@']")
        
#         # Extract unique profile URLs
#         seen = set()
#         for element in profile_elements:
#             href = element.get_attribute('href')
#             if href and ('/users/' in href or '/@' in href) and href not in seen:
#                 # Filter out non-profile links
#                 if not any(x in href for x in ['?', '#', 'posts', 'comments', 'upvotes']):
#                     profile_links.append(href)
#                     seen.add(href)
        
#         print(f"Found {len(profile_links)} unique profiles")
        
#     except TimeoutException:
#         print("Timeout while loading profiles. Trying alternative method...")
        
#         # Alternative: scroll and collect
#         last_height = driver.execute_script("return document.body.scrollHeight")
        
#         for _ in range(5):  # Scroll 5 times
#             # Human-like scrolling
#             scroll_amount = random.randint(500, 800)
#             driver.execute_script(f"window.scrollBy(0, {scroll_amount});")
#             human_like_delay(1.5, 2.5)
            
#             new_height = driver.execute_script("return document.body.scrollHeight")
#             if new_height == last_height:
#                 break
#             last_height = new_height
        
#         # Try again after scrolling
#         profile_elements = driver.find_elements(By.CSS_SELECTOR, "a[href*='/users/'], a[href*='/@']")
#         seen = set()
#         for element in profile_elements:
#             href = element.get_attribute('href')
#             if href and ('/users/' in href or '/@' in href) and href not in seen:
#                 if not any(x in href for x in ['?', '#', 'posts', 'comments', 'upvotes']):
#                     profile_links.append(href)
#                     seen.add(href)
        
#         print(f"Found {len(profile_links)} unique profiles after scrolling")
    
#     return profile_links

def follow_user(driver):
    """Try to follow a user on their profile page"""
    try:
        # Look for follow button
        follow_button = driver.find_element(By.XPATH, "//button[contains(text(), 'Follow') or contains(@aria-label, 'Follow')]")
        
        # Check if not already following
        if 'Following' not in follow_button.text:
            # Move mouse to button before clicking (human-like)
            human_like_mouse_movement(driver, follow_button)
            
            # Click with slight delay
            follow_button.click()
            print("  ✓ Followed user")
            human_like_delay(0.5, 1.5)
        else:
            print("  ℹ Already following")
            
    except NoSuchElementException:
        print("  ⚠ Follow button not found")
    except Exception as e:
        print(f"  ⚠ Could not follow: {str(e)}")

def extract_social_links(driver):
    """Extract social media links from the profile page"""
    social_data = {
        'linkedin': None,
        'twitter': None,
        'facebook': None,
        'other_links': []
    }
    
    try:
        # Wait for Links section to load with human-like delay
        human_like_delay(1.5, 2.5)
        
        # Sometimes scroll a bit (human-like behavior)
        if random.random() < 0.3:
            driver.execute_script(f"window.scrollBy(0, {random.randint(100, 300)});")
            human_like_delay(0.5, 1)
        
        # Find all social media links
        social_links = driver.find_elements(By.CSS_SELECTOR, "a[data-test='user-link']")
        
        for link in social_links:
            href = link.get_attribute('href')
            text = link.text.lower()
            
            if not href:
                continue
            
            if 'linkedin.com' in href:
                social_data['linkedin'] = href
            elif 'twitter.com' in href or 'x.com' in href:
                social_data['twitter'] = href
            elif 'facebook.com' in href:
                social_data['facebook'] = href
            else:
                # Collect other social links
                if href not in social_data['other_links']:
                    social_data['other_links'].append(href)
        
        # Alternative: look for any links in the profile
        if not any([social_data['linkedin'], social_data['twitter'], social_data['facebook']]):
            all_links = driver.find_elements(By.TAG_NAME, "a")
            
            for link in all_links:
                href = link.get_attribute('href')
                
                if not href:
                    continue
                
                if 'linkedin.com' in href and not social_data['linkedin']:
                    social_data['linkedin'] = href
                elif ('twitter.com' in href or 'x.com' in href) and not social_data['twitter']:
                    social_data['twitter'] = href
                elif 'facebook.com' in href and not social_data['facebook']:
                    social_data['facebook'] = href
        
    except Exception as e:
        print(f"  ⚠ Error extracting social links: {str(e)}")
    
    return social_data

def extract_full_name(driver):
    """Extract user's full name from profile"""
    try:
        # Try multiple selectors for name
        selectors = [
            "h1",
            "h1.text-24",
            "[data-test='user-name']",
            ".styles-module__name"
        ]
        
        for selector in selectors:
            try:
                name_element = driver.find_element(By.CSS_SELECTOR, selector)
                name = name_element.text.strip()
                if name and len(name) > 0:
                    return name
            except NoSuchElementException:
                continue
        
        return "Name not found"
        
    except Exception as e:
        print(f"  ⚠ Error extracting name: {str(e)}")
        return "Error extracting name"

def scrape_profile(driver, profile_url, index, total):
    """Scrape a single profile"""
    print(f"\n[{index}/{total}] Processing: {profile_url}")
    
    try:
        driver.get(profile_url)
        
        # Human-like page load wait with random delay
        human_like_delay(2, 4)
        
        # Sometimes scroll a bit before extracting (human behavior)
        if random.random() < 0.4:
            driver.execute_script(f"window.scrollBy(0, {random.randint(100, 300)});")
            human_like_delay(0.5, 1)
            driver.execute_script("window.scrollTo(0, 0);")
            human_like_delay(0.3, 0.7)
        
        # Extract full name
        full_name = extract_full_name(driver)
        print(f"  Name: {full_name}")
        
        # Follow the user
        follow_user(driver)
        
        # Extract social links
        social_data = extract_social_links(driver)
        
        # Print found links
        if social_data['linkedin']:
            print(f"  LinkedIn: {social_data['linkedin']}")
        if social_data['twitter']:
            print(f"  Twitter: {social_data['twitter']}")
        if social_data['facebook']:
            print(f"  Facebook: {social_data['facebook']}")
        if social_data['other_links']:
            print(f"  Other links: {len(social_data['other_links'])} found")
        
        return {
            'producthunt_profile': profile_url,
            'full_name': full_name,
            'linkedin': social_data['linkedin'] or '',
            'twitter': social_data['twitter'] or '',
            'facebook': social_data['facebook'] or '',
            'other_links': ', '.join(social_data['other_links']) if social_data['other_links'] else ''
        }
        
    except Exception as e:
        print(f"  ❌ Error processing profile: {str(e)}")
        return {
            'producthunt_profile': profile_url,
            'full_name': 'Error',
            'linkedin': '',
            'twitter': '',
            'facebook': '',
            'other_links': ''
        }

def save_to_csv(data, filename='producthunt_profiles.csv'):
    """Save scraped data to CSV"""
    df = pd.DataFrame(data)
    df.to_csv(filename, index=False)
    print(f"\n✅ Data saved to {filename}")
    print(f"Total profiles scraped: {len(data)}")

def main():
    driver = None
    
    try:
        # Setup
        driver = setup_driver()
        
        # Wait for user to login
        wait_for_login(driver)
        
        # Extract profile links
        profile_links = extract_profile_links(driver)
        
        if not profile_links:
            print("❌ No profiles found. Please check the page structure.")
            return
        
        print(f"\n{'='*50}")
        print(f"Starting to scrape {len(profile_links)} profiles...")
        print(f"{'='*50}\n")
        
        # Scrape each profile
        all_data = []
        total = len(profile_links)
        
        for index, profile_url in enumerate(profile_links, 1):
            profile_data = scrape_profile(driver, profile_url, index, total)
            all_data.append(profile_data)
            
            # Random delay between profiles (2-5 seconds) to appear more human
            human_like_delay(2, 5)
            
            # Occasionally take a longer break (simulate human taking a break)
            if index % 10 == 0:
                print(f"\n  💤 Taking a short break (human-like behavior)...")
                human_like_delay(5, 10)
        
        # Save to CSV
        save_to_csv(all_data)
        
        print("\n" + "="*50)
        print("✅ Scraping completed successfully!")
        print("="*50)
        
    except KeyboardInterrupt:
        print("\n\n⚠ Script interrupted by user")
        if 'all_data' in locals() and all_data:
            print(f"Saving {len(all_data)} profiles scraped so far...")
            save_to_csv(all_data, 'producthunt_profiles_partial.csv')
    
    except Exception as e:
        print(f"\n❌ An error occurred: {str(e)}")
        import traceback
        traceback.print_exc()
    
    finally:
        if driver:
            print("\nClosing browser...")
            driver.quit()

if __name__ == "__main__":
    main()