"""
LinkedIn Profile Scraper - Enhanced with Better Progress Tracking
Key improvements:
- Clear progress file showing what's been scraped and what remains
- Resumption checkpoint with detailed status
- Better error handling and recovery
"""
from creds import LINKEDIN_USERNAME, LINKEDIN_PASSWORD
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
import pandas as pd
import time
from datetime import datetime
import os
import json
import re
from urllib.parse import urlparse

class LinkedInBatchScraper:
    def __init__(self, email, password):
        self.email = email
        self.password = password
        self.driver = None

    @staticmethod
    def normalize_linkedin_profile_url(url):
        """Normalize LinkedIn profile URLs so resume/dedupe logic is reliable."""
        if not isinstance(url, str):
            return ''

        trimmed = url.strip()
        if not trimmed:
            return ''

        try:
            parsed = urlparse(trimmed)
            path = re.sub(r'/+', '/', parsed.path).rstrip('/')
            return f"{parsed.scheme}://{parsed.netloc}{path}" if parsed.scheme and parsed.netloc else trimmed.rstrip('/')
        except Exception:
            return trimmed.rstrip('/')

    @staticmethod
    def _first_non_empty(values):
        for value in values:
            cleaned = str(value).strip()
            if cleaned:
                return cleaned
        return ''

    def _find_first_text(self, css_selectors=None, xpath_selectors=None, timeout=5):
        """Return first non-empty text from any selector in order."""
        wait = WebDriverWait(self.driver, timeout)

        if css_selectors:
            for selector in css_selectors:
                try:
                    elem = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, selector)))
                    text = elem.text.strip()
                    if text:
                        return text
                except TimeoutException:
                    continue
                except Exception:
                    continue

        if xpath_selectors:
            for selector in xpath_selectors:
                try:
                    elem = wait.until(EC.presence_of_element_located((By.XPATH, selector)))
                    text = elem.text.strip()
                    if text:
                        return text
                except TimeoutException:
                    continue
                except Exception:
                    continue

        return ''

    @staticmethod
    def _extract_value_from_aria_label(label_text, expected_prefix):
        """Extract value from labels like 'Current company: X. Click to ...'."""
        if not isinstance(label_text, str):
            return ''

        lower = label_text.lower()
        prefix = expected_prefix.lower()
        if not lower.startswith(prefix):
            return ''

        after_prefix = label_text[len(expected_prefix):].strip()
        value = after_prefix.split('. Click to', 1)[0].strip()
        return value

    def extract_company_and_university_from_highlights(self):
        """Extract current company and university from top highlight list items."""
        company = ''
        university = ''

        try:
            buttons = self.driver.find_elements(By.CSS_SELECTOR, "main section ul li button[aria-label]")
            for btn in buttons:
                aria = btn.get_attribute("aria-label") or ''

                if not company:
                    company = self._extract_value_from_aria_label(aria, "Current company:")

                if not university:
                    university = self._extract_value_from_aria_label(aria, "Education:")

                if company and university:
                    break
        except Exception:
            pass

        # Positional fallback based on the list structure shown in your HTML snippet.
        if not company or not university:
            try:
                text_nodes = self.driver.find_elements(
                    By.CSS_SELECTOR,
                    "main section ul li button span div.inline-show-more-text[dir='ltr']"
                )
                values = [node.text.strip() for node in text_nodes if node.text and node.text.strip()]
                if not company and len(values) >= 1:
                    company = values[0]
                if not university and len(values) >= 2:
                    university = values[1]
            except Exception:
                pass

        return company, university
        
    def setup_driver(self):
        """Initialize Chrome driver with options"""
        options = webdriver.ChromeOptions()
        options.add_argument('--start-maximized')
        options.add_argument('--disable-blink-features=AutomationControlled')
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option('useAutomationExtension', False)
        
        self.driver = webdriver.Chrome(options=options)
        self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        
    def login(self):
        """Login to LinkedIn using email and password"""
        print("Navigating to LinkedIn login page...")
        self.driver.get("https://www.linkedin.com/login")
        
        wait = WebDriverWait(self.driver, 15)
        
        try:
            print("Entering email...")
            email_field = wait.until(EC.presence_of_element_located((By.ID, "username")))
            email_field.clear()
            email_field.send_keys(self.email)
            time.sleep(1)
            
            print("Entering password...")
            password_field = self.driver.find_element(By.ID, "password")
            password_field.clear()
            password_field.send_keys(self.password)
            time.sleep(1)
            
            print("Clicking sign in button...")
            sign_in_button = self.driver.find_element(By.CSS_SELECTOR, "button[type='submit']")
            sign_in_button.click()
            
            time.sleep(5)
            
            current_url = self.driver.current_url
            
            if "checkpoint" in current_url or "challenge" in current_url:
                print("\n⚠️ LinkedIn requires additional verification!")
                print("Please complete the verification in the browser window...")
                print("Waiting for 60 seconds for manual verification...")
                time.sleep(60)
            
            if "feed" in self.driver.current_url or "mynetwork" in self.driver.current_url:
                print("✓ Successfully logged in!")
                return True
            elif "login" in self.driver.current_url:
                print("✗ Login failed. Please check your credentials.")
                return False
            else:
                print("Login status unclear. Current URL:", self.driver.current_url)
                print("Waiting 5 more seconds...")
                time.sleep(5)
                return True
                
        except Exception as e:
            print(f"Error during login: {e}")
            return False
    
    def extract_profile_data(self, profile_url):
        """Extract profile information from LinkedIn profile page"""
        print(f"\nNavigating to profile: {profile_url}")
        self.driver.get(profile_url)
        time.sleep(4)
        
        wait = WebDriverWait(self.driver, 10)
        
        profile_data = {
            'profile_url': profile_url,
            'scraped_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'name': '',
            'headline': '',
            'current_company': '',
            'university': '',
            'location': '',
            'about': '',
            'connections': '',
            'mutual_connections': '',
            'connection_degree': '',
            'status': 'success',
            'fields_extracted': []
        }
        
        try:
            # Name
            try:
                name_selectors = [
                    "h1.text-heading-xlarge",
                    "h1.inline.t-24.v-align-middle.break-words",
                    "main h1",
                ]

                name_text = self._find_first_text(css_selectors=name_selectors, timeout=8)
                if name_text:
                    profile_data['name'] = name_text
                    profile_data['fields_extracted'].append('name')
                    print(f"✓ Found name: {profile_data['name']}")
            except Exception as e:
                print(f"✗ Could not find name: {e}")
            
            # Connection degree
            try:
                page_text_snippets = [e.text.strip() for e in self.driver.find_elements(By.CSS_SELECTOR, "main section span, main section p")]
                for snippet in page_text_snippets:
                    clean = snippet.replace('·', '').strip()
                    if clean in {'1st', '2nd', '3rd'}:
                        profile_data['connection_degree'] = clean
                        profile_data['fields_extracted'].append('connection_degree')
                        print(f"✓ Found connection degree: {profile_data['connection_degree']}")
                        break
            except Exception as e:
                print(f"✗ Could not find connection degree: {e}")
            
            # Headline
            try:
                headline = self._find_first_text(
                    css_selectors=[
                        "div.text-body-medium.break-words",
                        "div.text-body-medium",
                        "main section .pv-text-details__left-panel div.text-body-medium",
                    ],
                    xpath_selectors=["//main//div[contains(@class,'text-body-medium') and normalize-space()]"],
                    timeout=6,
                )
                if headline:
                    profile_data['headline'] = headline
                    profile_data['fields_extracted'].append('headline')
                    print(f"✓ Found headline: {profile_data['headline'][:50]}...")
            except Exception as e:
                print(f"✗ Could not find headline: {e}")

            # Company and University from top highlights list
            try:
                company_from_list, university_from_list = self.extract_company_and_university_from_highlights()

                if company_from_list:
                    profile_data['current_company'] = company_from_list
                    if 'current_company' not in profile_data['fields_extracted']:
                        profile_data['fields_extracted'].append('current_company')
                    print(f"✓ Found company from highlights: {profile_data['current_company']}")

                if university_from_list:
                    profile_data['university'] = university_from_list
                    profile_data['fields_extracted'].append('university')
                    print(f"✓ Found university from highlights: {profile_data['university']}")
            except Exception as e:
                print(f"✗ Could not parse highlights list: {e}")
            
            # Current Company
            try:
                if not profile_data['current_company']:
                    company = self._find_first_text(
                        css_selectors=[
                            "div.text-body-small.inline.t-black--light.break-words",
                            "main section .pv-text-details__left-panel div.text-body-small",
                        ],
                        timeout=5,
                    )
                    if company:
                        profile_data['current_company'] = company
                        if 'current_company' not in profile_data['fields_extracted']:
                            profile_data['fields_extracted'].append('current_company')
                        print(f"✓ Found company: {profile_data['current_company']}")
            except Exception as e:
                print(f"✗ Could not find company: {e}")
            
            # Location
            try:
                location_candidates = [
                    e.text.strip()
                    for e in self.driver.find_elements(
                        By.CSS_SELECTOR,
                        "main section .pv-text-details__left-panel span.text-body-small.inline.t-black--light.break-words, "
                        "main section .pv-text-details__left-panel div.text-body-small"
                    )
                ]
                for location_text in location_candidates:
                    if location_text and 'contact info' not in location_text.lower() and 'followers' not in location_text.lower():
                        profile_data['location'] = location_text
                        profile_data['fields_extracted'].append('location')
                        print(f"✓ Found location: {profile_data['location']}")
                        break
            except Exception as e:
                print(f"✗ Could not find location: {e}")
            
            # Connections count
            try:
                all_text = [e.text.strip() for e in self.driver.find_elements(By.CSS_SELECTOR, "main section span, main section a, main section p")]
                for text in all_text:
                    lower = text.lower()
                    if ' connection' in lower or lower.endswith('connections') or lower.endswith('connection'):
                        profile_data['connections'] = text
                        profile_data['fields_extracted'].append('connections')
                        print(f"✓ Found connections: {profile_data['connections']}")
                        break
            except Exception as e:
                print(f"✗ Could not find connections: {e}")
            
            # Mutual connections
            try:
                for elem in self.driver.find_elements(By.CSS_SELECTOR, "main section span, main section a, main section p"):
                    text = elem.text.strip()
                    if 'mutual connection' in text.lower():
                        profile_data['mutual_connections'] = text
                        profile_data['fields_extracted'].append('mutual_connections')
                        print(f"✓ Found mutual connections: {profile_data['mutual_connections']}")
                        break
            except Exception as e:
                print(f"✗ Could not find mutual connections: {e}")
            
            # Scroll to load more content
            self.driver.execute_script("window.scrollTo(0, 800);")
            time.sleep(2)
            
            # About section
            try:
                about_selectors = [
                    "div.inline-show-more-text",
                    "div.pv-shared-text-with-see-more",
                    "section[data-section='summary'] div.pv-shared-text-with-see-more",
                    "div.display-flex.ph5.pv3 div.full-width",
                    "section.artdeco-card p[dir='ltr']",
                ]
                
                for selector in about_selectors:
                    try:
                        try:
                            see_more_button = self.driver.find_element(By.XPATH, "//button[contains(translate(@aria-label, 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'more')]")
                            see_more_button.click()
                            time.sleep(1)
                        except:
                            pass
                        
                        about = self.driver.find_element(By.CSS_SELECTOR, selector)
                        about_text = about.text.strip()
                        if about_text and len(about_text) > 10:
                            profile_data['about'] = about_text
                            profile_data['fields_extracted'].append('about')
                            print(f"✓ Found about section ({len(about_text)} chars)")
                            break
                    except:
                        continue
            except Exception as e:
                print(f"✗ Could not find about section: {e}")
            
            # Convert fields_extracted list to string
            profile_data['fields_extracted'] = ', '.join(profile_data['fields_extracted']) if profile_data['fields_extracted'] else 'none'
            
            # Determine status
            key_fields = ['name', 'headline', 'location', 'connections', 'about']
            extracted_list = profile_data['fields_extracted'].split(', ') if profile_data['fields_extracted'] != 'none' else []
            extracted_key_count = len([f for f in extracted_list if f in key_fields])
            
            if extracted_key_count == 0:
                profile_data['status'] = 'failed'
            elif extracted_key_count < len(key_fields):
                profile_data['status'] = 'partial_success'
            else:
                profile_data['status'] = 'success'
                
        except Exception as e:
            print(f"✗ Error extracting profile data: {e}")
            profile_data['status'] = 'error'
            profile_data['error_message'] = str(e)
            profile_data['fields_extracted'] = 'none'
        
        return profile_data
    
    def save_progress_checkpoint(self, checkpoint_file, current_index, total, scraped_urls, remaining_urls):
        """Save detailed progress checkpoint"""
        checkpoint_data = {
            'last_updated': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'current_index': current_index,
            'total_urls': total,
            'completed': current_index,
            'remaining': total - current_index,
            'scraped_urls': list(scraped_urls),
            'remaining_urls': remaining_urls,
            'completion_percentage': round((current_index / total * 100), 2) if total > 0 else 0
        }
        
        with open(checkpoint_file, 'w') as f:
            json.dump(checkpoint_data, f, indent=2)
    
    def load_checkpoint(self, checkpoint_file):
        """Load progress checkpoint"""
        if os.path.exists(checkpoint_file):
            try:
                with open(checkpoint_file, 'r') as f:
                    return json.load(f)
            except:
                return None
        return None
    
    def scrape_profiles_from_csv(self, input_csv, output_csv='linkedin_profiles_output.csv', url_column='url', resume=True):
        """
        Scrape multiple LinkedIn profiles from CSV file with enhanced progress tracking
        """
        try:
            # Setup checkpoint file
            checkpoint_file = output_csv.replace('.csv', '_checkpoint.json')
            
            # Read input CSV
            print(f"\nReading URLs from: {input_csv}")
            df = pd.read_csv(input_csv)
            
            if url_column not in df.columns:
                print(f"\n✗ Column '{url_column}' not found in CSV!")
                print(f"Available columns: {', '.join(df.columns)}")
                return None
            
            # Get all URLs
            raw_urls = [str(u).strip() for u in df[url_column].dropna().tolist()]
            normalized_urls = [self.normalize_linkedin_profile_url(u) for u in raw_urls]
            all_urls = list(dict.fromkeys([u for u in normalized_urls if u]))

            if not all_urls:
                print("\n✗ No valid LinkedIn profile URLs found in input CSV.")
                return None
            
            # Load existing progress
            existing_df = None
            scraped_urls = set()
            
            if resume and os.path.exists(output_csv):
                try:
                    existing_df = pd.read_csv(output_csv)
                    if 'pronouns' in existing_df.columns:
                        existing_df = existing_df.drop(columns=['pronouns'])
                        existing_df.to_csv(output_csv, index=False, encoding='utf-8')
                    if 'profile_url' in existing_df.columns:
                        scraped_urls = {
                            self.normalize_linkedin_profile_url(u)
                            for u in existing_df['profile_url'].dropna().tolist()
                            if self.normalize_linkedin_profile_url(u)
                        }
                    else:
                        scraped_urls = set()
                    print(f"\n✓ Found existing progress file: {output_csv}")
                    print(f"✓ Already scraped: {len(scraped_urls)} profiles")
                except Exception as e:
                    print(f"✗ Error loading existing progress: {e}")
            
            # Load checkpoint if exists
            checkpoint = self.load_checkpoint(checkpoint_file) if resume else None
            if checkpoint:
                print(f"\n✓ Found checkpoint file from {checkpoint['last_updated']}")
                print(f"✓ Last session completed: {checkpoint['completed']}/{checkpoint['total_urls']} ({checkpoint['completion_percentage']}%)")
            
            # Filter URLs
            urls_to_scrape = [url for url in all_urls if url not in scraped_urls]
            
            total_urls = len(urls_to_scrape)
            already_scraped = len(all_urls) - total_urls
            
            # ENHANCED PROGRESS DISPLAY
            print(f"\n{'='*70}")
            print(f"SCRAPING SESSION PLAN")
            print(f"{'='*70}")
            print(f"📊 Total URLs in input file: {len(all_urls)}")
            print(f"✅ Already scraped: {already_scraped}")
            print(f"⏳ Remaining to scrape: {total_urls}")
            completion_pct = round((already_scraped / len(all_urls) * 100), 2) if len(all_urls) > 0 else 0
            print(f"📈 Completion: {completion_pct}%")
            print(f"{'='*70}\n")
            
            if total_urls == 0:
                print("✓ All profiles have already been scraped!")
                if existing_df is not None:
                    return existing_df
                return None
            
            # Show next 5 URLs to be scraped
            print("📋 Next profiles to scrape:")
            for i, url in enumerate(urls_to_scrape[:5], 1):
                print(f"   {i}. {url}")
            if total_urls > 5:
                print(f"   ... and {total_urls - 5} more\n")
            
            # Setup driver
            self.setup_driver()
            
            # Login
            if not self.login():
                print("✗ Login failed. Exiting...")
                return None
            
            print(f"\n{'='*70}")
            print(f"🚀 STARTING SCRAPING SESSION")
            print(f"{'='*70}\n")
            
            # Start with existing data
            if existing_df is not None:
                all_profiles_data = existing_df.to_dict('records')
            else:
                all_profiles_data = []
            
            # Scrape each profile
            for idx, url in enumerate(urls_to_scrape, 1):
                absolute_index = already_scraped + idx
                
                print(f"\n{'='*70}")
                print(f"🔄 Profile {idx}/{total_urls} | Overall: {absolute_index}/{len(all_urls)} ({round(absolute_index/len(all_urls)*100, 1)}%)")
                print(f"{'='*70}")
                
                try:
                    # Extract profile data
                    profile_data = self.extract_profile_data(url)
                    all_profiles_data.append(profile_data)
                    scraped_urls.add(url)
                    
                    # Save progress after each profile
                    temp_df = pd.DataFrame(all_profiles_data)
                    if 'pronouns' in temp_df.columns:
                        temp_df = temp_df.drop(columns=['pronouns'])
                    temp_df.to_csv(output_csv, index=False, encoding='utf-8')
                    
                    # Save checkpoint
                    remaining_urls = urls_to_scrape[idx:]
                    self.save_progress_checkpoint(
                        checkpoint_file, 
                        absolute_index, 
                        len(all_urls),
                        scraped_urls,
                        remaining_urls
                    )
                    
                    # Status display
                    status_emoji = "✓" if profile_data['status'] == 'success' else "⚠️" if profile_data['status'] == 'partial_success' else "✗"
                    print(f"\n{status_emoji} Status: {profile_data['status']}")
                    print(f"📝 Fields extracted: {profile_data['fields_extracted']}")
                    print(f"💾 Progress saved: {absolute_index}/{len(all_urls)} complete")
                    
                    # Show what's next
                    if idx < total_urls:
                        print(f"⏭️  Next: {urls_to_scrape[idx]} ({total_urls - idx} remaining)")
                        delay = 5
                        print(f"⏳ Waiting {delay} seconds...")
                        time.sleep(delay)
                    
                except KeyboardInterrupt:
                    print("\n\n⚠️ Scraping interrupted by user!")
                    print(f"✓ Progress saved to {output_csv}")
                    print(f"✓ Checkpoint saved to {checkpoint_file}")
                    print(f"✓ Completed: {absolute_index}/{len(all_urls)}")
                    print(f"✓ Remaining: {len(all_urls) - absolute_index} profiles")
                    print(f"\n💡 To resume: Just run the script again with resume=True")
                    raise
                    
                except Exception as e:
                    print(f"\n✗ Error processing profile {idx}: {e}")
                    error_data = {
                        'profile_url': url,
                        'scraped_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                        'status': 'error',
                        'error_message': str(e),
                        'fields_extracted': 'none'
                    }
                    all_profiles_data.append(error_data)
                    scraped_urls.add(url)
                    
                    # Save progress even on error
                    temp_df = pd.DataFrame(all_profiles_data)
                    if 'pronouns' in temp_df.columns:
                        temp_df = temp_df.drop(columns=['pronouns'])
                    temp_df.to_csv(output_csv, index=False, encoding='utf-8')
                    
                    # Update checkpoint
                    remaining_urls = urls_to_scrape[idx:]
                    self.save_progress_checkpoint(
                        checkpoint_file, 
                        absolute_index, 
                        len(all_urls),
                        scraped_urls,
                        remaining_urls
                    )
                    
                    print(f"✓ Error logged and progress saved")
                    continue
            
            # Final save
            final_df = pd.DataFrame(all_profiles_data)
            if 'pronouns' in final_df.columns:
                final_df = final_df.drop(columns=['pronouns'])
            final_df.to_csv(output_csv, index=False, encoding='utf-8')
            
            # Calculate statistics
            success_count = len([p for p in all_profiles_data if p.get('status') == 'success'])
            partial_count = len([p for p in all_profiles_data if p.get('status') == 'partial_success'])
            failed_count = len([p for p in all_profiles_data if p.get('status') in ['failed', 'error']])
            
            print(f"\n{'='*70}")
            print(f"🎉 SCRAPING COMPLETED!")
            print(f"{'='*70}")
            print(f"📊 Total profiles in output: {len(all_profiles_data)}")
            print(f"   - Scraped in this session: {total_urls}")
            print(f"   - Previously scraped: {already_scraped}")
            print(f"\n📈 Status breakdown:")
            print(f"   ✅ Full success: {success_count}")
            print(f"   ⚠️  Partial success: {partial_count}")
            print(f"   ❌ Failed/Error: {failed_count}")
            print(f"\n💾 Results saved to: {output_csv}")
            print(f"📍 Checkpoint saved to: {checkpoint_file}")
            
            return final_df
            
        except KeyboardInterrupt:
            print("\n\nExiting gracefully...")
            return pd.read_csv(output_csv) if os.path.exists(output_csv) else None
            
        except Exception as e:
            print(f"\n✗ Error in batch scraping: {e}")
            import traceback
            traceback.print_exc()
            return None
        finally:
            if self.driver:
                print("\nClosing browser in 5 seconds...")
                time.sleep(5)
                self.driver.quit()

# USAGE EXAMPLE
if __name__ == "__main__":
    # Configuration

    EMAIL = LINKEDIN_USERNAME
    PASSWORD = LINKEDIN_PASSWORD
    
    timestamp = datetime.now().strftime("%m-%d-%y-%H")
    
    INPUT_CSV = f"linkedin_profiles/extracted_profiles_of_founders_04-24-26-20.csv"
    OUTPUT_CSV = f"linkedin_profiles/extracted_profiles_keydata_{timestamp}.csv"
    URL_COLUMN = "url"
    
    # Run Scraper
    scraper = LinkedInBatchScraper(EMAIL, PASSWORD)
    results = scraper.scrape_profiles_from_csv(
        input_csv=INPUT_CSV, 
        output_csv=OUTPUT_CSV,
        url_column=URL_COLUMN,
        resume=True
    )

    # Add additional columns
    if results is not None:
        file_path = OUTPUT_CSV
        df = pd.read_csv(file_path)

        if "pronouns" in df.columns:
            df = df.drop(columns=["pronouns"])

        if "connection_date" not in df.columns:
            df["connection_date"] = ""
        if "connection_note" not in df.columns:
            df["connection_note"] = ""
        if "connection_status" not in df.columns:
            df["connection_status"] = ""
        if "university" not in df.columns:
            df["university"] = ""

        df.to_csv(file_path, index=False)

        print("\n✅ Additional columns added successfully!")
        
        # Summary statistics
        print(f"\n{'='*70}")
        print("📊 EXTRACTION QUALITY SUMMARY")
        print(f"{'='*70}")
        print(f"✅ Full success: {len(df[df['status'] == 'success'])}")
        print(f"⚠️  Partial success: {len(df[df['status'] == 'partial_success'])}")
        print(f"❌ Failed: {len(df[df['status'].isin(['failed', 'error'])])}")
        
        # Sample data
        if len(df) > 0:
            print(f"\n{'='*70}")
            print("📋 SAMPLE OF EXTRACTED DATA")
            print(f"{'='*70}")
            display_columns = [col for col in ['name', 'headline', 'current_company', 'university', 'location', 'connections', 'status', 'fields_extracted'] if col in df.columns]
            print(df[display_columns].head())