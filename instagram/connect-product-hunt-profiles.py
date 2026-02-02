"""
LinkedIn Connection Request Automation with Personalized Messages
Reads profile data from CSV and sends customized connection requests

WARNING: Use responsibly and in compliance with LinkedIn's Terms of Service
REQUIREMENTS: pip install selenium pandas
"""

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
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

class LinkedInConnectionBot:
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
        options.add_argument('--disable-blink-features=AutomationControlled')
        options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36')
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option('useAutomationExtension', False)
        
        self.driver = webdriver.Chrome(options=options)
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
            email_field.send_keys(self.email)
            
            # Enter password
            password_field = self.driver.find_element(By.ID, 'password')
            password_field.send_keys(self.password)
            
            # Click login button
            login_button = self.driver.find_element(By.CSS_SELECTOR, 'button[type="submit"]')
            login_button.click()
            
            # Wait for login to complete
            time.sleep(5)
            
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
        delay = random.uniform(min_seconds, max_seconds)
        logging.debug(f"Waiting {delay:.2f} seconds...")
        time.sleep(delay)
    
    def create_personalized_note(self, profile_data, note_template):
        """
        Create personalized connection note using profile data
        
        Args:
            profile_data: Dictionary containing profile information
            note_template: String template with {field} placeholders
        
        Returns:
            Personalized note string
        """
        try:
            # Get profile data with defaults
            full_name = profile_data.get('name', 'there')
            about_full = profile_data.get('about', 'your field')
            headline = profile_data.get('headline', '')
            current_position = profile_data.get('current_position', '')
            current_company = profile_data.get('current_company', '')
            
            # Extract first word of name (before first space)
            name = full_name.split()[0] if full_name and full_name.strip() else 'there'
            
            # If about is empty, use alternative text
            if not about_full or pd.isna(about_full) or about_full.strip() == '':
                if current_position and current_company:
                    about_full = f"{current_position} at {current_company}"
                elif headline:
                    about_full = headline
                else:
                    about_full = "your professional journey"
            
            # Extract first 2 words of about (separated by space)
            about_words = about_full.split()
            about = ' '.join(about_words[:2]) if len(about_words) >= 2 else about_full
            
            # Format the note
            personalized_note = note_template.format(
                name=name,
                about=about,
                headline=headline,
                current_position=current_position,
                current_company=current_company,
                location=profile_data.get('location', ''),
                connections=profile_data.get('connections', '')
            )
            
            # Ensure note is within LinkedIn's 300 character limit
            if len(personalized_note) > 300:
                logging.warning(f"Note too long ({len(personalized_note)} chars), truncating...")
                personalized_note = personalized_note[:297] + "..."
            
            return personalized_note
            
        except Exception as e:
            logging.error(f"Error creating personalized note: {e}")
            return note_template
    
    def send_connection_request(self, profile_url, note=None):
        """Send connection request to a profile"""
        try:
            logging.info(f"Visiting profile: {profile_url}")
            self.driver.get(profile_url)
            self.human_delay(3, 6)
            
            # Try to find and click the "Connect" button
            connect_clicked = False
            
            try:
                # First, try to find direct Connect button on the MAIN profile
                direct_connect_selectors = [
                    "//main//button[contains(@aria-label, 'Invite') and contains(@aria-label, 'to connect') and not(ancestor::section[contains(., 'More profiles for you') or contains(., 'People you may know') or contains(., 'People also viewed')])]",
                    "//section[contains(@class, 'artdeco-card') and contains(@class, 'pv-top-card')]//button[contains(@aria-label, 'Invite') and contains(@aria-label, 'to connect')]",
                    "//div[contains(@class, 'ph5') and not(ancestor::*[contains(@class, 'scaffold-layout__aside')])]//button[.//span[contains(text(), 'Connect')]]",
                    "//div[contains(@class, 'pv-top-card')]//button[contains(@aria-label, 'Invite')]"
                ]
                
                for selector in direct_connect_selectors:
                    try:
                        connect_button = self.driver.find_element(By.XPATH, selector)
                        if connect_button and connect_button.is_displayed():
                            # Double check it's not in a recommendation section
                            try:
                                parent_html = connect_button.find_element(By.XPATH, "./ancestor::section").get_attribute('innerHTML')
                                if any(text in parent_html.lower() for text in ['more profiles for you', 'people you may know', 'people also viewed']):
                                    logging.info("Skipping Connect button in recommendation section")
                                    continue
                            except:
                                pass  # No section parent, likely main area
                            
                            logging.info("Found direct Connect button on main profile, clicking...")
                            connect_button.click()
                            connect_clicked = True
                            self.human_delay(1, 2)
                            break
                    except (NoSuchElementException, Exception):
                        continue
                
                # If direct Connect button not found, try the "More" dropdown
                if not connect_clicked:
                    logging.info("Direct Connect button not found, trying 'More' dropdown...")
                    
                    more_button_selectors = [
                        "//main//button[contains(@aria-label, 'More actions') and not(ancestor::section[contains(., 'More profiles for you') or contains(., 'People you may know')])]",
                        "//section[contains(@class, 'pv-top-card')]//button[@aria-label='More actions']",
                        "//div[contains(@class, 'pv-top-card')]//button[contains(@id, 'profile-overflow-action')]",
                        "//div[contains(@class, 'ph5') and not(ancestor::aside)]//button[contains(@aria-label, 'More actions')]"
                    ]
                    
                    more_button = None
                    for selector in more_button_selectors:
                        try:
                            more_button = self.driver.find_element(By.XPATH, selector)
                            if more_button and more_button.is_displayed():
                                break
                        except NoSuchElementException:
                            continue
                    
                    if more_button:
                        logging.info("Clicking 'More' button...")
                        more_button.click()
                        self.human_delay(1, 2)
                        
                        # Find Connect in dropdown
                        dropdown_connect_selectors = [
                            "//div[contains(@class, 'artdeco-dropdown__content') and @aria-hidden='false']//div[@role='button' and contains(@aria-label, 'Invite')]",
                            "//div[contains(@class, 'artdeco-dropdown__content') and @aria-hidden='false']//span[text()='Connect']/..",
                        ]
                        
                        for selector in dropdown_connect_selectors:
                            try:
                                connect_option = self.wait.until(
                                    EC.element_to_be_clickable((By.XPATH, selector))
                                )
                                if connect_option:
                                    logging.info("Found Connect in dropdown, clicking...")
                                    connect_option.click()
                                    connect_clicked = True
                                    self.human_delay(1, 2)
                                    break
                            except (NoSuchElementException, TimeoutException):
                                continue
                
                if not connect_clicked:
                    logging.warning(f"Connect button not found for {profile_url}")
                    # Mark as processed since we attempted it
                    return "connect_not_found"
                
                # Add note if provided
                if note:
                    try:
                        # Look for "Add a note" button
                        add_note_button = self.wait.until(
                            EC.element_to_be_clickable((By.XPATH, "//button[contains(@aria-label, 'Add a note')]"))
                        )
                        logging.info("Clicking 'Add a note' button...")
                        add_note_button.click()
                        self.human_delay(1, 2)
                        
                        # Enter the note
                        note_field = self.wait.until(
                            EC.presence_of_element_located((By.TAG_NAME, 'textarea'))
                        )
                        note_field.clear()
                        note_field.send_keys(note)
                        logging.info(f"Added personalized note ({len(note)} chars)")
                        self.human_delay(1, 2)
                    except (NoSuchElementException, TimeoutException):
                        logging.info("No 'Add note' option found, sending without note")
                
                # Click Send button
                send_button = self.wait.until(
                    EC.element_to_be_clickable((By.XPATH, "//button[contains(@aria-label, 'Send') or .//span[contains(text(), 'Send')]]"))
                )
                send_button.click()
                
                logging.info(f"✓ Connection request sent successfully!")
                self.human_delay(3, 6)
                return "success"
                
            except Exception as e:
                logging.error(f"Error in connection flow: {str(e)}")
                return "failed"
                
        except Exception as e:
            logging.error(f"Error sending connection request to {profile_url}: {str(e)}")
            return "failed"
    
    def process_csv_profiles(self, csv_file, note_template, max_requests=20):
        """
        Process profiles from CSV and send connection requests
        
        Args:
            csv_file: Input CSV file with profile data
            note_template: Template string for connection note with {field} placeholders
            max_requests: Maximum number of connection requests to send
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
            if 'connection_date' not in df.columns:
                df['connection_date'] = ''
            if 'connection_note' not in df.columns:
                df['connection_note'] = ''
            if 'connection_status' not in df.columns:
                df['connection_status'] = ''
            
            # Find where to resume from - look for rows where all 3 columns are empty
            # Convert to string and strip whitespace to handle NaN and empty strings
            df['connection_date'] = df['connection_date'].astype(str).str.strip()
            df['connection_note'] = df['connection_note'].astype(str).str.strip()
            df['connection_status'] = df['connection_status'].astype(str).str.strip()
            
            # Replace 'nan' string (from NaN conversion) with empty string
            df['connection_date'] = df['connection_date'].replace('nan', '')
            df['connection_note'] = df['connection_note'].replace('nan', '')
            df['connection_status'] = df['connection_status'].replace('nan', '')
            
            # Find first unprocessed row (where all 3 columns are empty)
            unprocessed_mask = (
                (df['connection_date'] == '') & 
                (df['connection_note'] == '') & 
                (df['connection_status'] == '')
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
            
            # Find first unprocessed index
            first_unprocessed_idx = df[unprocessed_mask].index[0] if remaining_profiles > 0 else None
            
            if first_unprocessed_idx is not None:
                logging.info(f"Resuming from row {first_unprocessed_idx + 1} (index {first_unprocessed_idx})")
            
            successful = 0
            failed = 0
            skipped = 0
            connect_not_found = 0
            
            logging.info(f"\n{'='*70}")
            logging.info(f"Starting to send connection requests (max: {max_requests})")
            logging.info(f"{'='*70}\n")
            
            requests_sent = 0
            
            for idx, row in df.iterrows():
                # Skip already processed rows (where any of the 3 columns are not empty)
                if not unprocessed_mask[idx]:
                    continue
                
                if requests_sent >= max_requests:
                    logging.info(f"Reached maximum requests limit ({max_requests})")
                    skipped = remaining_profiles - requests_sent
                    break
                
                profile_url = row['profile_url']
                
                logging.info(f"\n{'='*70}")
                logging.info(f"Profile {idx + 1}/{total_profiles} (Processing {requests_sent + 1}/{remaining_profiles} remaining)")
                logging.info(f"{'='*70}")
                
                # Create personalized note
                personalized_note = self.create_personalized_note(row.to_dict(), note_template)
                logging.info(f"Personalized note preview:\n{personalized_note}\n")
                
                # Send connection request
                result = self.send_connection_request(profile_url, personalized_note)
                
                # Update the row with results
                df.at[idx, 'connection_date'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                df.at[idx, 'connection_note'] = personalized_note
                
                if result == "success":
                    df.at[idx, 'connection_status'] = 'success'
                    successful += 1
                elif result == "connect_not_found":
                    df.at[idx, 'connection_status'] = 'connect_not_found'
                    connect_not_found += 1
                else:  # failed
                    df.at[idx, 'connection_status'] = 'failed'
                    failed += 1
                
                requests_sent += 1
                
                # Save progress directly to input CSV after each request
                df.to_csv(csv_file, index=False, encoding='utf-8')
                logging.info(f"Progress saved to {csv_file}")
                
                # Add longer delay every few requests
                if requests_sent % 5 == 0 and requests_sent < remaining_profiles:
                    logging.info("Taking a longer break to avoid detection...")
                    self.human_delay(30, 60)
                elif requests_sent < remaining_profiles:
                    self.human_delay(5, 10)
            
            # Final summary
            logging.info(f"\n{'='*70}")
            logging.info(f"CONNECTION REQUEST SUMMARY")
            logging.info(f"{'='*70}")
            logging.info(f"✓ Successful: {successful}")
            logging.info(f"⊘ Connect not found: {connect_not_found}")
            logging.info(f"✗ Failed: {failed}")
            logging.info(f"⊘ Skipped (max limit): {skipped}")
            logging.info(f"Total processed this run: {requests_sent}")
            logging.info(f"Total processed overall: {processed_count + requests_sent}/{total_profiles}")
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
            logging.info("Closing browser in 5 seconds...")
            time.sleep(5)
            self.driver.quit()
            logging.info("Browser closed")

def main():
    """Main execution function"""
    
    # ========== Configuration ==========
    
    # LinkedIn credentials
    EMAIL = os.getenv("EMAIL")
    PASSWORD = os.getenv("PASSWORD")
    
    # Input CSV file (must have 'profile_url' column and other profile data)
    # INPUT_CSV = "linkedin_profiles/extracted_profiles_keydata_10-26-25-17.csv" 
    from datetime import datetime

    # Generate timestamp in mm-dd-yy-hh format (24-hour)
    timestamp = datetime.now().strftime("%m-%d-%y-%H")

    # Construct filename
    # INPUT_CSV  = f"linkedin_profiles/extracted_profile_url_{timestamp}.csv"
    # Input/Output files
    # INPUT_CSV = "linkedin_profiles/extracted_profile_urls-1.csv"  # CSV file with 'url' column
    # INPUT_CSV = f"linkedin_profiles/extracted_profiles_keydata_{timestamp}.csv"  # Output file
    INPUT_CSV = f"producthunt_profiles.csv"  # Output file

    # Maximum connection requests to send (LinkedIn limits ~100/week)
    MAX_REQUESTS = 200
    
    # Connection note template
    # Available placeholders: {name}, {about}, {headline}, {current_position}, {current_company}, {location}
    NOTE_TEMPLATE = """Hi {name} — your profile definitely caught my eye.
An Ive League Indian girl thriving in tech? I had to say hello. Your work in {about} sounds fascinating.

Would love to connect and chat about what you’re working on — you seem super interesting.

Let’s connect and talk!

Cheers,
Jay
 """
    
    # ========== Run Bot ==========
    
    bot = LinkedInConnectionBot(EMAIL, PASSWORD)
    
    try:
        # Setup and login
        bot.setup_driver() 
        
        if bot.login():
            # Process profiles from CSV
            results = bot.process_csv_profiles(
                csv_file=INPUT_CSV,
                note_template=NOTE_TEMPLATE,
                max_requests=MAX_REQUESTS
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