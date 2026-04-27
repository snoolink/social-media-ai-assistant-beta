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
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from selenium.webdriver.common.keys import Keys
import pandas as pd
import time
from datetime import datetime
import os
import json

class LinkedInBatchScraper:
    def __init__(self, email, password):
        self.email = email
        self.password = password
        self.driver = None
        
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
            'pronouns': '',
            'headline': '',
            'current_company': '',
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
                    "h2._50d2f93f._7fbfc969.aa2681d5.e5a8a44f._80760f21._5e96a778._8c4cb82e.b071448a._18fe8cac._1c02a242",
                    "h2.text-heading-xlarge",
                    "h1.text-heading-xlarge",
                    "h1.inline.t-24.v-align-middle.break-words",
                ]
                
                name_element = None
                for selector in name_selectors:
                    try:
                        name_element = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, selector)))
                        break
                    except:
                        continue
                
                if name_element:
                    profile_data['name'] = name_element.text.strip()
                    profile_data['fields_extracted'].append('name')
                    print(f"✓ Found name: {profile_data['name']}")
            except Exception as e:
                print(f"✗ Could not find name: {e}")
            
            # Pronouns
            try:
                pronouns_selectors = [
                    "p._50d2f93f._6302b07e.e5a8a44f._80760f21.dac53a5e._8c4cb82e.b071448a._080dc437.a533ef56._1c02a242",
                ]
                
                for selector in pronouns_selectors:
                    try:
                        pronouns_elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                        for elem in pronouns_elements:
                            text = elem.text.strip()
                            if '/' in text and text not in ['· 1st', '· 2nd', '· 3rd']:
                                profile_data['pronouns'] = text
                                profile_data['fields_extracted'].append('pronouns')
                                print(f"✓ Found pronouns: {profile_data['pronouns']}")
                                break
                        if profile_data['pronouns']:
                            break
                    except:
                        continue
            except Exception as e:
                print(f"✗ Could not find pronouns: {e}")
            
            # Connection degree
            try:
                degree_selectors = [
                    "p._50d2f93f._6302b07e.e5a8a44f._80760f21.dac53a5e._8c4cb82e.b071448a._080dc437._18fe8cac._1c02a242",
                ]
                
                for selector in degree_selectors:
                    try:
                        degree_elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                        for elem in degree_elements:
                            text = elem.text.strip()
                            if text in ['· 1st', '· 2nd', '· 3rd']:
                                profile_data['connection_degree'] = text.replace('·', '').strip()
                                profile_data['fields_extracted'].append('connection_degree')
                                print(f"✓ Found connection degree: {profile_data['connection_degree']}")
                                break
                        if profile_data['connection_degree']:
                            break
                    except:
                        continue
            except Exception as e:
                print(f"✗ Could not find connection degree: {e}")
            
            # Headline
            try:
                headline_selectors = [
                    "p._50d2f93f._85da35fc.e5a8a44f._80760f21.dac53a5e._8c4cb82e.b071448a._18fe8cac._1c02a242",
                    "div.text-body-medium",
                    "div.text-body-medium.break-words",
                ]
                
                for selector in headline_selectors:
                    try:
                        headline = self.driver.find_element(By.CSS_SELECTOR, selector)
                        profile_data['headline'] = headline.text.strip()
                        profile_data['fields_extracted'].append('headline')
                        print(f"✓ Found headline: {profile_data['headline'][:50]}...")
                        break
                    except:
                        continue
            except Exception as e:
                print(f"✗ Could not find headline: {e}")
            
            # Current Company
            try:
                company_selectors = [
                    "p._50d2f93f._6302b07e.e5a8a44f._80760f21.dac53a5e._8c4cb82e.b071448a.d81d1e76._18fe8cac._1c02a242",
                    "div.text-body-small.inline.t-black--light.break-words",
                ]
                
                for selector in company_selectors:
                    try:
                        company = self.driver.find_element(By.CSS_SELECTOR, selector)
                        profile_data['current_company'] = company.text.strip()
                        profile_data['fields_extracted'].append('current_company')
                        print(f"✓ Found company: {profile_data['current_company']}")
                        break
                    except:
                        continue
            except Exception as e:
                print(f"✗ Could not find company: {e}")
            
            # Location
            try:
                location_selectors = [
                    "p._50d2f93f._6302b07e.aa2681d5.e5a8a44f._80760f21._5e96a778._8c4cb82e.b071448a.a533ef56._1c02a242",
                    "span.text-body-small.inline.t-black--light.break-words",
                ]
                
                location_container = self.driver.find_elements(By.CSS_SELECTOR, "div._8b73bec0._8d9ef486._5f473b7a.e1c05024._7a63c662._42821794")
                for container in location_container:
                    try:
                        location_p = container.find_element(By.CSS_SELECTOR, "p._50d2f93f._6302b07e.aa2681d5.e5a8a44f._80760f21._5e96a778._8c4cb82e.b071448a.a533ef56._1c02a242")
                        location_text = location_p.text.strip()
                        if location_text and location_text not in ['·'] and 'Contact info' not in location_text:
                            profile_data['location'] = location_text
                            profile_data['fields_extracted'].append('location')
                            print(f"✓ Found location: {profile_data['location']}")
                            break
                    except:
                        continue
            except Exception as e:
                print(f"✗ Could not find location: {e}")
            
            # Connections count
            try:
                connections_selectors = [
                    "p._50d2f93f._6302b07e.aa2681d5.e5a8a44f._80760f21._5e96a778._8c4cb82e.b071448a._5520be2e._1c02a242",
                    "span.t-black--light span[aria-hidden='true']",
                ]
                
                for selector in connections_selectors:
                    try:
                        connections_elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                        for elem in connections_elements:
                            text = elem.text.strip()
                            if 'connection' in text.lower():
                                profile_data['connections'] = text
                                profile_data['fields_extracted'].append('connections')
                                print(f"✓ Found connections: {profile_data['connections']}")
                                break
                        if profile_data['connections']:
                            break
                    except:
                        continue
            except Exception as e:
                print(f"✗ Could not find connections: {e}")
            
            # Mutual connections
            try:
                mutual_selectors = [
                    "p._50d2f93f._6302b07e._819511f0._9dddadca._4d4b9b10._085c5a25.a3306e30._59ef8e78",
                    "a._0afd2031._06d74129",
                ]
                
                for selector in mutual_selectors:
                    try:
                        mutual_elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                        for elem in mutual_elements:
                            text = elem.text.strip()
                            if 'mutual connection' in text.lower():
                                profile_data['mutual_connections'] = text
                                profile_data['fields_extracted'].append('mutual_connections')
                                print(f"✓ Found mutual connections: {profile_data['mutual_connections']}")
                                break
                        if profile_data['mutual_connections']:
                            break
                    except:
                        continue
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
                ]
                
                for selector in about_selectors:
                    try:
                        try:
                            see_more_button = self.driver.find_element(By.XPATH, "//button[contains(@aria-label, 'more')]")
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
            all_urls = df[url_column].dropna().tolist()
            
            # Load existing progress
            existing_df = None
            scraped_urls = set()
            
            if resume and os.path.exists(output_csv):
                try:
                    existing_df = pd.read_csv(output_csv)
                    scraped_urls = set(existing_df['profile_url'].tolist())
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
            print(f"📈 Completion: {round((already_scraped/len(all_urls)*100), 2)}%")
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
    
    INPUT_CSV = f"linkedin_profiles/extracted_profiles_of_tech_recs_04-24-26-20.csv"
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

        if "connection_date" not in df.columns:
            df["connection_date"] = ""
        if "connection_note" not in df.columns:
            df["connection_note"] = ""
        if "connection_status" not in df.columns:
            df["connection_status"] = ""

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
            display_columns = [col for col in ['name', 'headline', 'current_company', 'location', 'connections', 'status', 'fields_extracted'] if col in df.columns]
            print(df[display_columns].head())

