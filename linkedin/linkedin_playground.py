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
from datetime import datetime
from creds import LINKEDIN_USERNAME, LINKEDIN_PASSWORD


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
        SUCCESS_URLS = ("feed", "mynetwork", "jobs", "messaging", "notifications", "in/", "linkedin.com/home")
        FAILURE_URLS = ("login", "authwall", "signup", "uas/login")

        try:
            self.driver.get('https://www.linkedin.com/login')
            email_field = self.wait.until(EC.presence_of_element_located((By.ID, 'username')))
            email_field.clear()
            email_field.send_keys(self.email)

            password_field = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.ID, 'password'))
            )
            password_field.clear()
            password_field.send_keys(self.password)

            # JS click avoids any overlay issues
            submit = self.driver.find_element(By.CSS_SELECTOR, 'button[type="submit"]')
            self.driver.execute_script("arguments[0].click();", submit)

            # Wait up to 15s for the URL to leave the login page
            try:
                WebDriverWait(self.driver, 15).until(
                    lambda d: not any(f in d.current_url for f in FAILURE_URLS)
                )
            except TimeoutException:
                print(f"Login may have failed — still on: {self.driver.current_url}")
                return False

            # Handle verification / CAPTCHA checkpoint
            if "checkpoint" in self.driver.current_url or "challenge" in self.driver.current_url:
                print("LinkedIn requires verification. Complete it in the browser, then press Enter...")
                input()
                try:
                    WebDriverWait(self.driver, 60).until(
                        lambda d: "checkpoint" not in d.current_url and "challenge" not in d.current_url
                    )
                except TimeoutException:
                    print(f"Still on checkpoint page: {self.driver.current_url}")
                    return False
                time.sleep(3)  # let page fully settle

            current = self.driver.current_url
            if any(s in current for s in SUCCESS_URLS):
                print(f"Login successful: {current}")
                return True

            # Still on linkedin.com and not on a login/auth page — good enough
            if "linkedin.com" in current and not any(f in current for f in FAILURE_URLS):
                print(f"Login likely successful (landing page): {current}")
                return True

            print(f"Login failed — unexpected URL: {current}")
            return False

        except Exception:
            import traceback
            traceback.print_exc()
            return False

    def human_delay(self, min_seconds=2, max_seconds=5):
        time.sleep(random.uniform(min_seconds, max_seconds))

    def _is_in_sidebar(self, element):
        """Return True if the element lives in the aside/sidebar (recommendations)."""
        try:
            return self.driver.execute_script("""
                var el = arguments[0];
                for (var i = 0; i < 12; i++) {
                    if (!el) return false;
                    var tag = el.tagName ? el.tagName.toLowerCase() : '';
                    if (tag === 'aside') return true;
                    var cls = (el.className || '').toLowerCase();
                    if (cls.includes('aside') || cls.includes('scaffold-layout__aside')) return true;
                    el = el.parentElement;
                }
                return false;
            """, element)
        except Exception:
            return False

    def _find_connect_button_direct(self):
        """
        Find the Connect button in the profile actions bar.

        Target button shape (from live LinkedIn HTML):
          <button aria-label="Invite X to connect"
                  class="artdeco-button artdeco-button--2 artdeco-button--primary ...">
            <span class="artdeco-button__text">Connect</span>
          </button>

        Strategies (tried in order, all skip sidebar elements):
          1. PRIMARY button with "to connect" in aria-label  ← most precise
          2. Any button with "to connect" in aria-label
          3. PRIMARY button whose span text is exactly "Connect"
          4. Any button whose span text is exactly "Connect"
        """

        def valid(el):
            try:
                return el.is_displayed() and not self._is_in_sidebar(el)
            except Exception:
                return False

        # Strategy 1: artdeco-button--primary + "to connect" aria-label (exact shape from HTML)
        for el in self.driver.find_elements(
            By.XPATH,
            "//button["
            "contains(@class,'artdeco-button--primary') and "
            "contains(translate(@aria-label,'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'),'to connect')"
            "]"
        ):
            if valid(el):
                return el

        # Strategy 2: any button with "to connect" in aria-label (no class filter)
        for el in self.driver.find_elements(
            By.XPATH,
            "//button[contains(translate(@aria-label,'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'),'to connect')]"
        ):
            if valid(el):
                return el

        # Strategy 3: artdeco-button--primary whose span text is "Connect"
        for el in self.driver.find_elements(
            By.XPATH,
            "//button["
            "contains(@class,'artdeco-button--primary') and "
            ".//span[normalize-space(text())='Connect']"
            "]"
        ):
            if valid(el):
                return el

        # Strategy 4: any button whose span text is "Connect"
        for el in self.driver.find_elements(
            By.XPATH,
            "//button[.//span[normalize-space(text())='Connect']]"
        ):
            if valid(el):
                return el

        return None

    def _open_more_actions_and_find_connect(self):
        """
        Fallback: the Connect option is hidden inside the 'More actions' dropdown.
        From the real HTML the dropdown items are <div role="button"> inside <li> tags,
        NOT <button> elements — so we target those specifically.

        The dropdown trigger is:
          <button aria-label="More actions" class="artdeco-dropdown__trigger ...">
        After clicking it the content div loses aria-hidden="true".
        Connect inside the dropdown would be a <div role="button"> or <li> with
        "Connect" text (same pattern as "Follow", "Save to PDF" etc. in the HTML).
        """
        # Find the More actions trigger that is NOT in the sidebar
        more_btn = None
        for btn in self.driver.find_elements(
            By.XPATH, "//button[@aria-label='More actions']"
        ):
            try:
                if btn.is_displayed() and not self._is_in_sidebar(btn):
                    more_btn = btn
                    break
            except Exception:
                continue

        # Fallback label scan
        if more_btn is None:
            for btn in self.driver.find_elements(By.TAG_NAME, "button"):
                try:
                    if not btn.is_displayed():
                        continue
                    label = (btn.get_attribute("aria-label") or "").lower()
                    if "more actions" in label and not self._is_in_sidebar(btn):
                        more_btn = btn
                        break
                except Exception:
                    continue

        if more_btn is None:
            return None

        try:
            self.driver.execute_script("arguments[0].scrollIntoView({block:'center'});", more_btn)
            time.sleep(0.4)
            self.driver.execute_script("arguments[0].click();", more_btn)
            time.sleep(1.5)
        except Exception:
            return None

        # The dropdown is the sibling div.artdeco-dropdown__content inside the same
        # artdeco-dropdown wrapper. Items are <div role="button"> or <li> children.
        # We look for any item whose text or aria-label contains "connect".
        dropdown_item_xpaths = [
            # <div role="button" aria-label="Invite X to connect"> (direct aria-label match)
            "//*[@role='button'][contains(translate(@aria-label,'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'), 'to connect')]",
            # <div role="button"> containing a span with "Connect" text
            "//*[@role='button'][.//span[normalize-space(text())='Connect']]",
            # <li> containing "Connect" span (in case role is on the li)
            "//li[.//span[normalize-space(text())='Connect']]",
            # artdeco dropdown item class with Connect text
            "//*[contains(@class,'artdeco-dropdown__item')][.//span[normalize-space(text())='Connect']]",
        ]
        for xpath in dropdown_item_xpaths:
            for el in self.driver.find_elements(By.XPATH, xpath):
                try:
                    if el.is_displayed():
                        return el
                except Exception:
                    continue

        # Last resort: any newly visible button with "to connect" in aria-label
        for el in self.driver.find_elements(
            By.XPATH,
            "//button[contains(translate(@aria-label,'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'), 'to connect')]"
        ):
            try:
                if el.is_displayed():
                    return el
            except Exception:
                continue

        # Close dropdown and give up
        try:
            from selenium.webdriver.common.keys import Keys
            self.driver.find_element(By.TAG_NAME, "body").send_keys(Keys.ESCAPE)
        except Exception:
            pass

        return None

    def discover_connect_button(self):
        """
        Returns the Connect element or None.
        Waits for the profile to load, then tries direct detection first,
        falling back to the More actions dropdown.
        """
        try:
            self.wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "main")))
        except TimeoutException:
            pass
        time.sleep(2)

        el = self._find_connect_button_direct()
        if el:
            return el

        return self._open_more_actions_and_find_connect()

    def _click_send_button(self):
        """Click the Send invitation button. Returns 'success' or 'failed'."""
        # Primary: exact aria-label match
        try:
            send_btn = WebDriverWait(self.driver, 8).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, "button[aria-label='Send invitation']"))
            )
            self.driver.execute_script("arguments[0].click();", send_btn)
            self.human_delay(3, 5)
            return "success"
        except TimeoutException:
            pass

        # Fallback: scan all visible buttons for send-like text
        send_btn = None
        for btn in self.driver.find_elements(By.TAG_NAME, "button"):
            try:
                if not btn.is_displayed():
                    continue
                label = (btn.get_attribute("aria-label") or "").strip().lower()
                text = btn.text.strip().lower()
                if text in ("send", "send now", "send invitation") or label in ("send", "send now", "send invitation"):
                    send_btn = btn
                    break
                if "send" in text and "message" not in text:
                    send_btn = send_btn or btn
            except Exception:
                continue

        if send_btn:
            self.driver.execute_script("arguments[0].click();", send_btn)
            self.human_delay(3, 5)
            return "success"

        # XPath fallback
        try:
            el = self.driver.find_element(
                By.XPATH,
                "//*[self::button or self::a][normalize-space(.)='Send' or normalize-space(.)='Send invitation']"
            )
            if el.is_displayed():
                self.driver.execute_script("arguments[0].click();", el)
                self.human_delay(3, 5)
                return "success"
        except NoSuchElementException:
            pass

        return "failed"

    def send_connection_request(self, profile_url, note=None):
        """
        Visit a profile URL and send a connection request with an optional note.

        Flow:
          1. Find and click the Connect button (button with aria-label "Invite X to connect")
          2. After clicking, handle either:
             A. Navigation to a /preload/custom-invite/ page (dedicated invite page)
             B. A modal dialog opening in place
          3. Optionally add a note, then click Send.
        """
        try:
            self.driver.get(profile_url)
            self.human_delay(3, 5)

            connect_el = self.discover_connect_button()
            if connect_el is None:
                return "connect_not_found"

            # Check if it's an <a> with a custom-invite href — navigate directly
            tag = connect_el.tag_name.lower()
            href = connect_el.get_attribute("href") or ""

            self.driver.execute_script("arguments[0].scrollIntoView({block:'center'});", connect_el)
            time.sleep(0.4)

            if tag == "a" and "/preload/custom-invite/" in href:
                self.driver.get(href)
            else:
                self.driver.execute_script("arguments[0].click();", connect_el)

            self.human_delay(2, 3)

            current_url = self.driver.current_url
            on_invite_page = "custom-invite" in current_url or "preload" in current_url

            if on_invite_page:
                # --- Dedicated invite page ---
                if note:
                    try:
                        add_note_btn = WebDriverWait(self.driver, 8).until(
                            EC.element_to_be_clickable((By.CSS_SELECTOR, "button[aria-label='Add a note']"))
                        )
                        self.driver.execute_script("arguments[0].click();", add_note_btn)
                        self.human_delay(0.8, 1.2)

                        textarea = WebDriverWait(self.driver, 8).until(
                            EC.presence_of_element_located((By.CSS_SELECTOR, "textarea"))
                        )
                        textarea.clear()
                        textarea.send_keys(note)
                        self.human_delay(0.8, 1.2)
                    except TimeoutException:
                        pass  # Send without note

                return self._click_send_button()

            else:
                # --- Modal flow ---
                try:
                    modal = WebDriverWait(self.driver, 6).until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, "[role='dialog'], [aria-modal='true']"))
                    )
                except TimeoutException:
                    # No modal and not on invite page — may have sent directly (no-note fast path)
                    return "success"

                if note:
                    for btn in modal.find_elements(By.TAG_NAME, "button"):
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
                                self.human_delay(0.8, 1.2)
                                break
                        except Exception:
                            continue

                return self._click_send_button()

        except Exception as e:
            import traceback
            traceback.print_exc()
            return "failed"

    def create_personalized_note(self, profile_data, note_template):
        try:
            full_name = profile_data.get('name', 'there')
            about_full = profile_data.get('about', '')
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
                personalized_note = personalized_note[:297] + "..."

            return personalized_note
        except Exception:
            return note_template

    def process_csv_profiles(self, csv_file, note_template, max_requests=20):
        try:
            df = pd.read_csv(csv_file)

            if 'profile_url' not in df.columns:
                print("CSV must contain 'profile_url' column!")
                return None

            for col in ['connection_date', 'connection_note', 'connection_status']:
                if col not in df.columns:
                    df[col] = ''

            for col in ['connection_date', 'connection_note', 'connection_status']:
                df[col] = df[col].astype(str).str.strip().replace('nan', '')

            unprocessed_mask = (
                (df['connection_date'] == '') &
                (df['connection_note'] == '') &
                (df['connection_status'] == '')
            )

            processed_count = (~unprocessed_mask).sum()
            total_profiles = len(df)
            remaining_profiles = unprocessed_mask.sum()

            print(f"Total: {total_profiles} | Already processed: {processed_count} | Remaining: {remaining_profiles}")

            if remaining_profiles == 0:
                print("All profiles have been processed!")
                return df

            successful = failed = skipped = connect_not_found = requests_sent = 0

            for idx, row in df.iterrows():
                if not unprocessed_mask[idx]:
                    continue
                if requests_sent >= max_requests:
                    skipped = remaining_profiles - requests_sent
                    break

                profile_url = row['profile_url']
                print(f"\n{'='*60}")
                print(f"Profile {idx + 1}/{total_profiles} | Run: {requests_sent + 1}/{min(max_requests, remaining_profiles)}")
                print(f"URL: {profile_url}")

                personalized_note = self.create_personalized_note(row.to_dict(), note_template)
                print(f"Note preview:\n{personalized_note}")

                result = self.send_connection_request(profile_url, personalized_note)
                print(f"Result: {result}")

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

                if requests_sent % 5 == 0 and requests_sent < remaining_profiles:
                    print("Taking a longer break...")
                    self.human_delay(30, 60)
                elif requests_sent < remaining_profiles:
                    self.human_delay(5, 10)

            print(f"\n{'='*60}")
            print(f"SUMMARY: Success={successful} | Not found={connect_not_found} | Failed={failed} | Skipped={skipped}")

            return df

        except Exception as e:
            import traceback
            traceback.print_exc()
            return None

    def close(self):
        if self.driver:
            time.sleep(5)
            self.driver.quit()


def main():
    EMAIL = LINKEDIN_USERNAME
    PASSWORD = LINKEDIN_PASSWORD

    INPUT_CSV = "linkedin_profiles/extracted_profiles_keydata_04-07-26-09.csv"

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
                print("Process completed successfully!")
        else:
            print("Login failed.")

    except KeyboardInterrupt:
        print("\nScript interrupted by user")
    except Exception as e:
        import traceback
        traceback.print_exc()
    finally:
        bot.close()


if __name__ == "__main__":
    main()