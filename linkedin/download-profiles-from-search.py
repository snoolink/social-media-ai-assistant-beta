"""
This scripts download all the profiles avaialable in a people's search results on linkedin

https://www.linkedin.com/search/results/people/?keywords=founding%20engineer&origin=FACETED_SEARCH&geoUrn=%5B%22103644278%22%5D&activelyHiringForJobTitles=%5B%229%22%2C%22340%22%2C%222732%22%5D
"""

import pandas as pd
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
import time
import json
import os
from creds import LINKEDIN_USERNAME, LINKEDIN_PASSWORD

def scroll_to_bottom(driver, pause_time=2):
    """Scroll to the bottom of the page"""
    last_height = driver.execute_script("return document.body.scrollHeight")
    
    while True:
        # Scroll down to bottom
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        
        # Wait for page to load
        time.sleep(pause_time)
        
        # Calculate new scroll height and compare with last scroll height
        new_height = driver.execute_script("return document.body.scrollHeight")
        if new_height == last_height:
            break
        last_height = new_height

def extract_profile_data(driver):
    """Extract profile information from the current page"""
    profile_data = {}
    
    try:
        # Scroll to load all content
        scroll_to_bottom(driver)
        
        # Get page source
        profile_data['page_source'] = driver.page_source
        profile_data['url'] = driver.current_url
        
        # Try to extract basic information (adjust selectors as needed)
        try:
            name = driver.find_element(By.CSS_SELECTOR, "h1").text
            profile_data['name'] = name
        except:
            profile_data['name'] = "Not found"
        
        # Add timestamp
        profile_data['scraped_at'] = time.strftime("%Y-%m-%d %H:%M:%S")
        
    except Exception as e:
        print(f"Error extracting data: {str(e)}")
        profile_data['error'] = str(e)
    
    return profile_data

def login_to_linkedin(driver, email, password):
    """
    Automated login to LinkedIn
    
    Args:
        driver: Selenium WebDriver instance
        email: LinkedIn email
        password: LinkedIn password
    """
    try:
        print("Logging in to LinkedIn...")
        driver.get("https://www.linkedin.com/login")
        
        # Wait for login page to load
        time.sleep(2)
        
        # Find and fill email field
        email_field = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, "username"))
        )
        email_field.clear()
        email_field.send_keys(email)
        
        # Find and fill password field
        password_field = driver.find_element(By.ID, "password")
        password_field.clear()
        password_field.send_keys(password)
        
        # Click login button
        login_button = driver.find_element(By.CSS_SELECTOR, "button[type='submit']")
        login_button.click()
        
        # Wait for login to complete
        time.sleep(5)
        
        # Check if login was successful by looking for feed or profile
        try:
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.ID, "global-nav"))
            )
            print("✓ Successfully logged in to LinkedIn")
            return True
        except TimeoutException:
            print("⚠ Login may have failed or requires verification")
            print("Please complete any verification steps in the browser...")
            input("Press Enter after completing verification...")
            return True
            
    except Exception as e:
        print(f"✗ Login error: {str(e)}")
        return False

def extract_profile_links_from_page(driver, page_url, max_pages=10):
    """
    Extract all LinkedIn profile links from a specific page with pagination
    
    Args:
        driver: Selenium WebDriver instance
        page_url: URL of the page to extract profiles from
        max_pages: Maximum number of pages to scrape (default: 10)
    
    Returns:
        List of profile URLs
    """
    print(f"\nNavigating to page: {page_url}")
    driver.get(page_url)
    
    # Wait for page to load
    time.sleep(3)
    
    all_profile_links = set()
    current_page = 1
    
    while current_page <= max_pages:
        print(f"\n--- Page {current_page} ---")
        
        # Scroll to load all profiles on current page
        print("Scrolling to load all content...")
        scroll_to_bottom(driver, pause_time=2)
        
        # Extract profile links from current page
        try:
            # Find all links on the page
            all_links = driver.find_elements(By.TAG_NAME, "a")
            
            page_profiles = 0
            for link in all_links:
                try:
                    href = link.get_attribute("href")
                    if href and "/in/" in href and "linkedin.com" in href:
                        # Clean the URL (remove query parameters)
                        clean_url = href.split('?')[0]
                        if clean_url not in all_profile_links:
                            all_profile_links.add(clean_url)
                            page_profiles += 1
                except:
                    continue
            
            print(f"✓ Found {page_profiles} new profiles on this page (Total: {len(all_profile_links)})")
            
        except Exception as e:
            print(f"Error extracting profile links: {str(e)}")
        
        # Try to find and click the Next button
        try:
            # Scroll to bottom to make sure Next button is visible
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(2)
            
            # Multiple selectors for Next button
            next_button = None
            next_selectors = [
                "//button[@aria-label='Next']",
                "//button[contains(@aria-label, 'Next')]",
                "//button[contains(text(), 'Next')]",
                "//span[text()='Next']/parent::button",
                ".artdeco-pagination__button--next",
                "button.artdeco-pagination__button--next",
                # New additions for the latest structure
                "//button[@data-testid='pagination-controls-next-button-visible']",
                "//button[@data-testid='pagination-controls-next-button-visible']//span[contains(text(), 'Next')]",
                "button[data-testid='pagination-controls-next-button-visible']",
                "//span[contains(text(), 'Next')]/ancestor::button"
            ]
            
            for selector in next_selectors:
                try:
                    if selector.startswith("//"):
                        # XPath selector
                        buttons = driver.find_elements(By.XPATH, selector)
                    else:
                        # CSS selector
                        buttons = driver.find_elements(By.CSS_SELECTOR, selector)
                    
                    for btn in buttons:
                        if btn.is_displayed() and btn.is_enabled():
                            # Check if button is not disabled
                            disabled = btn.get_attribute("disabled")
                            aria_disabled = btn.get_attribute("aria-disabled")
                            
                            if not disabled and aria_disabled != "true":
                                next_button = btn
                                break
                    
                    if next_button:
                        break
                except:
                    continue
            
            if next_button:
                print("✓ Clicking Next button...")
                driver.execute_script("arguments[0].scrollIntoView(true);", next_button)
                time.sleep(1)
                next_button.click()
                time.sleep(4)  # Wait for next page to load
                current_page += 1
            else:
                print("✓ No more pages (Next button not found or disabled)")
                break
                
        except Exception as e:
            print(f"✓ Reached last page or error with pagination: {str(e)}")
            break
    
    print(f"\n{'='*60}")
    print(f"✓ Total profiles found across {current_page} page(s): {len(all_profile_links)}")
    print(f"{'='*60}")
    
    return list(all_profile_links)

def download_linkedin_profiles(csv_file, email, password, output_dir='linkedin_profiles', start_page_url=None, max_pages=10):
    """
    Download LinkedIn profiles from URLs in a CSV file or from a specific page
    
    Args:
        csv_file: Path to CSV file containing LinkedIn URLs (optional if start_page_url is provided)
        email: LinkedIn email for login
        password: LinkedIn password for login
        output_dir: Directory to save profile data
        start_page_url: URL of page to extract profile links from (e.g., search results, company page)
        max_pages: Maximum number of pages to scrape when using start_page_url (default: 10)
    """
    # Create output directory if it doesn't exist
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    # Setup Selenium WebDriver
    options = webdriver.ChromeOptions()
    # Uncomment the next line to run in headless mode
    # options.add_argument('--headless')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    # Disable automation flags to avoid detection
    options.add_argument('--disable-blink-features=AutomationControlled')
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option('useAutomationExtension', False)
    
    driver = webdriver.Chrome(options=options)
    
    # Add script to avoid detection
    driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
    
    try:
        # Automated login
        if not login_to_linkedin(driver, email, password):
            print("Login failed. Exiting...")
            return
        
        # Get profile URLs
        profile_urls = []
        
        if start_page_url:
            # Extract profiles from the specified page
            profile_urls = extract_profile_links_from_page(driver, start_page_url, max_pages)
            
            # Save extracted URLs to CSV
            urls_df = pd.DataFrame({'url': profile_urls})        # Save to CSV
            from datetime import datetime

            # Generate timestamp in mm-dd-yy-hh format (24-hour)
            timestamp = datetime.now().strftime("%m-%d-%y-%H")

            # Construct filename
            csv_filename = f"extracted_profiles_of_tech_recs_{timestamp}.csv"
            urls_df.to_csv(f"{output_dir}/{csv_filename}", index=False)
            print(f"✓ Saved extracted URLs to {output_dir}/{csv_filename}")
            
        elif csv_file:
            # Read CSV file
            df = pd.read_csv(csv_file)
            
            # Find URL column
            url_column = None
            for col in df.columns:
                if 'url' in col.lower() or 'linkedin' in col.lower():
                    url_column = col
                    break
            
            if url_column is None:
                print("Available columns:", df.columns.tolist())
                url_column = input("Enter the column name containing LinkedIn URLs: ")
            
            profile_urls = df[url_column].tolist()
        else:
            print("Error: Please provide either a CSV file or a start_page_url")
            return
        
        if not profile_urls:
            print("No profile URLs to process. Exiting...")
            return
        
        print(f"\n{'='*60}")
        print(f"Starting to download {len(profile_urls)} profiles...")
        print(f"{'='*60}\n")
        """
        results = []
        
        # Process each URL
        for idx, url in enumerate(profile_urls):
            print(f"\nProcessing {idx + 1}/{len(profile_urls)}: {url}")
            
            try:
                driver.get(url)
                
                # Wait for page to load
                WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.TAG_NAME, "body"))
                )
                
                # Extract profile data
                profile_data = extract_profile_data(driver)
                
                # Save individual profile HTML
                filename = f"{output_dir}/profile_{idx + 1}.html"
                # with open(filename, 'w', encoding='utf-8') as f:
                #     f.write(profile_data.get('page_source', ''))
                
                # print(f"✓ Saved: {filename}")
                
                # Store metadata
                results.append({
                    'index': idx,
                    'url': url,
                    'name': profile_data.get('name', 'N/A'),
                    'filename': filename,
                    'scraped_at': profile_data.get('scraped_at', ''),
                    'status': 'success'
                })
                
                # Be polite - add delay between requests
                time.sleep(3)
                
            except Exception as e:
                print(f"✗ Error processing {url}: {str(e)}")
                results.append({
                    'index': idx,
                    'url': url,
                    'status': 'error',
                    'error': str(e)
                })
        
        # Save results summary
        results_df = pd.DataFrame(results)
        results_df.to_csv(f"{output_dir}/scraping_results.csv", index=False)
        print(f"\n✓ Results saved to {output_dir}/scraping_results.csv")
        """
    finally:
        driver.quit()

if __name__ == "__main__":
    # ========== Configuration ==========
    email = LINKEDIN_USERNAME
    password = LINKEDIN_PASSWORD
    output_dir = "linkedin/linkedin_profiles"

    # ========== Usage Examples ==========
    
    # Example 1: Extract profiles from a specific LinkedIn search page with pagination
    page_url = "https://www.linkedin.com/search/results/people/?keywords=co%20founder&origin=FACETED_SEARCH&geoUrn=%5B%22103644278%22%5D&activelyHiringForJobTitles=%5B%229%22%2C%2239%22%2C%222732%22%2C%2225190%22%5D"
    download_linkedin_profiles(
        csv_file=None,
        email=email, 
        password=password, 
        start_page_url=page_url, 
        max_pages=30  # Adjust based on how many pages you want to scrape
    )
