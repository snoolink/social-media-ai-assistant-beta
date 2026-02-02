#!/usr/bin/env python3
"""
Product Hunt Automation Script with Gemini AI
Automates browsing, upvoting, and commenting on top products of the day
Uses Gemini AI to generate personalized comments
"""

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
import time
import os
import random
import google.generativeai as genai
from creds import GEMINI_API_KEY

# API Keys configuration - will randomly select one for each product
API_KEYS = [
    os.getenv("GOOGLE_API_KEY_1", GEMINI_API_KEY),  # Default key from creds.py
]

def setup_driver():
    """Initialize Chrome driver with options"""
    options = webdriver.ChromeOptions()
    options.add_argument('--start-maximized')
    options.add_argument('--disable-blink-features=AutomationControlled')
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option('useAutomationExtension', False)
    
    driver = webdriver.Chrome(options=options)
    return driver

def setup_gemini(api_key=None):
    """Setup Gemini API with a specific key or random selection"""
    if not api_key:
        # Filter out None/empty keys
        valid_keys = [key for key in API_KEYS if key]
        
        if not valid_keys: 
            print("\n⚠ WARNING: No valid API keys found")
            print("Please set environment variables: GOOGLE_API_KEY_1, GOOGLE_API_KEY_2")
            print("Or update the API_KEYS array in the script")
            print("Get your API keys from: https://makersuite.google.com/app/apikey")
            print("Falling back to default comments...\n")
            return None
        
        # Randomly select an API key
        api_key = random.choice(valid_keys)
        print(f"🔑 Selected API key #{API_KEYS.index(api_key) + 1}")
    
    try:
        genai.configure(api_key=api_key)
        # Using gemini-2.0-flash - latest model
        model = genai.GenerativeModel('gemini-2.0-flash')
        print("✓ Gemini AI initialized successfully\n")
        return model
    except Exception as e:
        print(f"⚠ Error initializing Gemini: {e}")
        print("Falling back to default comments...\n")
        return None

def get_product_info(driver):
    """Extract product name and description from the page"""
    try:
        product_info = {}
        
        # Get product name - from the h1 or main heading
        try:
            name = driver.find_element(By.CSS_SELECTOR, "h1").text
            product_info['name'] = name
        except:
            product_info['name'] = "this product"
        
        # Get product description/tagline - multiple possible locations
        description_selectors = [
            "h2",  # Often the tagline
            "p.text-secondary",
            "div.text-secondary",
            "[data-test='product-description']",
            "meta[name='description']",
            "meta[property='og:description']"
        ]
        
        description = ""
        for selector in description_selectors:
            try:
                if selector.startswith("meta"):
                    elem = driver.find_element(By.CSS_SELECTOR, selector)
                    description = elem.get_attribute('content')
                else:
                    elem = driver.find_element(By.CSS_SELECTOR, selector)
                    desc_text = elem.text.strip()
                    if desc_text and len(desc_text) > 10:
                        description = desc_text
                        break
            except:
                continue
        
        product_info['description'] = description if description else "An innovative product"
        
        # Try to get more details from the page
        try:
            # Get the main content area
            main_content = driver.find_elements(By.CSS_SELECTOR, "p, div.text-16")
            details = []
            for elem in main_content[:5]:  # Get first 5 paragraphs
                text = elem.text.strip()
                if text and len(text) > 20 and len(text) < 500:
                    details.append(text)
            
            if details:
                product_info['details'] = " ".join(details[:3])
        except:
            pass
        
        print(f"  📝 Product: {product_info.get('name', 'Unknown')}")
        print(f"  📄 Description: {product_info.get('description', 'N/A')[:100]}...")
        
        return product_info
        
    except Exception as e:
        print(f"  ⚠ Error extracting product info: {e}")
        return {'name': 'this product', 'description': 'An innovative product'}

def generate_comment_with_gemini(model, product_info):
    """Generate a personalized comment using Gemini AI"""
    if not model:
        return "This is so good. Exactly what I needed."
    
    try:
        product_name = product_info.get('name', 'this product')
        description = product_info.get('description', '')
        details = product_info.get('details', '')
        
        prompt = f"""You are an enthusiastic Product Hunt user who just discovered an exciting new product.

Product Name: {product_name}
Product Description: {description}
{f'Additional Details: {details}' if details else ''}

Write a short, authentic comment (2-3 sentences max, under 280 characters) that:
1. Shows genuine appreciation and excitement
2. Mentions a specific aspect or feature that caught your attention
3. Asks one thoughtful, niche question about how it works or a specific use case

Keep it conversational, friendly, and human-like. Avoid corporate language or excessive emoji.
Do not use quotation marks in your response.
"""
        
        response = model.generate_content(prompt)
        comment = response.text.strip()
        
        # Remove any quotation marks
        comment = comment.replace('"', '').replace("'", '')
        
        # Ensure it's not too long
        if len(comment) > 500:
            comment = comment[:497] + "..."
        
        print(f"  🤖 Generated comment: {comment[:100]}...")
        return comment
        
    except Exception as e:
        print(f"  ⚠ Error generating comment with Gemini: {e}")
        return "This is so good. Exactly what I needed."

def wait_for_manual_login(driver):
    """Wait for user to manually log in"""
    print("\n" + "="*60)
    print("PLEASE LOG IN TO PRODUCT HUNT")
    print("="*60)
    print("\nThe browser window should now be open.")
    print("Please:")
    print("1. Log in to your Product Hunt account")
    print("2. Make sure you're fully logged in")
    print("3. Press ENTER here in the terminal when ready...")
    print("="*60 + "\n")
    
    input("Press ENTER when you've completed login: ")
    print("\nGreat! Starting automation...\n")

def get_top_products(driver):
    """Get list of top products from today's page"""
    print("Fetching today's top products...")
    
    try:
        # Wait for products to load
        wait = WebDriverWait(driver, 10)
        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "section[data-test^='post-item']")))
        time.sleep(2)
        
        # Find all product sections in "Top Products Launching Today"
        product_links = []
        
        # Find the "Top Products Launching Today" section
        sections = driver.find_elements(By.CSS_SELECTOR, "section[data-test^='post-item']")
        
        for section in sections:
            try:
                # Find the link within each section that has the product URL
                link = section.find_element(By.CSS_SELECTOR, "a[href*='/products/']")
                href = link.get_attribute('href')
                
                if href and '/products/' in href and href not in product_links:
                    product_links.append(href)
            except:
                continue
        
        print(f"Found {len(product_links)} product(s)")
        return product_links  # Return all products (removed [:10] limit)
        
    except Exception as e:
        print(f"Error finding products: {e}")
        return []

def upvote_product(driver):
    """Click the upvote button on a product"""
    try:
        # The upvote button has data-test="vote-button"
        wait = WebDriverWait(driver, 10)
        
        # Wait for and find the upvote button
        upvote_btn = wait.until(EC.presence_of_element_located(
            (By.CSS_SELECTOR, "button[data-test='vote-button']")
        ))
        
        # Scroll to button
        driver.execute_script("arguments[0].scrollIntoView(true);", upvote_btn)
        time.sleep(1)
        
        # Click the button
        upvote_btn.click()
        print("  ✓ Upvoted!")
        time.sleep(2)
        return True
        
    except Exception as e:
        print(f"  ⚠ Error upvoting: {e}")
        return False

def leave_comment(driver, message="This is so good. Exactly what I needed."):
    """Leave a comment on the product"""
    try:
        # Scroll down to load comment section
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight/2);")
        time.sleep(2)
        
        # Look for comment input field - try multiple approaches
        comment_selectors = [
            "textarea[placeholder*='comment' i]",
            "textarea[placeholder*='Add a comment' i]",
            "textarea[name='comment']",
            "div[contenteditable='true']",
            "textarea"
        ]
        
        for selector in comment_selectors:
            try:
                comment_field = driver.find_element(By.CSS_SELECTOR, selector)
                if comment_field and comment_field.is_displayed():
                    # Scroll to comment field
                    driver.execute_script("arguments[0].scrollIntoView(true);", comment_field)
                    time.sleep(1)
                    
                    # Click and enter comment
                    comment_field.click()
                    time.sleep(0.5)
                    comment_field.send_keys(message)
                    time.sleep(1)
                    
                    # Look for submit button near the comment field
                    try:
                        # Try to find parent form and submit button
                        parent = comment_field.find_element(By.XPATH, "./ancestor::form")
                        submit_btn = parent.find_element(By.CSS_SELECTOR, "button[type='submit']")
                        submit_btn.click()
                        print(f"  ✓ Commented: '{message[:80]}...'")
                        time.sleep(2)
                        return True
                    except:
                        # Try finding any nearby submit button
                        submit_buttons = driver.find_elements(By.CSS_SELECTOR, "button[type='submit']")
                        for btn in submit_buttons:
                            if btn.is_displayed():
                                btn.click()
                                print(f"  ✓ Commented: '{message[:80]}...'")
                                time.sleep(2)
                                return True
                    
            except NoSuchElementException:
                continue
        
        print("  ⚠ Could not find comment field or submit button")
        return False
        
    except Exception as e:
        print(f"  ⚠ Error commenting: {e}")
        return False

def process_product(driver, product_url, index, total):
    """Process a single product: extract info, upvote and comment"""
    try:
        print(f"\n[{index}/{total}] Processing product...")
        print(f"URL: {product_url}")
        
        driver.get(product_url)
        time.sleep(3)  # Wait for page to load
        
        # Extract product information
        product_info = get_product_info(driver)
        
        # Upvote the product
        upvote_product(driver)
        
        # Setup Gemini with a random API key for this product
        gemini_model = setup_gemini()
        
        # Generate personalized comment with Gemini
        comment = generate_comment_with_gemini(gemini_model, product_info)
        
        # Leave the comment
        leave_comment(driver, comment)
        
        # Random delay between 30-45 seconds before next product
        if index < total:  # Don't delay after the last product
            delay = random.randint(30, 45)
            print(f"\n⏱  Waiting {delay} seconds before next product...")
            time.sleep(delay)
        
    except Exception as e:
        print(f"  ✗ Error processing product: {e}")

def main():
    """Main execution function"""
    driver = None
    
    try:
        print("\n🚀 Product Hunt Automation Script with Gemini AI")
        print("="*60)
        print(f"📊 {len([k for k in API_KEYS if k])} API key(s) configured")
        print("="*60)
        
        # Setup driver
        driver = setup_driver()
        
        # Navigate to Product Hunt
        print("\nNavigating to Product Hunt...")
        driver.get("https://www.producthunt.com")
        time.sleep(2)
        
        # Wait for manual login
        wait_for_manual_login(driver)
        
        # Make sure we're on the main page
        driver.get("https://www.producthunt.com")
        time.sleep(2)
        
        # Get top products
        product_links = get_top_products(driver)
        
        if not product_links:
            print("\n⚠ No products found. Please check the page structure.")
            return
        
        # Process each product
        print(f"\n🎯 Processing {len(product_links)} product(s)...\n")
        print("⏱  Random delays of 30-45 seconds will be added between products")
        print("="*60)
        
        for i, product_url in enumerate(product_links, 1):
            process_product(driver, product_url, i, len(product_links))
        
        print("\n" + "="*60)
        print("✅ Automation complete!")
        print("="*60)
        print("\nThe browser will stay open for 10 seconds...")
        time.sleep(10)
        
    except KeyboardInterrupt:
        print("\n\n⚠ Script interrupted by user")
        
    except Exception as e:
        print(f"\n✗ An error occurred: {e}")
        
    finally:
        if driver:
            print("\nClosing browser...")
            driver.quit()
            print("Done!")

if __name__ == "__main__":
    main()