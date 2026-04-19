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
from selenium.webdriver.common.keys import Keys
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

    # ------------------------------------------------------------------ #
    # DEBUG HELPER                                                         #
    # ------------------------------------------------------------------ #
    def _dump_all_buttons(self):
        """
        Prints every visible button inside <main> with id, class,
        aria-label, and text. Use when selectors break to re-identify
        the correct More button attributes from the log.
        """
        logging.info("=== BUTTON DUMP (all visible buttons in <main>) ===")
        buttons = self.driver.find_elements(By.XPATH, "//main//button")
        for i, btn in enumerate(buttons):
            try:
                if not btn.is_displayed():
                    continue
                logging.info(
                    f"  [{i}] id='{btn.get_attribute('id')}' "
                    f"aria-label='{btn.get_attribute('aria-label')}' "
                    f"aria-expanded='{btn.get_attribute('aria-expanded')}' "
                    f"class='{(btn.get_attribute('class') or '')[:80]}' "
                    f"text='{btn.text.strip()[:60]}'"
                )
            except Exception:
                continue
        logging.info("=== END BUTTON DUMP ===")

    # ------------------------------------------------------------------ #
    # RECOMMENDATION SECTION GUARD                                         #
    # ------------------------------------------------------------------ #
    def _is_in_recommendation_section(self, element):
        """Return True if element lives inside a sidebar / recommendation section."""
        try:
            script = """
                var el = arguments[0];
                for (var depth = 0; el && depth < 12; depth++) {
                    var text = (
                        el.getAttribute('aria-label') ||
                        el.getAttribute('data-test-id') ||
                        el.id || ''
                    ).toLowerCase();
                    if (
                        text.includes('people you may know') ||
                        text.includes('more profiles') ||
                        text.includes('people also viewed')
                    ) { return true; }
                    var cls = (el.className || '').toLowerCase();
                    if (
                        cls.includes('aside') ||
                        cls.includes('scaffold-layout__aside')
                    ) { return true; }
                    el = el.parentElement;
                }
                return false;
            """
            return self.driver.execute_script(script, element)
        except Exception:
            return False

    # ------------------------------------------------------------------ #
    # MORE BUTTON DETECTION                                                #
    # ------------------------------------------------------------------ #
    def _find_more_button(self):
        """
        Locate the 'More actions' trigger button.

        Confirmed HTML from live page:
          <button aria-expanded="false"
                  aria-label="More actions"
                  id="ember73-profile-overflow-action"
                  class="artdeco-dropdown__trigger artdeco-dropdown__trigger--placement-bottom
                         ember-view MfwEeGimHySKbgcUtkemOkVzjeQMyBJWOHI
                         artdeco-button artdeco-button--secondary artdeco-button--muted
                         artdeco-button--2"
                  type="button">
            <span>More</span>
          </button>
        """
        time.sleep(1.5)

        # S1: id ends with '-profile-overflow-action'  ← confirmed pattern
        for btn in self.driver.find_elements(
            By.CSS_SELECTOR, "button[id$='-profile-overflow-action']"
        ):
            try:
                if btn.is_displayed() and not self._is_in_recommendation_section(btn):
                    logging.info(f"[More-S1] Found via id suffix: id='{btn.get_attribute('id')}'")
                    return btn
            except Exception:
                continue

        # S2: aria-label="More actions" scoped to <main>  ← confirmed attribute
        for btn in self.driver.find_elements(
            By.XPATH, "//main//button[@aria-label='More actions']"
        ):
            try:
                if btn.is_displayed() and not self._is_in_recommendation_section(btn):
                    logging.info("[More-S2] Found via aria-label='More actions'")
                    return btn
            except Exception:
                continue

        # S3: artdeco-dropdown__trigger button with "More" span  ← confirmed classes
        for btn in self.driver.find_elements(
            By.CSS_SELECTOR, "button.artdeco-dropdown__trigger"
        ):
            try:
                if not btn.is_displayed():
                    continue
                spans = btn.find_elements(By.TAG_NAME, "span")
                visible_texts = [s.text.strip() for s in spans if s.text.strip()]
                if "More" in visible_texts and not self._is_in_recommendation_section(btn):
                    logging.info("[More-S3] Found via artdeco-dropdown__trigger + 'More' span")
                    return btn
            except Exception:
                continue

        # S4: Any <main> button whose direct span text is "More"
        for btn in self.driver.find_elements(
            By.XPATH,
            "//main//button[.//span[normalize-space(text())='More']]"
        ):
            try:
                if btn.is_displayed() and not self._is_in_recommendation_section(btn):
                    logging.info("[More-S4] Found via XPath span text='More'")
                    return btn
            except Exception:
                continue

        # S5: JavaScript full-DOM scan — survives any class or id rename
        logging.info("[More-S5] Trying JS full-DOM scan...")
        try:
            result = self.driver.execute_script("""
                var buttons = document.querySelectorAll('button');
                for (var i = 0; i < buttons.length; i++) {
                    var btn = buttons[i];
                    if (!btn.offsetParent) continue;
                    var label = (btn.getAttribute('aria-label') || '').trim();
                    var spans = btn.querySelectorAll('span');
                    var spanText = '';
                    for (var j = 0; j < spans.length; j++) {
                        var t = spans[j].textContent.trim();
                        if (t) { spanText = t; break; }
                    }
                    if (label === 'More actions' || spanText === 'More') {
                        var el = btn;
                        var inSidebar = false;
                        for (var d = 0; el && d < 10; d++) {
                            var cls = (el.className || '').toLowerCase();
                            if (cls.includes('aside') ||
                                cls.includes('scaffold-layout__aside')) {
                                inSidebar = true; break;
                            }
                            el = el.parentElement;
                        }
                        if (!inSidebar) return btn;
                    }
                }
                return null;
            """)
            if result:
                logging.info("[More-S5] JS scan found More button")
                return result
        except Exception as e:
            logging.warning(f"[More-S5] JS scan failed: {e}")

        # Nothing worked — dump button inventory so we can fix selectors
        self._dump_all_buttons()
        logging.warning("[More] No More button found by any method.")
        return None

    # ------------------------------------------------------------------ #
    # CONNECT BUTTON DISCOVERY                                             #
    # ------------------------------------------------------------------ #
    def discover_connect_button(self):
        """
        Find the Connect button via two paths:

        PATH A — Direct button in the profile action bar (when visible):
            <button aria-label="Invite X to connect" ...>
              <span class="artdeco-button__text">Connect</span>
            </button>

        PATH B — Inside the 'More actions' dropdown (confirmed structure):
            Dropdown trigger:
              <button id="ember73-profile-overflow-action"
                      aria-label="More actions" aria-expanded="false" ...>
                <span>More</span>
              </button>
            Dropdown container (always present in DOM, hidden via aria-hidden):
              <div class="artdeco-dropdown__content artdeco-dropdown--is-dropdown-element ...">
                <div class="artdeco-dropdown__content-inner">
                  <ul>
                    <li>
                      <div role="button"
                           aria-label="Invite Cameron Khani to connect"
                           class="artdeco-dropdown__item artdeco-dropdown__item--is-dropdown ...">
                        <span>Connect</span>
                      </div>
                    </li>
                  </ul>
                </div>
              </div>

        Returns (element, method_string) or (None, None).
        """
        try:
            self.wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "main")))
        except TimeoutException:
            pass
        time.sleep(2)

        # ---------------------------------------------------------------- #
        # PATH A — Direct Connect button                                    #
        # ---------------------------------------------------------------- #

        # A1: button whose aria-label contains "invite" + "connect"
        for btn in self.driver.find_elements(By.CSS_SELECTOR, "button.artdeco-button"):
            try:
                if not btn.is_displayed():
                    continue
                aria = (btn.get_attribute("aria-label") or "").lower()
                if "invite" in aria and "connect" in aria:
                    if self._is_in_recommendation_section(btn):
                        continue
                    logging.info(f"[A1] Direct Connect button — aria-label='{aria}'")
                    return btn, "direct_aria"
            except Exception:
                continue

        # A2: artdeco-button whose __text span is exactly "Connect"
        for btn in self.driver.find_elements(By.CSS_SELECTOR, "button.artdeco-button"):
            try:
                if not btn.is_displayed():
                    continue
                try:
                    span_text = btn.find_element(
                        By.CSS_SELECTOR, "span.artdeco-button__text"
                    ).text.strip()
                except NoSuchElementException:
                    span_text = btn.text.strip()

                if span_text == "Connect":
                    if self._is_in_recommendation_section(btn):
                        continue
                    logging.info("[A2] Direct Connect button — span text='Connect'")
                    return btn, "direct_span_text"
            except Exception:
                continue

        # ---------------------------------------------------------------- #
        # PATH B — 'More actions' dropdown                                  #
        # ---------------------------------------------------------------- #
        logging.info("[B] Direct Connect not found — opening 'More actions' dropdown...")

        more_btn = self._find_more_button()
        if more_btn is None:
            logging.warning("[B] 'More actions' button not found")
            return None, None

        # Click to open the dropdown
        try:
            self.driver.execute_script(
                "arguments[0].scrollIntoView({block:'center'});", more_btn
            )
            time.sleep(0.5)
            self.driver.execute_script("arguments[0].click();", more_btn)
            logging.info("[B] Clicked 'More actions' — waiting for dropdown to open...")

            # Wait for aria-expanded="true" on the More button
            WebDriverWait(self.driver, 6).until(
                lambda d: more_btn.get_attribute("aria-expanded") == "true"
            )
            time.sleep(0.8)
        except Exception as e:
            logging.error(f"[B] Could not open dropdown: {e}")
            return None, None

        # ---------------------------------------------------------------- #
        # Scan the dropdown for the Connect item                            #
        #                                                                   #
        # Confirmed HTML of the Connect item:                               #
        #   <div role="button"                                              #
        #        aria-label="Invite Cameron Khani to connect"               #
        #        class="artdeco-dropdown__item                              #
        #               artdeco-dropdown__item--is-dropdown ...">           #
        #     <span class="...">Connect</span>                              #
        #   </div>                                                          #
        #                                                                   #
        # NOTE: the dropdown container uses aria-hidden="true" when        #
        # closed and removes it when open. We look for items inside the    #
        # parent artdeco-dropdown wrapper of our More button.               #
        # ---------------------------------------------------------------- #

        # Find the artdeco-dropdown wrapper that contains the More button
        try:
            dropdown_wrapper = self.driver.execute_script(
                """
                var btn = arguments[0];
                var el = btn.parentElement;
                for (var d = 0; el && d < 6; d++) {
                    if ((el.className || '').includes('artdeco-dropdown')) {
                        return el;
                    }
                    el = el.parentElement;
                }
                return null;
                """,
                more_btn
            )
        except Exception:
            dropdown_wrapper = None

        # Search within the wrapper first, then fall back to full page
        search_roots = []
        if dropdown_wrapper:
            search_roots.append(dropdown_wrapper)
        search_roots.append(self.driver)  # full-page fallback

        dropdown_item_selectors = [
            "div.artdeco-dropdown__item[role='button']",
            "div[role='button'].artdeco-dropdown__item--is-dropdown",
            "li div[role='button']",
            "[role='menuitem']",
        ]

        for root in search_roots:
            for selector in dropdown_item_selectors:
                try:
                    items = root.find_elements(By.CSS_SELECTOR, selector)
                except Exception:
                    continue

                for item in items:
                    try:
                        aria = (item.get_attribute("aria-label") or "").lower()
                        # Get the visible text from the flex span (confirmed structure)
                        try:
                            text = item.find_element(
                                By.CSS_SELECTOR, "span.display-flex"
                            ).text.strip()
                        except NoSuchElementException:
                            text = item.text.strip()

                        logging.info(
                            f"  [dropdown scan | {selector}] "
                            f"aria='{aria}' text='{text}'"
                        )

                        if ("invite" in aria and "connect" in aria) or text == "Connect":
                            logging.info(
                                f"[B] Connect item found — "
                                f"aria='{aria}' text='{text}'"
                            )
                            return item, "dropdown_item"
                    except Exception:
                        continue

        # Dropdown open but Connect item not found — close cleanly and give up
        logging.warning("[B] Connect not found inside dropdown")
        try:
            self.driver.find_element(By.TAG_NAME, "body").send_keys(Keys.ESCAPE)
        except Exception:
            pass

        return None, None

    # ------------------------------------------------------------------ #
    # PERSONALIZED NOTE BUILDER                                            #
    # ------------------------------------------------------------------ #
    def create_personalized_note(self, profile_data, note_template):
        """
        Build the connection note using 'name' and 'about' from the CSV row.
        Falls back gracefully if columns are missing or empty.
        """
        try:
            full_name = str(profile_data.get('name', '') or '').strip()
            name = full_name.split()[0] if full_name else 'there'

            about = str(profile_data.get('about', '') or '').strip()
            if not about or about.lower() == 'nan':
                current_position = str(profile_data.get('current_position', '') or '').strip()
                current_company  = str(profile_data.get('current_company', '') or '').strip()
                headline         = str(profile_data.get('headline', '') or '').strip()

                if current_position and current_company:
                    about = f"{current_position} at {current_company}"
                elif headline:
                    about = headline
                else:
                    about = "your organization"

            personalized_note = note_template.format(
                name=name,
                about=about,
                headline=str(profile_data.get('headline', '') or '').strip(),
                current_position=str(profile_data.get('current_position', '') or '').strip(),
                current_company=str(profile_data.get('current_company', '') or '').strip(),
                location=str(profile_data.get('location', '') or '').strip(),
                connections=str(profile_data.get('connections', '') or '').strip(),
            )

            if len(personalized_note) > 300:
                logging.warning(f"Note too long ({len(personalized_note)} chars), truncating...")
                personalized_note = personalized_note[:297] + "..."

            return personalized_note

        except Exception as e:
            logging.error(f"Error creating personalized note: {e}")
            return note_template

    # ------------------------------------------------------------------ #
    # SEND CONNECTION REQUEST                                              #
    # ------------------------------------------------------------------ #
    def send_connection_request(self, profile_url, note=None):
        """
        Full flow:
          1. Load the profile page
          2. Discover and click Connect (direct or via More dropdown)
          3. Handle the modal — add note, click Send
        """
        try:
            logging.info(f"Visiting profile: {profile_url}")
            self.driver.get(profile_url)
            self.human_delay(3, 5)

            # STEP 1 — find and click Connect
            connect_el, method = self.discover_connect_button()

            if connect_el is None:
                logging.warning(f"[SEND] Connect button not found for {profile_url}")
                return "connect_not_found"

            logging.info(f"[SEND] Clicking Connect (method={method})")
            self.driver.execute_script(
                "arguments[0].scrollIntoView({block:'center'});", connect_el
            )
            time.sleep(0.5)
            self.driver.execute_script("arguments[0].click();", connect_el)
            self.human_delay(2, 3)

            # STEP 2 — wait for modal
            try:
                modal = WebDriverWait(self.driver, 8).until(
                    EC.presence_of_element_located(
                        (By.CSS_SELECTOR, "[role='dialog'], [aria-modal='true']")
                    )
                )
                logging.info("[SEND] Modal detected.")
            except TimeoutException:
                logging.warning("[SEND] No modal appeared — assuming already sent.")
                return "success"

            modal_buttons = modal.find_elements(By.TAG_NAME, "button")
            logging.info(f"[SEND] Modal has {len(modal_buttons)} buttons:")
            for i, b in enumerate(modal_buttons):
                try:
                    logging.info(
                        f"  modal_btn[{i}] label='{b.get_attribute('aria-label')}' "
                        f"text='{b.text.strip()}'"
                    )
                except Exception:
                    pass

            # STEP 3 — add note (optional)
            if note:
                add_note_clicked = False

                try:
                    add_note_btn = WebDriverWait(self.driver, 5).until(
                        EC.element_to_be_clickable(
                            (By.CSS_SELECTOR, "button[aria-label='Add a note']")
                        )
                    )
                    self.driver.execute_script("arguments[0].click();", add_note_btn)
                    logging.info("[SEND] Clicked 'Add a note' (aria-label match).")
                    self.human_delay(0.8, 1.2)
                    add_note_clicked = True
                except TimeoutException:
                    for btn in modal_buttons:
                        try:
                            lbl = (btn.get_attribute("aria-label") or "").lower()
                            txt = btn.text.strip().lower()
                            if "add a note" in lbl or "add a note" in txt:
                                self.driver.execute_script("arguments[0].click();", btn)
                                logging.info("[SEND] Clicked 'Add a note' (text scan).")
                                self.human_delay(0.8, 1.2)
                                add_note_clicked = True
                                break
                        except Exception:
                            continue

                if add_note_clicked:
                    try:
                        textarea = WebDriverWait(self.driver, 8).until(
                            EC.presence_of_element_located((By.CSS_SELECTOR, "textarea"))
                        )
                        textarea.clear()
                        textarea.send_keys(note)
                        logging.info(f"[SEND] Note entered ({len(note)} chars).")
                        self.human_delay(0.8, 1.2)
                    except TimeoutException:
                        logging.warning("[SEND] Textarea not found after clicking 'Add a note'.")
                else:
                    logging.warning("[SEND] 'Add a note' not found — sending without note.")

            # STEP 4 — click Send
            return self._click_send_button()

        except Exception as e:
            logging.error(f"[SEND] Error for {profile_url}: {e}")
            import traceback
            traceback.print_exc()
            return "failed"

    # ------------------------------------------------------------------ #
    # SEND BUTTON CLICK                                                    #
    # ------------------------------------------------------------------ #
    def _click_send_button(self):
        """Find and click the Send invitation button. Returns 'success' or 'failed'."""

        # Primary: aria-label='Send invitation'
        try:
            send_btn = WebDriverWait(self.driver, 8).until(
                EC.element_to_be_clickable(
                    (By.CSS_SELECTOR, "button[aria-label='Send invitation']")
                )
            )
            self.driver.execute_script("arguments[0].click();", send_btn)
            logging.info("[SEND] ✓ Clicked 'Send invitation' (aria-label).")
            self.human_delay(3, 5)
            return "success"
        except TimeoutException:
            logging.warning("[SEND] aria-label='Send invitation' not found, trying fallbacks...")

        # Fallback: scan all visible buttons for send-like text
        all_buttons = self.driver.find_elements(By.TAG_NAME, "button")
        logging.info(f"[SEND] Scanning {len(all_buttons)} buttons for Send...")
        send_btn = None
        for btn in all_buttons:
            try:
                if not btn.is_displayed():
                    continue
                label = (btn.get_attribute("aria-label") or "").strip().lower()
                text  = btn.text.strip().lower()
                logging.info(f"  btn aria-label='{label}' text='{text}'")
                if text in ("send", "send now", "send invitation") or \
                   label in ("send", "send now", "send invitation"):
                    send_btn = btn
                    break
                if "send" in text and "message" not in text:
                    send_btn = send_btn or btn
            except Exception:
                continue

        if send_btn:
            self.driver.execute_script("arguments[0].click();", send_btn)
            logging.info(f"[SEND] ✓ Clicked Send: '{send_btn.text.strip()}'")
            self.human_delay(3, 5)
            return "success"

        # XPath fallback
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
        return "failed"

    # ------------------------------------------------------------------ #
    # CSV PROCESSING                                                       #
    # ------------------------------------------------------------------ #
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

            df['connection_date']   = df['connection_date'].astype(str).str.strip().replace('nan', '')
            df['connection_note']   = df['connection_note'].astype(str).str.strip().replace('nan', '')
            df['connection_status'] = df['connection_status'].astype(str).str.strip().replace('nan', '')

            unprocessed_mask = (
                (df['connection_date'] == '') &
                (df['connection_note'] == '') &
                (df['connection_status'] == '')
            )

            processed_count    = (~unprocessed_mask).sum()
            total_profiles     = len(df)
            remaining_profiles = unprocessed_mask.sum()

            logging.info(
                f"Total: {total_profiles} | Already processed: {processed_count} "
                f"| Remaining: {remaining_profiles}"
            )

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
                logging.info(
                    f"Profile {idx + 1}/{total_profiles} | "
                    f"Run: {requests_sent + 1}/{min(max_requests, remaining_profiles)}"
                )
                logging.info(f"{'='*70}")

                personalized_note = self.create_personalized_note(row.to_dict(), note_template)
                logging.info(f"Note preview:\n{personalized_note}\n")

                result = self.send_connection_request(profile_url, personalized_note)

                df.at[idx, 'connection_date']   = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                df.at[idx, 'connection_note']   = personalized_note
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
            logging.info(
                f"SUMMARY: ✓ Success={successful} | ⊘ Not found={connect_not_found} "
                f"| ✗ Failed={failed} | Skipped={skipped}"
            )
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


# ------------------------------------------------------------------ #
# ENTRY POINT                                                          #
# ------------------------------------------------------------------ #
def main():
    EMAIL    = LINKEDIN_USERNAME
    PASSWORD = LINKEDIN_PASSWORD

    INPUT_CSV    = "linkedin_profiles/extracted_profiles_keydata_04-07-26-12.csv"
    MAX_REQUESTS = 200

    NOTE_TEMPLATE = """Hi {name},

I saw you're hiring for data roles at {about} and wanted to reach out.

I'm a Data Engineer with 5 years of experience building scalable data pipelines across cloud and modern data stacks. I'd love to connect and see if my background aligns with your team's needs.

I'm currently exploring new opportunities and would love to connect and learn more about the roles you're hiring for, as well as how my experience could align with your team's needs.

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