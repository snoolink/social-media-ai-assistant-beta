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
from creds import LINKEDIN_USERNAME, LINKEDIN_PASSWORD


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
        self.email = email
        self.password = password
        self.driver = None
        self.wait = None
        
    def setup_driver(self):
        options = webdriver.ChromeOptions()
        options.add_argument('--disable-blink-features=AutomationControlled')
        options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36')
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option('useAutomationExtension', False)
        
        self.driver = webdriver.Chrome(options=options)
        self.wait = WebDriverWait(self.driver, 10)
        self.driver.maximize_window()
        
    def login(self):
        try:
            logging.info("Navigating to LinkedIn login page...")
            self.driver.get('https://www.linkedin.com/login')
            
            email_field = self.wait.until(EC.presence_of_element_located((By.ID, 'username')))
            email_field.send_keys(self.email)
            
            password_field = self.driver.find_element(By.ID, 'password')
            password_field.send_keys(self.password)
            
            login_button = self.driver.find_element(By.CSS_SELECTOR, 'button[type="submit"]')
            login_button.click()
            
            time.sleep(5)
            
            if "checkpoint" in self.driver.current_url or "challenge" in self.driver.current_url:
                logging.warning("LinkedIn requires verification. Please complete it manually...")
                input("Press Enter after completing verification...")
            
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
        delay = random.uniform(min_seconds, max_seconds)
        time.sleep(delay)

    def discover_connect_button(self):
        """
        Discover the Connect element on a LinkedIn profile page.

        Key insight from inspecting real LinkedIn HTML:
          - The Connect button is an <a> tag (NOT a <button>) with:
              href="/preload/custom-invite/?vanityName=..."
              aria-label="Invite <Name> to connect"
          - It may appear directly in the top action bar, OR only inside
            the "More actions" popover/dropdown (also an <a> with the same
            href pattern).
          - The "More actions" trigger is a <button> whose aria-label contains
            "More actions" or whose visible text is "More".

        Returns (element, method_string) or (None, None).
        """
        try:
            self.wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "main")))
        except TimeoutException:
            logging.warning("[DISCOVERY] <main> not found, continuing...")

        time.sleep(2)

        # ------------------------------------------------------------------ #
        # METHOD 1 — Direct <a href="/preload/custom-invite/..."> in top bar  #
        # ------------------------------------------------------------------ #
        # This is the most reliable selector: href starts with the invite path
        candidates = self.driver.find_elements(
            By.CSS_SELECTOR,
            "a[href*='/preload/custom-invite/']"
        )
        logging.info(f"[DISCOVERY] Found {len(candidates)} <a> elements with custom-invite href")

        for el in candidates:
            try:
                if not el.is_displayed():
                    continue
                label = el.get_attribute("aria-label") or ""
                href  = el.get_attribute("href") or ""
                logging.info(f"  → aria-label='{label}' href='{href[:80]}'")
                if "invite" in label.lower() and "connect" in label.lower():
                    if self._is_in_recommendation_section(el):
                        logging.info("    (skipping — inside recommendation section)")
                        continue
                    logging.info(f"[DISCOVERY] ✓ Direct Connect <a> found (Method 1): '{label}'")
                    return el, "direct_a_href"
            except Exception:
                continue

        # ------------------------------------------------------------------ #
        # METHOD 2 — <a> or element whose visible text / span says "Connect" #
        #            and is NOT in the sidebar                                #
        # ------------------------------------------------------------------ #
        connect_anchors = self.driver.find_elements(
            By.XPATH,
            "//main//a[.//span[normalize-space(text())='Connect'] or normalize-space(text())='Connect']"
        )
        logging.info(f"[DISCOVERY] Found {len(connect_anchors)} <a> with 'Connect' text in <main>")
        for el in connect_anchors:
            try:
                if not el.is_displayed():
                    continue
                if self._is_in_recommendation_section(el):
                    continue
                logging.info(f"[DISCOVERY] ✓ Connect <a> found by text (Method 2)")
                return el, "direct_a_text"
            except Exception:
                continue

        # ------------------------------------------------------------------ #
        # METHOD 3 — "More actions" popover → Connect item inside it         #
        # The popover is a <div popover="manual"> that contains an <a> with  #
        # href="/preload/custom-invite/..." and aria-label "Invite … connect" #
        # ------------------------------------------------------------------ #
        logging.info("[DISCOVERY] Direct Connect not found. Trying 'More actions' popover...")

        # Find the More actions trigger button in the profile top area
        more_btn = None

        # Audit all buttons so we can see what's on the page
        all_buttons = self.driver.find_elements(By.TAG_NAME, "button")
        logging.info(f"[DISCOVERY] Auditing {len(all_buttons)} buttons for 'More actions'...")
        for i, btn in enumerate(all_buttons):
            try:
                label = btn.get_attribute("aria-label") or ""
                text  = btn.text.strip()
                vis   = btn.is_displayed()
                logging.info(f"  btn[{i}] vis={vis} label='{label}' text='{text}'")
                if not vis:
                    continue
                if "more actions" in label.lower() or text.lower() in ("more", "…", "..."):
                    if not self._is_in_recommendation_section(btn):
                        more_btn = btn
                        logging.info(f"[DISCOVERY] Found 'More actions' button: label='{label}' text='{text}'")
                        break
            except Exception:
                continue

        if more_btn is None:
            logging.warning("[DISCOVERY] 'More actions' button not found.")
            return None, None

        # Click it
        try:
            self.driver.execute_script("arguments[0].scrollIntoView({block:'center'});", more_btn)
            time.sleep(0.4)
            self.driver.execute_script("arguments[0].click();", more_btn)
            time.sleep(1.5)
        except Exception as e:
            logging.error(f"[DISCOVERY] Could not click More actions: {e}")
            return None, None

        # The popover is a div with popover="manual" — wait for it to appear
        # Then look for the custom-invite <a> inside it
        try:
            popover = WebDriverWait(self.driver, 5).until(
                EC.visibility_of_element_located(
                    (By.CSS_SELECTOR, "div[popover='manual'] a[href*='/preload/custom-invite/']")
                )
            )
            label = popover.get_attribute("aria-label") or ""
            logging.info(f"[DISCOVERY] ✓ Connect <a> found in popover (Method 3): '{label}'")
            return popover, "popover_a_href"
        except TimeoutException:
            pass

        # Fallback: scan all newly visible <a> elements for custom-invite href
        all_anchors = self.driver.find_elements(By.CSS_SELECTOR, "a[href*='/preload/custom-invite/']")
        for el in all_anchors:
            try:
                if not el.is_displayed():
                    continue
                label = el.get_attribute("aria-label") or ""
                logging.info(f"[DISCOVERY] ✓ Connect <a> found after popover open (fallback): '{label}'")
                return el, "popover_fallback"
            except Exception:
                continue

        # Also check for <div role="menuitem"> or <a role="menuitem"> with "Connect" text
        menu_items = self.driver.find_elements(
            By.XPATH,
            "//*[@role='menuitem'][.//p[normalize-space(text())='Connect'] or normalize-space(text())='Connect']"
        )
        for el in menu_items:
            try:
                if el.is_displayed():
                    logging.info(f"[DISCOVERY] ✓ Connect menuitem found (Method 3b)")
                    return el, "popover_menuitem"
            except Exception:
                continue

        logging.warning("[DISCOVERY] Connect not found in popover/dropdown either.")
        from selenium.webdriver.common.keys import Keys
        try:
            self.driver.find_element(By.TAG_NAME, "body").send_keys(Keys.ESCAPE)
        except Exception:
            pass

        return None, None

    def _is_in_recommendation_section(self, element):
        """Check if element is inside a recommendation/suggested people section."""
        try:
            # Walk up ancestors to find section text
            script = """
                var el = arguments[0];
                var depth = 0;
                while (el && depth < 10) {
                    var text = (el.getAttribute('aria-label') || el.getAttribute('data-test-id') || el.id || '').toLowerCase();
                    if (text.includes('people you may know') || text.includes('more profiles') || text.includes('people also viewed')) {
                        return true;
                    }
                    // Check class names
                    var cls = (el.className || '').toLowerCase();
                    if (cls.includes('aside') || cls.includes('scaffold-layout__aside')) {
                        return true;
                    }
                    el = el.parentElement;
                    depth++;
                }
                return false;
            """
            return self.driver.execute_script(script, element)
        except Exception:
            return False

    def create_personalized_note(self, profile_data, note_template):
        try:
            full_name = profile_data.get('name', 'there')
            about_full = profile_data.get('about', 'your field')
            headline = profile_data.get('headline', '')
            current_position = profile_data.get('current_position', '')
            current_company = profile_data.get('current_company', '')
            
            name = full_name.split()[0] if full_name and full_name.strip() else 'there'
            
            if not about_full or pd.isna(about_full) or str(about_full).strip() == '':
                if current_position and current_company:
                    about_full = f"{current_position} at {current_company}"
                elif headline:
                    about_full = headline
                else:
                    about_full = "your professional journey"
            
            about_words = str(about_full).split()
            about = ' '.join(about_words[:2]) if len(about_words) >= 2 else about_full
            
            personalized_note = note_template.format(
                name=name,
                about=about,
                headline=headline,
                current_position=current_position,
                current_company=current_company,
                location=profile_data.get('location', ''),
                connections=profile_data.get('connections', '')
            )
            
            if len(personalized_note) > 300:
                logging.warning(f"Note too long ({len(personalized_note)} chars), truncating...")
                personalized_note = personalized_note[:297] + "..."
            
            return personalized_note
            
        except Exception as e:
            logging.error(f"Error creating personalized note: {e}")
            return note_template
    
    def send_connection_request(self, profile_url, note=None):
        """
        Send a connection request to a LinkedIn profile.

        LinkedIn's Connect flow (as of 2025):
          1. The Connect element is an <a href="/preload/custom-invite/?vanityName=...">
             Clicking it navigates to a new page — the custom invite / note page.
          2. On that page there is a textarea for the optional note and a Send button.
          3. If Connect is not in the top action bar it lives inside a popover triggered
             by the "More actions" button (same <a> href pattern inside the popover).
        """
        try:
            logging.info(f"Visiting profile: {profile_url}")
            self.driver.get(profile_url)
            self.human_delay(3, 5)

            # ---------------------------------------------------------------- #
            # STEP 1 — Discover and click the Connect element                  #
            # ---------------------------------------------------------------- #
            connect_el, method = self.discover_connect_button()

            if connect_el is None:
                logging.warning(f"[SEND] Connect element not found for {profile_url}")
                return "connect_not_found"

            connect_href = connect_el.get_attribute("href") or ""
            logging.info(f"[SEND] Clicking Connect element (method={method}) href='{connect_href[:80]}'")

            self.driver.execute_script("arguments[0].scrollIntoView({block:'center'});", connect_el)
            time.sleep(0.4)

            # Navigate directly via href if it's a /preload/custom-invite/ link —
            # this is more reliable than clicking an <a> that may be intercepted.
            if "/preload/custom-invite/" in connect_href:
                logging.info("[SEND] Navigating directly to custom-invite URL...")
                self.driver.get(connect_href)
            else:
                self.driver.execute_script("arguments[0].click();", connect_el)

            self.human_delay(2, 3)

            # ---------------------------------------------------------------- #
            # STEP 2 — We are now on the custom-invite page OR a modal opened  #
            # Detect which case we're in.                                      #
            # ---------------------------------------------------------------- #
            current_url = self.driver.current_url
            logging.info(f"[SEND] Current URL after click: {current_url}")

            on_invite_page = "custom-invite" in current_url or "preload" in current_url

            if on_invite_page:
                # ---- CASE A: Dedicated invite page ---- #
                logging.info("[SEND] On custom-invite page.")

                if note:
                    # Click "Add a note" button first — aria-label="Add a note"
                    try:
                        add_note_btn = WebDriverWait(self.driver, 8).until(
                            EC.element_to_be_clickable(
                                (By.CSS_SELECTOR, "button[aria-label='Add a note']")
                            )
                        )
                        self.driver.execute_script("arguments[0].click();", add_note_btn)
                        logging.info("[SEND] Clicked 'Add a note' button.")
                        self.human_delay(0.8, 1.2)

                        # Now type into the textarea that appears
                        textarea = WebDriverWait(self.driver, 8).until(
                            EC.presence_of_element_located((By.CSS_SELECTOR, "textarea"))
                        )
                        textarea.clear()
                        textarea.send_keys(note)
                        logging.info(f"[SEND] Note entered ({len(note)} chars).")
                        self.human_delay(0.8, 1.2)

                    except TimeoutException:
                        logging.warning("[SEND] 'Add a note' button or textarea not found; sending without note.")

                # Click "Send invitation" — aria-label="Send invitation", button text="Send"
                return self._click_send_button()

            else:
                # ---- CASE B: Modal appeared (fallback / older flow) ---- #
                try:
                    modal = WebDriverWait(self.driver, 6).until(
                        EC.presence_of_element_located(
                            (By.CSS_SELECTOR, "[role='dialog'], [aria-modal='true']")
                        )
                    )
                    logging.info("[SEND] Modal detected.")
                except TimeoutException:
                    logging.warning("[SEND] No modal and not on invite page — may have sent directly.")
                    return "success"

                # Audit modal buttons
                modal_buttons = modal.find_elements(By.TAG_NAME, "button")
                logging.info(f"[SEND] Modal has {len(modal_buttons)} buttons:")
                for i, b in enumerate(modal_buttons):
                    try:
                        logging.info(f"  modal_btn[{i}] label='{b.get_attribute('aria-label')}' text='{b.text.strip()}'")
                    except Exception:
                        pass

                # Click "Add a note" if note provided
                if note:
                    for btn in modal_buttons:
                        try:
                            lbl = (btn.get_attribute("aria-label") or "").lower()
                            txt = btn.text.strip().lower()
                            if "add a note" in lbl or "add a note" in txt:
                                self.driver.execute_script("arguments[0].click();", btn)
                                self.human_delay(1, 1.5)
                                textarea = WebDriverWait(self.driver, 6).until(
                                    EC.presence_of_element_located((By.CSS_SELECTOR, "textarea"))
                                )
                                textarea.clear()
                                textarea.send_keys(note)
                                logging.info(f"[SEND] Note entered in modal ({len(note)} chars)")
                                self.human_delay(0.8, 1.2)
                                break
                        except Exception:
                            continue

                return self._click_send_button()

        except Exception as e:
            logging.error(f"[SEND] Error for {profile_url}: {e}")
            import traceback
            traceback.print_exc()
            return "failed"

    def _click_send_button(self):
        """
        Find and click the Send invitation button.
        Targets aria-label='Send invitation' first (most stable), then falls back.
        Returns 'success' or 'failed'.
        """
        # Primary: aria-label="Send invitation" (the exact label LinkedIn uses)
        try:
            send_btn = WebDriverWait(self.driver, 8).until(
                EC.element_to_be_clickable(
                    (By.CSS_SELECTOR, "button[aria-label='Send invitation']")
                )
            )
            self.driver.execute_script("arguments[0].click();", send_btn)
            logging.info("[SEND] ✓ Clicked 'Send invitation' (aria-label match).")
            self.human_delay(3, 5)
            return "success"
        except TimeoutException:
            logging.warning("[SEND] button[aria-label='Send invitation'] not found, trying fallbacks...")

        # Fallback 1: button whose visible text is exactly "Send"
        all_buttons = self.driver.find_elements(By.TAG_NAME, "button")
        logging.info(f"[SEND] Scanning {len(all_buttons)} buttons for Send...")
        send_btn = None
        for btn in all_buttons:
            try:
                if not btn.is_displayed():
                    continue
                label = (btn.get_attribute("aria-label") or "").strip()
                text  = btn.text.strip()
                logging.info(f"  btn aria-label='{label}' text='{text}'")
                if text.lower() in ("send", "send now", "send invitation") or \
                   label.lower() in ("send", "send now", "send invitation"):
                    send_btn = btn
                    break
                # Partial — avoid "Send a message" etc.
                if "send" in text.lower() and "message" not in text.lower():
                    send_btn = send_btn or btn
            except Exception:
                continue

        if send_btn:
            self.driver.execute_script("arguments[0].click();", send_btn)
            logging.info(f"[SEND] ✓ Clicked Send button: '{send_btn.text.strip()}'")
            self.human_delay(3, 5)
            return "success"

        # Fallback 2: any clickable element whose text is "Send" or "Send invitation"
        try:
            send_el = self.driver.find_element(
                By.XPATH,
                "//*[self::button or self::a]"
                "[normalize-space(.)='Send' or normalize-space(.)='Send invitation']"
            )
            if send_el.is_displayed():
                self.driver.execute_script("arguments[0].click();", send_el)
                logging.info("[SEND] ✓ Clicked Send (XPath fallback).")
                self.human_delay(3, 5)
                return "success"
        except NoSuchElementException:
            pass

        logging.error("[SEND] Could not find Send button by any method.")
        try:
            logging.debug(f"Page source snippet:\n{self.driver.page_source[:3000]}")
        except Exception:
            pass
        return "failed"
    
    def process_csv_profiles(self, csv_file, note_template, max_requests=20):
        try:
            logging.info(f"Reading profiles from {csv_file}...")
            df = pd.read_csv(csv_file)
            
            if 'profile_url' not in df.columns:
                logging.error("CSV must contain 'profile_url' column!")
                return None
            
            for col in ['connection_date', 'connection_note', 'connection_status']:
                if col not in df.columns:
                    df[col] = ''
            
            df['connection_date'] = df['connection_date'].astype(str).str.strip().replace('nan', '')
            df['connection_note'] = df['connection_note'].astype(str).str.strip().replace('nan', '')
            df['connection_status'] = df['connection_status'].astype(str).str.strip().replace('nan', '')
            
            unprocessed_mask = (
                (df['connection_date'] == '') & 
                (df['connection_note'] == '') & 
                (df['connection_status'] == '')
            )
            
            processed_count = (~unprocessed_mask).sum()
            total_profiles = len(df)
            remaining_profiles = unprocessed_mask.sum()
            
            logging.info(f"Total: {total_profiles} | Already processed: {processed_count} | Remaining: {remaining_profiles}")
            
            if remaining_profiles == 0:
                logging.info("All profiles have been processed!")
                return df
            
            successful = failed = skipped = connect_not_found = requests_sent = 0
            
            for idx, row in df.iterrows():
                if not unprocessed_mask[idx]:
                    continue
                
                if requests_sent >= max_requests:
                    skipped = remaining_profiles - requests_sent
                    break
                
                profile_url = row['profile_url']
                logging.info(f"\n{'='*70}")
                logging.info(f"Profile {idx + 1}/{total_profiles} | Run: {requests_sent + 1}/{min(max_requests, remaining_profiles)}")
                logging.info(f"{'='*70}")
                
                personalized_note = self.create_personalized_note(row.to_dict(), note_template)
                logging.info(f"Note preview:\n{personalized_note}\n")
                
                result = self.send_connection_request(profile_url, personalized_note)
                
                df.at[idx, 'connection_date'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                df.at[idx, 'connection_note'] = personalized_note
                df.at[idx, 'connection_status'] = result
                
                if result == "success":
                    successful += 1
                elif result == "connect_not_found":
                    connect_not_found += 1
                else:
                    failed += 1
                
                requests_sent += 1
                df.to_csv(csv_file, index=False, encoding='utf-8')
                logging.info(f"Progress saved to {csv_file}")
                
                if requests_sent % 5 == 0 and requests_sent < remaining_profiles:
                    logging.info("Taking a longer break to avoid detection...")
                    self.human_delay(30, 60)
                elif requests_sent < remaining_profiles:
                    self.human_delay(5, 10)
            
            logging.info(f"\n{'='*70}")
            logging.info(f"SUMMARY: ✓ Success={successful} | ⊘ Not found={connect_not_found} | ✗ Failed={failed} | Skipped={skipped}")
            logging.info(f"{'='*70}\n")
            
            return df
            
        except Exception as e:
            logging.error(f"Error processing CSV: {str(e)}")
            import traceback
            traceback.print_exc()
            return None
    
    def close(self):
        if self.driver:
            logging.info("Closing browser in 5 seconds...")
            time.sleep(5)
            self.driver.quit()


def main():
    EMAIL = LINKEDIN_USERNAME
    PASSWORD = LINKEDIN_PASSWORD
    
    INPUT_CSV = "linkedin_profiles/extracted_profiles_keydata_04-07-26-09.csv"
    
    MAX_REQUESTS = 200
    
#     NOTE_TEMPLATE = """Hi {name}, 

# I discovered your product on Product Hunt and genuinely loved what you're building. 

# I'm currently working on an AI-driven content curation and creation platform and would love to connect and exchange ideas.

# Looking forward to connecting!
# Cheers,
# Jay
# (www.snoolink.com)
# """

    NOTE_TEMPLATE = """Hi {name},

I saw you’re hiring for data roles at {about} and wanted to reach out.

I’m a Data Engineer with 5 years of experience building scalable data pipelines across cloud and modern data stacks. I’d love to connect and see if my background aligns with your team’s needs.

I’m currently exploring new opportunities and would love to connect and learn more about the roles you’re hiring for, as well as how my experience could align with your team’s needs.

-Jay  
"""

    
    bot = LinkedInConnectionBot(EMAIL, PASSWORD)
    
    try:
        bot.setup_driver()
        
        if bot.login():
            results = bot.process_csv_profiles(
                csv_file=INPUT_CSV,
                note_template=NOTE_TEMPLATE,
                max_requests=MAX_REQUESTS
            )
            if results is not None:
                logging.info("✓ Process completed successfully!")
        else:
            logging.error("✗ Login failed.")
        
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