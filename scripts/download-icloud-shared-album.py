#!/usr/bin/env python3
"""
iCloud Shared Album Photo Downloader

This script automates downloading all photos from an iCloud shared album link.
It uses Selenium to interact with the iCloud web interface.

Requirements:
    pip install selenium webdriver-manager
"""

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.action_chains import ActionChains
import time
import os

class iCloudAlbumDownloader:
    def __init__(self, url, download_dir=None):
        """
        Initialize the downloader
        
        Args:
            url: iCloud shared album URL
            download_dir: Directory to save downloads (default: ./icloud_downloads)
        """
        self.url = url
        self.download_dir = download_dir or os.path.join(os.getcwd(), 'icloud_downloads')
        
        # Create download directory if it doesn't exist
        os.makedirs(self.download_dir, exist_ok=True)
        
        # Setup Chrome options
        self.chrome_options = webdriver.ChromeOptions()
        prefs = {
            "download.default_directory": self.download_dir,
            "download.prompt_for_download": False,
            "download.directory_upgrade": True,
            "safebrowsing.enabled": True
        }
        self.chrome_options.add_experimental_option("prefs", prefs)
        
        # Initialize driver
        self.driver = None
    
    def start_driver(self):
        """Initialize the Chrome WebDriver"""
        print("Starting Chrome WebDriver...")
        service = Service(ChromeDriverManager().install())
        self.driver = webdriver.Chrome(service=service, options=self.chrome_options)
        self.driver.maximize_window()
    
    def wait_for_download(self, timeout=30):
        """Wait for download to complete"""
        download_wait_time = 0
        while download_wait_time < timeout:
            # Check if there are any .crdownload files (Chrome's temp download files)
            temp_files = [f for f in os.listdir(self.download_dir) if f.endswith('.crdownload')]
            if not temp_files:
                time.sleep(1)  # Give it a second to ensure download is complete
                return True
            time.sleep(1)
            download_wait_time += 1
        return False
    
    def download_photos(self, max_photos=None, delay=2):
        """
        Download photos from the iCloud album
        
        Args:
            max_photos: Maximum number of photos to download (None for all)
            delay: Delay between downloads in seconds
        """
        try:
            self.start_driver()
            
            print(f"Opening iCloud album: {self.url}")
            self.driver.get(self.url)
            
            # Wait for page to load
            wait = WebDriverWait(self.driver, 20)
            
            # Wait for the album to load
            print("Waiting for album to load (2 minutes)...")
            time.sleep(120)  # Wait 2 minutes for page to fully load
            
            print("Starting download process...")
            
            # Create action chains for mouse movements
            actions = ActionChains(self.driver)
            
            photo_count = 0
            
            while True:
                if max_photos and photo_count >= max_photos:
                    print(f"\nReached maximum photo limit: {max_photos}")
                    break
                
                try:
                    # Move mouse to center of the page to make buttons visible
                    # Find the main photo/image area to hover over
                    try:
                        photo_element = self.driver.find_element(
                            By.CSS_SELECTOR, 
                            "img, .photo-view, .slideshow-item, [class*='photo'], [class*='image']"
                        )
                        actions.move_to_element(photo_element).perform()
                        print("Moved cursor to photo area to reveal buttons")
                        time.sleep(1)
                    except:
                        # If can't find photo element, just move to center of screen
                        viewport_width = self.driver.execute_script("return window.innerWidth")
                        viewport_height = self.driver.execute_script("return window.innerHeight")
                        actions.move_by_offset(viewport_width // 2, viewport_height // 2).perform()
                        print("Moved cursor to center of screen")
                        time.sleep(1)
                    
                    # Find and click the download button
                    download_btn = wait.until(EC.element_to_be_clickable(
                        (By.CSS_SELECTOR, "span.download.title.view.button, button[aria-label='Download'], .download-button")
                    ))
                    
                    print(f"\nDownloading photo {photo_count + 1}...")
                    download_btn.click()
                    
                    # Wait for download to complete
                    if self.wait_for_download():
                        photo_count += 1
                        print(f"Photo {photo_count} downloaded successfully")
                    else:
                        print(f"Warning: Download may not have completed for photo {photo_count + 1}")
                        photo_count += 1
                    
                    time.sleep(delay)
                    
                    # Find and click the next button
                    try:
                        # First, move cursor again to ensure next button is visible
                        try:
                            photo_element = self.driver.find_element(
                                By.CSS_SELECTOR, 
                                "img, .photo-view, .slideshow-item, [class*='photo'], [class*='image']"
                            )
                            actions.move_to_element(photo_element).perform()
                            time.sleep(0.5)
                        except:
                            pass
                        
                        next_btn = self.driver.find_element(
                            By.CSS_SELECTOR, 
                            "div.x-next-slideshow-item, button[aria-label='Next'], .next-button"
                        )
                        
                        # Move cursor to the next button to make it visible/active
                        actions.move_to_element(next_btn).perform()
                        time.sleep(0.5)
                        
                        # Check if next button is visible/enabled
                        is_displayed = next_btn.is_displayed()
                        style = next_btn.get_attribute('style')
                        
                        if is_displayed and 'display: none' not in (style or ''):
                            next_btn.click()
                            print("Moving to next photo...")
                            time.sleep(1)
                        else:
                            # Try clicking anyway as it might be hidden but functional
                            try:
                                next_btn.click()
                                print("Moving to next photo...")
                                time.sleep(1)
                            except:
                                print("\nNo more photos available (Next button not clickable)")
                                break
                            
                    except NoSuchElementException:
                        print("\nReached the end of the album (No next button found)")
                        break
                
                except TimeoutException:
                    print("\nCould not find download button. Possible end of album or page issue.")
                    break
                except Exception as e:
                    print(f"\nError during download: {str(e)}")
                    break
            
            print(f"\n{'='*50}")
            print(f"Download complete! Total photos downloaded: {photo_count}")
            print(f"Photos saved to: {self.download_dir}")
            print(f"{'='*50}")
            
        except Exception as e:
            print(f"\nAn error occurred: {str(e)}")
        
        finally:
            if self.driver:
                print("\nClosing browser...")
                time.sleep(2)
                self.driver.quit()

def main():
    # Example usage
    icloud_url = "https://www.icloud.com/sharedalbum/#B245oqs3q2TmTut;89E5B594-AF83-4EE2-863C-A3E194B874F7"
    
    # You can customize the download directory
    download_directory = "./icloud_photos"
    
    # Create downloader instance
    downloader = iCloudAlbumDownloader(icloud_url, download_directory)
    
    # Download all photos (or specify max_photos=10 to limit)
    # delay parameter controls seconds between downloads (adjust if needed)
    downloader.download_photos(max_photos=None, delay=2)


if __name__ == "__main__":
    main()