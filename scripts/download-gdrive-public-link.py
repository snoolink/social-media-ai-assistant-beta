import os
import time
import re
from pathlib import Path
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException, NoSuchElementException
import requests

# Google Drive folder links
drive_links = [
    "https://drive.google.com/drive/folders/18x8vgUYSkp_TQBTqTQv_vvkDb2zIVl9C?usp=share_link",
    "https://drive.google.com/drive/folders/1BYku_2jrQgZdwLXvgEcOyE-B9kH2u71a?usp=share_link",
    "https://drive.google.com/drive/folders/15rIQelSHWGWiMsP8nrSXJgOCocnW6J5f",
    "https://drive.google.com/drive/folders/1QjKh1tW6hrn0T0FbyI0uJ5NePot5khE0?usp=sharing",
    "https://drive.google.com/drive/folders/1W7g2-rGTT1G4YzKP0yJM7rXDie3U2PML?usp=share_link",
    "https://drive.google.com/drive/folders/1cj5D6tLEk9cEltS3H7MJp4IHTs5E6GRv?usp=sharing",
    "https://drive.google.com/drive/folders/1Xs5kZY5HKKdC2lPs0LxEcU98A80n0Za-"
]

def setup_driver(download_dir):
    """Setup Chrome driver with download preferences"""
    chrome_options = Options()
    
    # Set download directory
    prefs = {
        "download.default_directory": download_dir,
        "download.prompt_for_download": False,
        "download.directory_upgrade": True,
        "safebrowsing.enabled": True
    }
    chrome_options.add_experimental_option("prefs", prefs)
    
    # Optional: Run headless (uncomment to hide browser)
    # chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--start-maximized")
    
    driver = webdriver.Chrome(options=chrome_options)
    return driver

def extract_folder_id(url):
    """Extract folder ID from Google Drive URL"""
    match = re.search(r'/folders/([a-zA-Z0-9_-]+)', url)
    return match.group(1) if match else None

def clean_filename(filename):
    """Clean filename to remove 'image' prefix and other artifacts"""
    if not filename:
        return None
    
    # Remove common prefixes like "image", "video", etc.
    filename = re.sub(r'^(image|video|file)\s*', '', filename, flags=re.IGNORECASE)
    
    # Remove leading/trailing whitespace
    filename = filename.strip()
    
    # If filename is empty after cleaning, return None
    if not filename:
        return None
    
    return filename

def get_file_list(driver):
    """Get list of files with their IDs and names from the current folder"""
    try:
        # Wait for the grid view to load
        WebDriverWait(driver, 15).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "div[data-id]"))
        )
        time.sleep(3)
        
        files_info = []
        
        # Find all file items with data-id attribute
        file_elements = driver.find_elements(By.CSS_SELECTOR, "div[data-id]")
        
        for elem in file_elements:
            file_id = elem.get_attribute("data-id")
            if not file_id:
                continue
            
            # Try multiple ways to get the filename
            filename = None
            
            # Method 1: Look for filename in aria-label
            aria_label = elem.get_attribute("aria-label")
            if aria_label:
                # Extract filename from aria-label (usually format: "filename.ext")
                filename = aria_label.strip()
            
            # Method 2: Look for filename in child div with class containing name
            if not filename:
                try:
                    name_divs = elem.find_elements(By.CSS_SELECTOR, "div[data-tooltip], div.KL4NAf")
                    for div in name_divs:
                        tooltip = div.get_attribute("data-tooltip")
                        if tooltip:
                            filename = tooltip.strip()
                            break
                        text = div.text.strip()
                        if text:
                            filename = text
                            break
                except:
                    pass
            
            # Method 3: Try to find spans with filename
            if not filename:
                try:
                    spans = elem.find_elements(By.TAG_NAME, "span")
                    for span in spans:
                        text = span.text.strip()
                        if text and ('.' in text or len(text) > 3):
                            filename = text
                            break
                except:
                    pass
            
            # Clean the filename
            if filename:
                filename = clean_filename(filename)
            
            # Only add if we have both ID and filename
            if file_id and filename:
                files_info.append({
                    'id': file_id,
                    'name': filename
                })
        
        return files_info
        
    except TimeoutException:
        print("⚠️  Timeout waiting for files to load")
        return []
    except Exception as e:
        print(f"⚠️  Error getting file list: {str(e)}")
        return []

def download_file_direct(file_id, filename, output_dir):
    """Download file directly using requests with proper filename"""
    try:
        # Ensure filename has proper extension
        if '.' not in filename:
            filename = f"{filename}.bin"
        
        print(f"   📄 Downloading: {filename}")
        
        url = f"https://drive.google.com/uc?export=download&id={file_id}"
        
        session = requests.Session()
        response = session.get(url, stream=True, timeout=30)
        
        # Handle large file confirmation
        for key, value in response.cookies.items():
            if key.startswith('download_warning'):
                url = f"https://drive.google.com/uc?export=download&confirm={value}&id={file_id}"
                response = session.get(url, stream=True, timeout=30)
                break
        
        # Check if download was successful
        if response.status_code != 200:
            print(f"   ⚠️  HTTP {response.status_code}")
            return False
        
        # Save file
        filepath = os.path.join(output_dir, filename)
        
        # Download with progress
        total_size = int(response.headers.get('content-length', 0))
        block_size = 8192
        
        with open(filepath, 'wb') as f:
            if total_size == 0:
                # No content-length header, just download
                for chunk in response.iter_content(chunk_size=block_size):
                    if chunk:
                        f.write(chunk)
            else:
                # Show progress
                downloaded = 0
                for chunk in response.iter_content(chunk_size=block_size):
                    if chunk:
                        f.write(chunk)
                        downloaded += len(chunk)
        
        file_size = os.path.getsize(filepath)
        if file_size > 0:
            size_mb = file_size / (1024 * 1024)
            print(f"   ✅ Downloaded: {filename} ({size_mb:.2f} MB)")
            return True
        else:
            print(f"   ❌ File is empty")
            os.remove(filepath)
            return False
            
    except Exception as e:
        print(f"   ❌ Download failed: {str(e)}")
        return False

def download_folder(driver, folder_url, output_dir):
    """Download all files from a Google Drive folder"""
    folder_id = extract_folder_id(folder_url)
    
    if not folder_id:
        print(f"❌ Could not extract folder ID from: {folder_url}")
        return 0
    
    print(f"\n📁 Opening folder: {folder_id}")
    print(f"   URL: {folder_url}")
    
    # Navigate to folder
    driver.get(folder_url)
    
    # Wait for page to load completely
    time.sleep(5)
    
    # Get list of files
    print("   📋 Fetching file list...")
    files_info = get_file_list(driver)
    
    if not files_info:
        print("⚠️  No files found in folder")
        return 0
    
    print(f"   ✅ Found {len(files_info)} files\n")
    
    successful = 0
    for i, file_info in enumerate(files_info, 1):
        print(f"   [{i}/{len(files_info)}]", end=" ")
        
        if download_file_direct(file_info['id'], file_info['name'], output_dir):
            successful += 1
        
        # Wait between downloads to avoid rate limits
        time.sleep(2)
    
    return successful

def main():
    """Main function"""
    print("=" * 70)
    print("Google Drive Folder Downloader")
    print("=" * 70)
    
    # Create output directory
    output_dir = os.path.abspath("google_drive_downloads")
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    
    print(f"\n📂 Download directory: {output_dir}\n")
    
    # Setup driver
    print("🚀 Starting Chrome browser...")
    driver = setup_driver(output_dir)
    
    total_downloaded = 0
    total_folders = len(drive_links)
    
    try:
        for i, url in enumerate(drive_links, 1):
            print(f"\n{'='*70}")
            print(f"Processing Folder {i}/{total_folders}")
            print(f"{'='*70}")
            
            downloaded = download_folder(driver, url, output_dir)
            total_downloaded += downloaded
            
            print(f"\n✅ Folder {i} complete: {downloaded} files downloaded")
            
            # Wait between folders
            if i < total_folders:
                print("   ⏳ Waiting before next folder...")
                time.sleep(3)
        
    except KeyboardInterrupt:
        print("\n\n⚠️  Download interrupted by user")
    except Exception as e:
        print(f"\n\n❌ Error: {str(e)}")
    finally:
        print("\n🔚 Closing browser...")
        driver.quit()
    
    print(f"\n{'='*70}")
    print(f"📊 Download Summary")
    print(f"{'='*70}")
    print(f"  📁 Folders processed: {total_folders}")
    print(f"  ✅ Files downloaded: {total_downloaded}")
    print(f"  📂 Location: {output_dir}")
    print(f"{'='*70}\n")

if __name__ == "__main__":
    main()