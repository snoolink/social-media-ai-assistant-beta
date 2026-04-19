"""
LinkedIn Direct Message Automation with Personalized Messages
Reads profile data from CSV and sends customized messages to 1st connections

WARNING: Use responsibly and in compliance with LinkedIn's Terms of Service
REQUIREMENTS: pip install selenium pandas
"""

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from selenium.webdriver.common.keys import Keys
import pandas as pd
import time
import random
import logging
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('linkedin_automation.log'),
        logging.StreamHandler()
    ]
)

class LinkedInMessageBot:
    def __init__(self, email, password):
        """Initialize the LinkedIn automation bot"""
        self.email = email
        self.password = password
        self.driver = None
        self.wait = None
        
    def setup_driver(self):
        """Setup Chrome driver with options"""
        options = webdriver.ChromeOptions()
        # Uncomment to run headless
        # options.add_argument('--headless')
        
        # Anti-detection measures
        options.add_argument('--disable-blink-features=AutomationControlled')
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option('useAutomationExtension', False)
        
        # Realistic user agent
        options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
        
        # Additional stealth options
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-gpu')
        
        # Set window size to common resolution
        options.add_argument('--window-size=1920,1080')
        
        self.driver = webdriver.Chrome(options=options)
        
        # Execute CDP commands to hide automation
        self.driver.execute_cdp_cmd('Network.setUserAgentOverride', {
            "userAgent": 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        })
        self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        
        self.wait = WebDriverWait(self.driver, 10)
        self.driver.maximize_window()
        
    def login(self):
        """Login to LinkedIn"""
        try:
            logging.info("Navigating to LinkedIn login page...")
            self.driver.get('https://www.linkedin.com/login')
            
            # Wait and enter email
            email_field = self.wait.until(
                EC.presence_of_element_located((By.ID, 'username'))
            )
            self.human_delay(0.5, 1.5)
            self.human_type(email_field, self.email, 0.08, 0.18)
            
            # Enter password
            self.human_delay(0.5, 1.5)
            password_field = self.driver.find_element(By.ID, 'password')
            self.human_type(password_field, self.password, 0.08, 0.18)
            
            # Click login button
            self.human_delay(0.8, 1.5)
            login_button = self.driver.find_element(By.CSS_SELECTOR, 'button[type="submit"]')
            login_button.click()
            
            # Wait for login to complete (with more realistic delay)
            self.human_delay(5, 8)
            
            # Check for verification
            if "checkpoint" in self.driver.current_url or "challenge" in self.driver.current_url:
                logging.warning("LinkedIn requires verification. Please complete it manually...")
                input("Press Enter after completing verification...")
            
            # Check if login was successful
            if "feed" in self.driver.current_url or "mynetwork" in self.driver.current_url:
                logging.info("✓ Login successful!")
                return True
            else:
                logging.error("✗ Login may have failed. Please check manually.")
                return False
                
        except Exception as e:
            logging.error(f"Login error: {str(e)}")
            return False
    
    def human_delay(self, min_seconds=2, max_seconds=5):
        """Add random delay to mimic human behavior"""
        # Reduced to half
        min_seconds = min_seconds / 2
        max_seconds = max_seconds / 2
        delay = random.uniform(min_seconds, max_seconds)
        logging.debug(f"Waiting {delay:.2f} seconds...")
        time.sleep(delay)
    
    def human_type(self, element, text, min_delay=0.05, max_delay=0.15):
        """Type text character by character with random delays to mimic human typing"""
        # Reduced to half
        min_delay = min_delay / 2
        max_delay = max_delay / 2
        for char in text:
            element.send_keys(char)
            delay = random.uniform(min_delay, max_delay)
            time.sleep(delay)
    
    def random_mouse_movement(self):
        """Simulate random mouse movements"""
        try:
            from selenium.webdriver.common.action_chains import ActionChains
            actions = ActionChains(self.driver)
            
            # Random small movements (reduced count)
            for _ in range(random.randint(1, 2)):
                x_offset = random.randint(-50, 50)
                y_offset = random.randint(-50, 50)
                actions.move_by_offset(x_offset, y_offset)
                actions.perform()
                time.sleep(random.uniform(0.05, 0.15))
        except:
            pass  # If fails, just skip
    
    def create_personalized_message(self, profile_data, message_template):
        """
        Create personalized message using profile data
        
        Args:
            profile_data: Dictionary containing profile information
            message_template: String template with {field} placeholders
        
        Returns:
            Personalized message string
        """
        try:
            # Get profile data with defaults
            full_name = profile_data.get('name', 'there')
            company_name_full = profile_data.get('about', 'your field')
            headline = profile_data.get('headline', '')
            current_position = profile_data.get('current_position', '')
            current_company = profile_data.get('about', '')
            
            # Extract first word of name (before first space)
            name = full_name.split()[0] if full_name and full_name.strip() else 'there'
            
            # If company_name is empty, use alternative text
            if not company_name_full or pd.isna(company_name_full) or company_name_full.strip() == '':
                if current_position and current_company:
                    company_name_full = f"{current_position} at {current_company}"
                elif headline:
                    company_name_full = headline
                else:
                    company_name_full = "your professional journey"
            
            # Extract first 2 words of company_name (separated by space)
            company_name_words = company_name_full.split()
            company_name = ' '.join(company_name_words[:2]) if len(company_name_words) >= 2 else company_name_full
            
            # Determine what to use for "about" field
            about = company_name_full
            
            # Format the message
            personalized_message = message_template.format(
                name=name,
                company_name=company_name,
                about=about,
                headline=headline,
                current_position=current_position,
                current_company=current_company,
                location=profile_data.get('location', ''),
                connections=profile_data.get('connections', '')
            )
            
            return personalized_message
            
        except Exception as e:
            logging.error(f"Error creating personalized message: {e}")
            return message_template
    
    def send_direct_message(self, profile_url, message):
        """Send direct message to a 1st connection"""
        try:
            logging.info(f"Visiting profile: {profile_url}")
            self.driver.get(profile_url)
            
            # Random realistic delays and mouse movements
            self.human_delay(4, 8)
            self.random_mouse_movement()
            
            # Scroll down slowly to mimic reading profile
            scroll_amount = random.randint(300, 600)
            self.driver.execute_script(f"window.scrollBy(0, {scroll_amount});")
            self.human_delay(2, 4)
            
            # Scroll back up
            self.driver.execute_script("window.scrollTo(0, 0);")
            self.human_delay(1, 2)
            
            # Try to find and click the "Message" button
            message_clicked = False
            
            try:
                # Selectors for the Message button
                message_button_selectors = [
                    "//main//button[contains(@aria-label, 'Message') and not(ancestor::section[contains(., 'More profiles for you') or contains(., 'People you may know') or contains(., 'People also viewed')])]",
                    "//section[contains(@class, 'pv-top-card')]//button[contains(@aria-label, 'Message')]",
                    "//div[contains(@class, 'ph5') and not(ancestor::*[contains(@class, 'scaffold-layout__aside')])]//button[.//span[contains(text(), 'Message')]]",
                    "//button[contains(@class, 'artdeco-button--primary') and .//span[text()='Message']]"
                ]
                
                for selector in message_button_selectors:
                    try:
                        message_button = self.driver.find_element(By.XPATH, selector)
                        if message_button and message_button.is_displayed():
                            # Double check it's not in a recommendation section
                            try:
                                parent_html = message_button.find_element(By.XPATH, "./ancestor::section").get_attribute('innerHTML')
                                if any(text in parent_html.lower() for text in ['more profiles for you', 'people you may know', 'people also viewed']):
                                    logging.info("Skipping Message button in recommendation section")
                                    continue
                            except:
                                pass  # No section parent, likely main area
                            
                            logging.info("Found Message button, clicking...")
                            
                            # Hover before clicking (more human-like)
                            from selenium.webdriver.common.action_chains import ActionChains
                            actions = ActionChains(self.driver)
                            actions.move_to_element(message_button).perform()
                            self.human_delay(0.5, 1.2)
                            
                            message_button.click()
                            message_clicked = True
                            self.human_delay(3, 5)
                            break
                    except (NoSuchElementException, Exception):
                        continue
                
                if not message_clicked:
                    logging.warning(f"Message button not found for {profile_url} - may not be a 1st connection")
                    return "message_not_found"
                
                # Wait for message compose box to appear
                try:
                    # Look for the message input field
                    message_box_selectors = [
                        "//div[contains(@class, 'msg-form__contenteditable')]",
                        "//div[@role='textbox' and @contenteditable='true']",
                        "//div[contains(@class, 'msg-form__msg-content-container')]//div[@contenteditable='true']"
                    ]
                    
                    message_box = None
                    for selector in message_box_selectors:
                        try:
                            message_box = self.wait.until(
                                EC.presence_of_element_located((By.XPATH, selector))
                            )
                            if message_box:
                                break
                        except (NoSuchElementException, TimeoutException):
                            continue
                    
                    if not message_box:
                        logging.error("Could not find message input box")
                        return "failed"
                    
                    # Clear any existing text and type the message
                    logging.info("Typing message...")
                    message_box.click()
                    self.human_delay(0.8, 1.5)
                    
                    # Sometimes move cursor around a bit (realistic behavior)
                    self.random_mouse_movement()
                    
                    # Clear the box first
                    message_box.send_keys(Keys.CONTROL + "a")
                    self.human_delay(0.2, 0.4)
                    message_box.send_keys(Keys.DELETE)
                    self.human_delay(0.5, 1)
                    
                    # Type the message with realistic pauses
                    lines = message.split('\n')
                    for i, line in enumerate(lines):
                        # Occasionally pause as if thinking
                        if random.random() < 0.2:  # 20% chance
                            self.human_delay(0.5, 1.5)
                        
                        # Type with character-by-character delays
                        self.human_type(message_box, line, 0.05, 0.15)
                        
                        if i < len(lines) - 1:  # Don't add extra newline after last line
                            self.human_delay(0.3, 0.6)
                            message_box.send_keys(Keys.SHIFT + Keys.RETURN)
                            self.human_delay(0.2, 0.5)
                    
                    logging.info(f"Message typed ({len(message)} chars)")
                    
                    # Pause before sending (as if reviewing)
                    self.human_delay(2, 4)
                    
                    # Find and click Send button
                    send_button_selectors = [
                        "//button[contains(@class, 'msg-form__send-button') and not(@disabled)]",
                        "//button[@type='submit' and contains(@class, 'msg-form__send-button')]",
                        "//footer//button[contains(@class, 'artdeco-button--primary') and not(@disabled)]"
                    ]
                    
                    send_button = None
                    for selector in send_button_selectors:
                        try:
                            send_button = self.wait.until(
                                EC.element_to_be_clickable((By.XPATH, selector))
                            )
                            if send_button:
                                break
                        except (NoSuchElementException, TimeoutException):
                            continue
                    
                    if not send_button:
                        logging.error("Could not find Send button")
                        # Try to close window before returning
                        try:
                            from selenium.webdriver.common.action_chains import ActionChains
                            actions = ActionChains(self.driver)
                            actions.send_keys(Keys.ESCAPE).perform()
                        except:
                            pass
                        return "failed"
                    
                    logging.info("Clicking Send button...")
                    
                    # Scroll to send button to ensure it's in view
                    self.driver.execute_script("arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});", send_button)
                    self.human_delay(0.5, 1)
                    
                    # Hover over send button before clicking
                    from selenium.webdriver.common.action_chains import ActionChains
                    actions = ActionChains(self.driver)
                    actions.move_to_element(send_button).perform()
                    self.human_delay(0.5, 1)
                    
                    send_button.click()
                    
                    logging.info(f"✓ Message sent successfully!")
                    self.human_delay(2, 3)
                    
                    # Close the messaging window to avoid interference with next message
                    try:
                        close_button_selectors = [
                            "//button[contains(@aria-label, 'Close') and contains(@aria-label, 'conversation')]",
                            "//button[contains(@aria-label, 'Dismiss') and contains(@class, 'msg-overlay-bubble-header__control')]",
                            "//aside//button[@data-control-name='overlay.close_conversation_window']",
                            "//button[contains(@class, 'msg-overlay-bubble-header__control--new-convo-btn')]//preceding-sibling::button"
                        ]
                        
                        close_button = None
                        for selector in close_button_selectors:
                            try:
                                close_button = self.driver.find_element(By.XPATH, selector)
                                if close_button and close_button.is_displayed():
                                    break
                            except NoSuchElementException:
                                continue
                        
                        if close_button:
                            logging.info("Closing message window...")
                            close_button.click()
                            self.human_delay(1, 2)
                        else:
                            # Alternative: press Escape key to close
                            logging.info("Pressing Escape to close message window...")
                            from selenium.webdriver.common.action_chains import ActionChains
                            actions = ActionChains(self.driver)
                            actions.send_keys(Keys.ESCAPE).perform()
                            self.human_delay(1, 2)
                    
                    except Exception as e:
                        logging.warning(f"Could not close message window, but message was sent: {e}")
                    
                    self.human_delay(2, 3)
                    return "success"
                    
                except Exception as e:
                    logging.error(f"Error in message compose flow: {str(e)}")
                    # Try to close any open message windows before continuing
                    try:
                        from selenium.webdriver.common.action_chains import ActionChains
                        actions = ActionChains(self.driver)
                        actions.send_keys(Keys.ESCAPE).perform()
                        self.human_delay(1, 2)
                    except:
                        pass
                    return "failed"
                
            except Exception as e:
                logging.error(f"Error finding Message button: {str(e)}")
                return "failed"
                
        except Exception as e:
            logging.error(f"Error sending message to {profile_url}: {str(e)}")
            return "failed"
    
    def process_csv_profiles(self, csv_file, message_template, max_messages=20):
        """
        Process profiles from CSV and send messages
        
        Args:
            csv_file: Input CSV file with profile data
            message_template: Template string for message with {field} placeholders
            max_messages: Maximum number of messages to send
        """
        try:
            # Read CSV
            logging.info(f"Reading profiles from {csv_file}...")
            df = pd.read_csv(csv_file)
            
            # Check required columns
            if 'profile_url' not in df.columns:
                logging.error("CSV must contain 'profile_url' column!")
                return None
            
            # Ensure required columns exist
            if 'message_date' not in df.columns:
                df['message_date'] = ''
            if 'message_content' not in df.columns:
                df['message_content'] = ''
            if 'message_status' not in df.columns:
                df['message_status'] = ''
            
            # Find where to resume from - look for rows where all 3 columns are empty
            df['message_date'] = df['message_date'].astype(str).str.strip()
            df['message_content'] = df['message_content'].astype(str).str.strip()
            df['message_status'] = df['message_status'].astype(str).str.strip()
            
            # Replace 'nan' string (from NaN conversion) with empty string
            df['message_date'] = df['message_date'].replace('nan', '')
            df['message_content'] = df['message_content'].replace('nan', '')
            df['message_status'] = df['message_status'].replace('nan', '')
            
            # Find first unprocessed row
            unprocessed_mask = (
                (df['message_date'] == '') & 
                (df['message_content'] == '') & 
                (df['message_status'] == '')
            )
            
            processed_count = (~unprocessed_mask).sum()
            total_profiles = len(df)
            remaining_profiles = unprocessed_mask.sum()
            
            logging.info(f"✓ Total profiles in CSV: {total_profiles}")
            logging.info(f"✓ Already processed: {processed_count}")
            logging.info(f"✓ Remaining to process: {remaining_profiles}")
            
            if remaining_profiles == 0:
                logging.info("All profiles have been processed!")
                return df
            
            first_unprocessed_idx = df[unprocessed_mask].index[0] if remaining_profiles > 0 else None
            
            if first_unprocessed_idx is not None:
                logging.info(f"Resuming from row {first_unprocessed_idx + 1} (index {first_unprocessed_idx})")
            
            successful = 0
            failed = 0
            skipped = 0
            message_not_found = 0
            
            logging.info(f"\n{'='*70}")
            logging.info(f"Starting to send messages (max: {max_messages})")
            logging.info(f"{'='*70}\n")
            
            messages_sent = 0
            
            for idx, row in df.iterrows():
                # Skip already processed rows
                if not unprocessed_mask[idx]:
                    continue
                
                if messages_sent >= max_messages:
                    logging.info(f"Reached maximum messages limit ({max_messages})")
                    skipped = remaining_profiles - messages_sent
                    break
                
                profile_url = row['profile_url']
                
                logging.info(f"\n{'='*70}")
                logging.info(f"Profile {idx + 1}/{total_profiles} (Processing {messages_sent + 1}/{remaining_profiles} remaining)")
                logging.info(f"{'='*70}")
                
                # Create personalized message
                personalized_message = self.create_personalized_message(row.to_dict(), message_template)
                logging.info(f"Personalized message preview:\n{personalized_message}\n")
                
                # Send message
                result = self.send_direct_message(profile_url, personalized_message)
                
                # Update the row with results
                df.at[idx, 'message_date'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                df.at[idx, 'message_content'] = personalized_message
                
                if result == "success":
                    df.at[idx, 'message_status'] = 'success'
                    successful += 1
                elif result == "message_not_found":
                    df.at[idx, 'message_status'] = 'message_not_found'
                    message_not_found += 1
                else:  # failed
                    df.at[idx, 'message_status'] = 'failed'
                    failed += 1
                
                messages_sent += 1
                
                # Save progress after each message
                df.to_csv(csv_file, index=False, encoding='utf-8')
                logging.info(f"Progress saved to {csv_file}")
                
                # Variable delays between messages (more realistic) - reduced to half
                if messages_sent % 10 == 0 and messages_sent < remaining_profiles:
                    # Longer break every 10 messages
                    break_time = random.randint(60, 120)  # 1-2 minutes (was 2-4)
                    logging.info(f"Taking a longer break ({break_time}s) to appear more human...")
                    time.sleep(break_time)
                elif messages_sent % 5 == 0 and messages_sent < remaining_profiles:
                    # Medium break every 5 messages
                    break_time = random.randint(22, 45)  # 22-45 seconds (was 45-90)
                    logging.info(f"Taking a medium break ({break_time}s)...")
                    time.sleep(break_time)
                elif messages_sent < remaining_profiles:
                    # Short random break between each message
                    break_time = random.randint(7, 17)  # 7-17 seconds (was 15-35)
                    logging.info(f"Short break ({break_time}s)...")
                    time.sleep(break_time)
            
            # Final summary
            logging.info(f"\n{'='*70}")
            logging.info(f"MESSAGE SUMMARY")
            logging.info(f"{'='*70}")
            logging.info(f"✓ Successful: {successful}")
            logging.info(f"⊘ Message button not found: {message_not_found}")
            logging.info(f"✗ Failed: {failed}")
            logging.info(f"⊘ Skipped (max limit): {skipped}")
            logging.info(f"Total processed this run: {messages_sent}")
            logging.info(f"Total processed overall: {processed_count + messages_sent}/{total_profiles}")
            logging.info(f"Results saved to: {csv_file}")
            logging.info(f"{'='*70}\n")
            
            return df
            
        except Exception as e:
            logging.error(f"Error processing CSV: {str(e)}")
            import traceback
            traceback.print_exc()
            return None
    
    def close(self):
        """Close the browser"""
        if self.driver:
            logging.info("Closing browser in 2.5 seconds...")
            time.sleep(2.5)
            self.driver.quit()
            logging.info("Browser closed")

def main():
    """Main execution function"""
    
    # ========== Configuration ==========
    
    # LinkedIn credentials
    EMAIL = "jaytalksdata@gmail.com"
    PASSWORD = "Switch@2025"
    
    # Input CSV file
    INPUT_CSV = "linkedin_profiles/extracted_profiles_keydata_01-12-26-20.csv" 
 
    # Maximum messages to send per session (keep it reasonable - 15-25 per session)
    MAX_MESSAGES = 20
    
    # Message template
    # Available placeholders: {name}, {company_name}, {about}, {headline}, {current_position}, {current_company}, {location}
    MESSAGE_TEMPLATE = """Hi {name},

I came across {about} and saw how much content your team manages for social and creators.

Out of curiosity — when you need a very specific clip (like a creator smiling, outdoors, with a product), how do you usually find it? Most teams tell us they're stuck manually scrolling through folders and files.

We're building Snoolink to solve exactly that — it lets you search your entire photo and video library using natural language, so you get the right clip instantly.

If this is a real headache for you, I'd love to learn how you're handling it today.
Happy to jump on a quick 10-minute call.

— Jay
(www.snoolink.com)"""
    
    # ========== Run Bot ==========
    
    bot = LinkedInMessageBot(EMAIL, PASSWORD)
    
    try:
        # Setup and login
        bot.setup_driver() 
        
        if bot.login():
            # Process profiles from CSV
            results = bot.process_csv_profiles(
                csv_file=INPUT_CSV,
                message_template=MESSAGE_TEMPLATE,
                max_messages=MAX_MESSAGES
            )
            
            if results is not None:
                logging.info("✓ Process completed successfully!")
        else:
            logging.error("✗ Login failed. Please check your credentials.")
        
    except KeyboardInterrupt:
        logging.info("\n⚠ Script interrupted by user")
    except Exception as e:
        logging.error(f"✗ An error occurred: {str(e)}")
        import traceback
        traceback.print_exc()
    finally:
        bot.close()


if __name__ == "__main__":
    main()