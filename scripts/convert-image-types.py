import os
from pathlib import Path
from PIL import Image
from pillow_heif import register_heif_opener

# Register HEIF opener with Pillow
register_heif_opener()

# Hard-coded folder path - change this to your desired folder
FOLDER_PATH = "/Users/jay/Downloads/mumbai-photos"

def convert_heic_to_png(folder_path):
    """
    Convert all HEIC images in the specified folder to PNG format.
    Keeps the same filename with .png extension.
    Ignores all other file types.
    """
    folder = Path(folder_path)
    
    if not folder.exists():
        print(f"Error: Folder '{folder_path}' does not exist!")
        return
    
    if not folder.is_dir():
        print(f"Error: '{folder_path}' is not a directory!")
        return
    
    # Find all HEIC files (case-insensitive)
    heic_files = list(folder.glob("*.heic")) + list(folder.glob("*.HEIC"))
    
    if not heic_files:
        print(f"No HEIC files found in '{folder_path}'")
        return
    
    print(f"Found {len(heic_files)} HEIC file(s) to convert...")
    
    converted = 0
    failed = 0
    
    for heic_file in heic_files:
        try:
            # Open HEIC image
            img = Image.open(heic_file)
            
            # Create PNG filename (same name, different extension)
            png_filename = heic_file.stem + ".png"
            png_path = folder / png_filename
            
            # Convert and save as PNG
            img.save(png_path, "PNG")
            
            print(f"✓ Converted: {heic_file.name} → {png_filename}")
            converted += 1
            
        except Exception as e:
            print(f"✗ Failed to convert {heic_file.name}: {str(e)}")
            failed += 1
    
    print(f"\nConversion complete!")
    print(f"Successfully converted: {converted}")
    print(f"Failed: {failed}")

if __name__ == "__main__":
    convert_heic_to_png(FOLDER_PATH)