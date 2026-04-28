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
from selenium.common.exceptions import (
    TimeoutException,
    NoSuchElementException,
    StaleElementReferenceException,
)
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
                if (!el) return false;

                // Exact ancestor checks only; avoid substring false positives from random class names.
                if (el.closest('aside')) return true;

                var cur = el;
                for (var i = 0; i < 14 && cur; i++) {
                    var cls = cur.classList;
                    if (cls && (cls.contains('scaffold-layout__aside') || cls.contains('pv-profile-layout__aside'))) {
                        return true;
                    }
                    var idv = (cur.id || '').toLowerCase();
                    if (idv === 'aside' || idv.includes('right-rail')) {
                        return true;
                    }
                    cur = cur.parentElement;
                }
                return false;
            """, element)
        except Exception:
            return False

    def _safe_click(self, element):
        """Best-effort click that handles overlays/intercepted clicks."""
        try:
            self.driver.execute_script("arguments[0].scrollIntoView({block:'center'});", element)
            time.sleep(0.3)
        except Exception:
            pass

        try:
            element.click()
            return True
        except Exception:
            pass

        try:
            self.driver.execute_script("arguments[0].click();", element)
            return True
        except Exception:
            return False

    def _debug_connect_candidates(self, limit=20):
        """Print a compact audit of visible connect-like controls for debugging."""
        try:
            data = self.driver.execute_script(
                """
                const out = [];
                const nodes = Array.from(document.querySelectorAll('main a, main button, main [role="button"], main [role="menuitem"]'));
                const isVisible = (el) => {
                  const style = window.getComputedStyle(el);
                  const rect = el.getBoundingClientRect();
                  return style && style.visibility !== 'hidden' && style.display !== 'none' && rect.width > 0 && rect.height > 0;
                };
                for (const el of nodes) {
                  if (!isVisible(el)) continue;
                  const txt = (el.innerText || el.textContent || '').trim().replace(/\s+/g, ' ');
                  const aria = (el.getAttribute('aria-label') || '').trim();
                  const href = (el.getAttribute('href') || '').trim();
                  const cls = (el.className || '').toString();
                  const low = (txt + ' ' + aria + ' ' + href).toLowerCase();
                  if (!low.includes('connect') && !low.includes('invite') && !href.includes('/preload/custom-invite/')) continue;
                  const inAside = !!el.closest('aside, .scaffold-layout__aside');
                  const rect = el.getBoundingClientRect();
                  out.push({
                    tag: (el.tagName || '').toLowerCase(),
                    role: (el.getAttribute('role') || '').toLowerCase(),
                    text: txt,
                    aria: aria,
                    href: href,
                    inAside: inAside,
                    y: Math.round(rect.top),
                    cls: cls.slice(0, 140)
                  });
                }
                out.sort((a, b) => a.y - b.y);
                return out.slice(0, arguments[0]);
                """,
                int(limit),
            )
            if data:
                print(f"[DEBUG] Connect-like visible candidates ({len(data)}):")
                for i, item in enumerate(data, 1):
                    print(
                        f"  {i:02d}. tag={item.get('tag')} role={item.get('role')} y={item.get('y')} "
                        f"aside={item.get('inAside')} text='{item.get('text')}' aria='{item.get('aria')}' href='{item.get('href')}'"
                    )
            else:
                print("[DEBUG] No visible connect-like candidates found in <main>.")
        except Exception:
            pass

    def _find_connect_button_direct(self):
        def valid(el):
            try:
                return el.is_displayed() and not self._is_in_sidebar(el)
            except Exception:
                return False

        try:
            WebDriverWait(self.driver, 6).until(
                lambda d: len(
                    d.find_elements(
                        By.XPATH,
                        "//main//button["
                        "contains(translate(@aria-label,'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'),'connect') or "
                        "contains(translate(@aria-label,'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'),'invite') or "
                        ".//span[normalize-space(text())='Connect']"
                        "]"
                    )
                ) > 0
            )
        except Exception:
            pass

        for el in self.driver.find_elements(
            By.XPATH,
            "//main//button["
            "contains(@class,'artdeco-button--primary') and "
            "contains(translate(@aria-label,'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'),'invite') and "
            "contains(translate(@aria-label,'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'),'to connect') and "
            ".//span[normalize-space(text())='Connect'] and "
            ".//*[self::svg or self::use][contains(@data-test-icon,'connect-small') or contains(@href,'#connect-small')]"
            "]"
        ):
            if valid(el): return el

        for el in self.driver.find_elements(
            By.XPATH,
            "//main//button["
            "contains(@class,'artdeco-button--primary') and "
            "contains(translate(@aria-label,'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'),'to connect')"
            "]"
        ):
            if valid(el): return el

        for el in self.driver.find_elements(
            By.XPATH,
            "//main//a[contains(@href,'/preload/custom-invite/') and (contains(translate(@aria-label,'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'),'connect') or contains(translate(normalize-space(string(.)),'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'),'connect'))]"
        ):
            if valid(el): return el

        for el in self.driver.find_elements(
            By.XPATH,
            "//main//button[contains(translate(@aria-label,'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'),'to connect')]"
        ):
            if valid(el): return el

        for el in self.driver.find_elements(
            By.XPATH,
            "//main//button["
            "contains(translate(@aria-label,'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'),'invite') and "
            "contains(translate(@aria-label,'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'),'connect')"
            "]"
        ):
            if valid(el): return el

        for el in self.driver.find_elements(
            By.XPATH,
            "//main//button["
            "contains(@class,'artdeco-button--primary') and "
            ".//span[normalize-space(text())='Connect']"
            "]"
        ):
            if valid(el): return el

        for el in self.driver.find_elements(
            By.XPATH,
            "//main//button[.//span[normalize-space(text())='Connect']]"
        ):
            if valid(el): return el

        for el in self.driver.find_elements(
            By.XPATH,
            "//main//a[contains(translate(normalize-space(string(.)),'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'),'connect')]"
        ):
            if valid(el): return el

        try:
            candidate = self.driver.execute_script(
                """
                const inMain = document.querySelector('main') || document;
                const buttons = Array.from(inMain.querySelectorAll('button'));
                const isVisible = (el) => {
                  const style = window.getComputedStyle(el);
                  const rect = el.getBoundingClientRect();
                  return style && style.visibility !== 'hidden' && style.display !== 'none' && rect.width > 0 && rect.height > 0;
                };
                const isInAside = (el) => !!el.closest('aside, .scaffold-layout__aside');
                const text = (el) => (el.innerText || el.textContent || '').trim().toLowerCase();
                const label = (el) => (el.getAttribute('aria-label') || '').trim().toLowerCase();
                const ranked = buttons.filter((b) => {
                  const t = text(b);
                  const l = label(b);
                  return !isInAside(b) && isVisible(b) && (
                    l.includes('to connect') ||
                    (l.includes('invite') && l.includes('connect')) ||
                    t === 'connect'
                  );
                });
                const topCardHit = ranked.find((b) => {
                  const card = b.closest('section.artdeco-card, .pv-top-card, .pv-profile-card');
                  return !!card;
                });
                return topCardHit || ranked[0] || null;
                """
            )
            if candidate and valid(candidate):
                return candidate
        except Exception:
            pass

        try:
            candidate = self.driver.execute_script(
                """
                const inMain = document.querySelector('main') || document;
                const isVisible = (el) => {
                  const style = window.getComputedStyle(el);
                  const rect = el.getBoundingClientRect();
                  return style && style.visibility !== 'hidden' && style.display !== 'none' && rect.width > 0 && rect.height > 0;
                };
                const buttons = Array.from(inMain.querySelectorAll('button'));
                const hits = buttons.filter((b) => {
                  if (!isVisible(b)) return false;
                  if (b.closest('aside, .scaffold-layout__aside, .pv-profile-layout__aside')) return false;
                  const label = (b.getAttribute('aria-label') || '').toLowerCase();
                  const text = (b.innerText || b.textContent || '').trim().toLowerCase();
                  return label.includes('invite') && label.includes('connect') && text.includes('connect');
                });
                hits.sort((a, b) => a.getBoundingClientRect().top - b.getBoundingClientRect().top);
                return hits[0] || null;
                """
            )
            if candidate:
                return candidate
        except Exception:
            pass

        return None

    def _open_more_actions_and_find_connect(self):
        # Find the profile top-card "More actions" trigger that is NOT in the sidebar.
        more_btn = None
        for btn in self.driver.find_elements(
            By.XPATH,
            "//main//button[@aria-label='More actions' and contains(@class,'artdeco-dropdown__trigger')]"
        ):
            try:
                if btn.is_displayed() and not self._is_in_sidebar(btn):
                    more_btn = btn
                    break
            except Exception:
                continue

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

            try:
                more_btn.click()
            except Exception:
                self.driver.execute_script("arguments[0].click();", more_btn)

            self.wait.until(
                lambda d: d.execute_script(
                    """
                    const btn = arguments[0];
                    const host = btn ? btn.closest('.artdeco-dropdown') : null;
                    if (!host) return false;
                    const panel = host.querySelector('.artdeco-dropdown__content');
                    if (!panel) return false;
                    const hidden = (panel.getAttribute('aria-hidden') || '').toLowerCase();
                    const style = window.getComputedStyle(panel);
                    return hidden === 'false' && style.display !== 'none' && style.visibility !== 'hidden';
                    """,
                    more_btn,
                )
            )
        except Exception:
            return None

        try:
            dropdown_root = self.driver.execute_script(
                """
                const btn = arguments[0];
                const host = btn ? btn.closest('.artdeco-dropdown') : null;
                if (!host) return null;
                return host.querySelector('.artdeco-dropdown__content .artdeco-dropdown__content-inner') ||
                       host.querySelector('.artdeco-dropdown__content');
                """,
                more_btn,
            )
        except Exception:
            dropdown_root = None

        if dropdown_root is not None:
            try:
                exact_connect = WebDriverWait(self.driver, 5).until(
                    lambda d: dropdown_root.find_element(
                        By.XPATH,
                        ".//div[@role='button' and contains(@class,'artdeco-dropdown__item') and contains(translate(@aria-label,'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'),'invite') and contains(translate(@aria-label,'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'),'to connect')]",
                    )
                )
                if exact_connect.is_displayed() and not self._is_in_sidebar(exact_connect):
                    return exact_connect
            except Exception:
                pass

            scoped_item_xpaths = [
                ".//*[self::div or self::li][@role='button' and contains(translate(@aria-label,'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'),'to connect')]",
                ".//*[contains(@class,'artdeco-dropdown__item') and @role='button' and .//span[normalize-space(text())='Connect']]",
                ".//*[@role='menuitem' and contains(translate(normalize-space(string(.)),'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'),'connect')]",
                ".//a[contains(@href,'/preload/custom-invite/') and contains(translate(normalize-space(string(.)),'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'),'connect')]",
            ]
            for xpath in scoped_item_xpaths:
                for el in dropdown_root.find_elements(By.XPATH, xpath):
                    try:
                        if el.is_displayed() and not self._is_in_sidebar(el):
                            return el
                    except Exception:
                        continue

        for el in self.driver.find_elements(
            By.XPATH,
            "//button[contains(translate(@aria-label,'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'), 'to connect')]"
        ):
            try:
                if el.is_displayed():
                    return el
            except Exception:
                continue

        for el in self.driver.find_elements(By.XPATH, "//a[contains(@href,'/preload/custom-invite/')]"):
            try:
                if el.is_displayed() and not self._is_in_sidebar(el):
                    return el
            except Exception:
                continue

        try:
            from selenium.webdriver.common.keys import Keys
            self.driver.find_element(By.TAG_NAME, "body").send_keys(Keys.ESCAPE)
        except Exception:
            pass

        return None

    def discover_connect_button(self):
        try:
            self.wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "main")))
        except TimeoutException:
            pass
        time.sleep(2)

        try:
            WebDriverWait(self.driver, 5).until(
                EC.presence_of_element_located(
                    (
                        By.XPATH,
                        "//main//button[contains(@class,'artdeco-button--primary') and contains(translate(@aria-label,'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'),'invite') and contains(translate(@aria-label,'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'),'to connect') and .//span[normalize-space(text())='Connect']]",
                    )
                )
            )
        except Exception:
            pass

        # Primary: More actions dropdown first
        el = self._open_more_actions_and_find_connect()
        if el:
            return el

        # Fallback: direct Connect button
        el = self._find_connect_button_direct()
        if el:
            return el

        self._debug_connect_candidates(limit=25)
        return None

    def _click_send_button(self):
        try:
            send_btn = WebDriverWait(self.driver, 8).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, "button[aria-label='Send invitation']"))
            )
            self.driver.execute_script("arguments[0].click();", send_btn)
            self.human_delay(3, 5)
            return "success"
        except TimeoutException:
            pass

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
        try:
            self.driver.get(profile_url)
            self.human_delay(3, 5)

            connect_el = self.discover_connect_button()
            if connect_el is None:
                return "connect_not_found"

            try:
                tag = connect_el.tag_name.lower()
                href = connect_el.get_attribute("href") or ""
            except StaleElementReferenceException:
                connect_el = self.discover_connect_button()
                if connect_el is None:
                    return "connect_not_found"
                tag = connect_el.tag_name.lower()
                href = connect_el.get_attribute("href") or ""

            self.driver.execute_script("arguments[0].scrollIntoView({block:'center'});", connect_el)
            time.sleep(0.4)

            if tag == "a" and "/preload/custom-invite/" in href:
                self.driver.get(href)
            else:
                if not self._safe_click(connect_el):
                    return "failed"

            self.human_delay(2, 3)

            current_url = self.driver.current_url
            on_invite_page = "custom-invite" in current_url or "preload" in current_url

            if on_invite_page:
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
                        pass
                return self._click_send_button()

            else:
                try:
                    modal = WebDriverWait(self.driver, 6).until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, "[role='dialog'], [aria-modal='true']"))
                    )
                except TimeoutException:
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

    def process_csv_profiles(self, csv_file, max_requests=20):
        try:
            df = pd.read_csv(csv_file)

            if 'profile_url' not in df.columns:
                print("CSV must contain 'profile_url' column!")
                return None

            if 'connection_note' not in df.columns:
                print("CSV must contain 'connection_note' column with pre-generated notes!")
                return None

            for col in ['connection_date', 'connection_status']:
                if col not in df.columns:
                    df[col] = ''

            for col in ['connection_date', 'connection_note', 'connection_status']:
                df[col] = df[col].astype(str).str.strip().replace('nan', '')

            # A row is ready to send if it has a generated note but hasn't been sent yet
            sendable_mask = (
                (df['connection_note'] != '') &
                (df['connection_status'] == '')
            )

            already_sent   = (df['connection_status'] != '').sum()
            missing_note   = ((df['connection_note'] == '') & (df['connection_status'] == '')).sum()
            to_send        = sendable_mask.sum()
            total_profiles = len(df)

            print(f"Total: {total_profiles} | Already sent: {already_sent} | No note (skipped): {missing_note} | Ready to send: {to_send}")

            if to_send == 0:
                print("No profiles ready to send — either all sent or notes are missing.")
                return df

            successful = failed = skipped = connect_not_found = requests_sent = 0

            for idx, row in df.iterrows():
                if not sendable_mask[idx]:
                    continue
                if requests_sent >= max_requests:
                    skipped = to_send - requests_sent
                    break

                profile_url = row['profile_url']
                note        = str(row['connection_note']).strip()

                print(f"\n{'='*60}")
                print(f"Profile {idx + 1}/{total_profiles} | Run: {requests_sent + 1}/{min(max_requests, to_send)}")
                print(f"URL: {profile_url}")
                print(f"Note preview:\n{note}")

                # Enforce LinkedIn's 300-char hard limit before sending
                if len(note) > 300:
                    note = note[:300].rsplit(' ', 1)[0]
                    print(f"⚠️  Note trimmed to {len(note)} chars to fit LinkedIn limit.")

                result = self.send_connection_request(profile_url, note)
                print(f"Result: {result}")

                df.at[idx, 'connection_date']   = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                df.at[idx, 'connection_status'] = result

                if result == "success":
                    successful += 1
                elif result == "connect_not_found":
                    connect_not_found += 1
                else:
                    failed += 1

                requests_sent += 1
                df.to_csv(csv_file, index=False, encoding='utf-8')

                if requests_sent % 5 == 0 and requests_sent < to_send:
                    print("Taking a longer break...")
                    self.human_delay(30, 60)
                elif requests_sent < to_send:
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
    EMAIL    = LINKEDIN_USERNAME
    PASSWORD = LINKEDIN_PASSWORD

    # ── Point this at the CSV that already has connection_note filled in ──────
    INPUT_CSV    = "linkedin_profiles/extracted_profiles_of_tech_recs_04-27-26-16_with_notes.csv"
    MAX_REQUESTS = 200
    # ─────────────────────────────────────────────────────────────────────────

    bot = LinkedInConnectionBot(EMAIL, PASSWORD)

    try:
        bot.setup_driver()

        if bot.login():
            results = bot.process_csv_profiles(
                csv_file=INPUT_CSV,
                max_requests=MAX_REQUESTS,
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