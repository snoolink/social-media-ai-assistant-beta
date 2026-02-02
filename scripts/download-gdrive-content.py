import os
import io
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload
import pickle
import re

# If modifying these scopes, delete the file token.pickle.
SCOPES = ['https://www.googleapis.com/auth/drive.readonly']

def get_credentials():
    """Authenticate and get credentials"""
    creds = None
    
    # Token file stores user's access and refresh tokens
    if os.path.exists('token.pickle'):
        with open('token.pickle', 'rb') as token:
            creds = pickle.load(token)
    
    # If there are no valid credentials, let the user log in
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                'credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        
        # Save credentials for next run
        with open('token.pickle', 'wb') as token:
            pickle.dump(creds, token)
    
    return creds

def extract_folder_id(url):
    """Extract folder ID from Google Drive URL"""
    patterns = [
        r'/folders/([a-zA-Z0-9-_]+)',
        r'id=([a-zA-Z0-9-_]+)',
    ]
    
    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1)
    
    return None

def download_file(service, file_id, file_name, output_path):
    """Download a single file"""
    try:
        request = service.files().get_media(fileId=file_id)
        file_path = os.path.join(output_path, file_name)
        
        fh = io.FileIO(file_path, 'wb')
        downloader = MediaIoBaseDownload(fh, request)
        
        done = False
        print(f"  Downloading: {file_name}")
        while not done:
            status, done = downloader.next_chunk()
            if status:
                print(f"    Progress: {int(status.progress() * 100)}%", end='\r')
        print(f"    ✓ Complete: {file_name}")
        
    except Exception as e:
        print(f"    ✗ Error downloading {file_name}: {str(e)}")

def list_files_in_folder(service, folder_id):
    """List all files and folders in a Google Drive folder"""
    query = f"'{folder_id}' in parents and trashed=false"
    results = service.files().list(
        q=query,
        fields="files(id, name, mimeType)",
        pageSize=1000
    ).execute()
    
    return results.get('files', [])

def download_folder_recursive(service, folder_id, output_dir, folder_name=""):
    """Recursively download all files and subfolders"""
    # Create directory for current folder
    current_dir = os.path.join(output_dir, folder_name) if folder_name else output_dir
    os.makedirs(current_dir, exist_ok=True)
    
    print(f"\n📁 Processing folder: {folder_name or 'root'}")
    
    # Get all items in folder
    items = list_files_in_folder(service, folder_id)
    
    if not items:
        print("  (empty folder)")
        return
    
    # Separate files and folders
    files = [item for item in items if item['mimeType'] != 'application/vnd.google-apps.folder']
    folders = [item for item in items if item['mimeType'] == 'application/vnd.google-apps.folder']
    
    # Download files
    for file in files:
        # Skip Google Docs, Sheets, Slides (need export instead of download)
        if file['mimeType'].startswith('application/vnd.google-apps'):
            print(f"  ⚠ Skipping Google Doc/Sheet/Slide: {file['name']}")
            continue
        
        download_file(service, file['id'], file['name'], current_dir)
    
    # Recursively download subfolders
    for folder in folders:
        subfolder_path = folder['name']
        download_folder_recursive(service, folder['id'], current_dir, subfolder_path)

def main():
    print("=" * 70)
    print("Google Drive Folder Downloader (with Authentication)")
    print("=" * 70)
    
    # Your Google Drive folder URL
    drive_url = "https://drive.google.com/drive/u/3/folders/1UIHQNDz5Fwr50LlFF-_N0jgbQVS_2wNF"
    output_directory = "downloaded_files"
    
    # Extract folder ID
    folder_id = extract_folder_id(drive_url)
    if not folder_id:
        print("Error: Could not extract folder ID from URL")
        return
    
    print(f"\nFolder ID: {folder_id}")
    print(f"Output directory: {output_directory}")
    print("\nAuthenticating...")
    
    try:
        # Authenticate and create service
        creds = get_credentials()
        service = build('drive', 'v3', credentials=creds)
        
        print("✓ Authentication successful!")
        print("\nStarting download...")
        
        # Download folder contents
        download_folder_recursive(service, folder_id, output_directory)
        
        print("\n" + "=" * 70)
        print(f"✓ Download completed!")
        print(f"Files saved to: {os.path.abspath(output_directory)}")
        print("=" * 70)
        
    except Exception as e:
        print(f"\n✗ Error: {str(e)}")
        print("\nMake sure you have:")
        print("1. Created a Google Cloud project")
        print("2. Enabled the Google Drive API")
        print("3. Downloaded credentials.json to this directory")

if __name__ == "__main__":
    main()