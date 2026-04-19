#!/usr/bin/env python3
"""
Ultra-Simple Image OCR with HEIC Support
Extracts text from any image format including HEIC
"""

import sys
import os
from PIL import Image
import pytesseract


def convert_heic_to_jpg(heic_path):
    """
    Convert HEIC image to JPG
    
    Returns:
        Path to converted JPG file
    """
    try:
        from pillow_heif import register_heif_opener
        register_heif_opener()
        print("✓ HEIC support enabled")
        return None  # PIL can now open HEIC directly
    except ImportError:
        print("Note: pillow-heif not installed, attempting conversion...")
        
        # Try using pyheif if available
        try:
            import pyheif
            
            heif_file = pyheif.read(heic_path)
            image = Image.frombytes(
                heif_file.mode,
                heif_file.size,
                heif_file.data,
                "raw",
                heif_file.mode,
                heif_file.stride,
            )
            
            # Save as temporary JPG
            jpg_path = heic_path.rsplit('.', 1)[0] + '_converted.jpg'
            image.save(jpg_path, "JPEG")
            print(f"✓ Converted HEIC to: {jpg_path}")
            return jpg_path
            
        except ImportError:
            print("\nError: Cannot process HEIC files without additional libraries")
            print("\nInstall HEIC support with ONE of these:")
            print("  pip install pillow-heif")
            print("  OR")
            print("  pip install pyheif")
            print("\nAlternatively, convert the HEIC file to JPG manually:")
            print("  macOS: Open in Preview, File > Export > Format: JPEG")
            return None


def open_image(image_path):
    """
    Open image, handling HEIC format if needed
    """
    file_ext = os.path.splitext(image_path)[1].lower()
    
    if file_ext in ['.heic', '.heif']:
        # Try to handle HEIC
        converted_path = convert_heic_to_jpg(image_path)
        if converted_path:
            return Image.open(converted_path), converted_path
        else:
            # pillow_heif registered, can open directly
            return Image.open(image_path), None
    else:
        # Regular image format
        return Image.open(image_path), None


def main():
    if len(sys.argv) < 2:
        print("Usage: python heic_ocr.py <image_path>")
        print("\nExample:")
        print("  python heic_ocr.py photo.jpg")
        print("  python heic_ocr.py photo.HEIC")
        print("\nSupported formats: JPG, PNG, HEIC, HEIF, and more")
        sys.exit(1)
    
    image_path = sys.argv[1]
    
    try:
        # Check if file exists
        if not os.path.exists(image_path):
            print(f"Error: Image file '{image_path}' not found")
            sys.exit(1)
        
        print(f"Processing: {image_path}")
        print("=" * 80)
        
        # Open image (handles HEIC conversion if needed)
        image, temp_file = open_image(image_path)
        
        print(f"Image size: {image.size[0]}x{image.size[1]}")
        print("\nRunning OCR...")
        
        # Extract text
        text = pytesseract.image_to_string(image)
        
        # Print text
        print("\n📄 EXTRACTED TEXT:")
        print("-" * 80)
        if text.strip():
            print(text)
        else:
            print("[No text detected]")
        print("-" * 80)
        
        # Clean up temporary file if created
        if temp_file and os.path.exists(temp_file):
            os.remove(temp_file)
            print(f"\n(Temporary file removed: {temp_file})")
        
    except FileNotFoundError:
        print(f"Error: Image file '{image_path}' not found")
        sys.exit(1)
    except Exception as e:
        print(f"Error: {e}")
        print("\nMake sure Tesseract is installed:")
        print("  macOS:   brew install tesseract")
        print("  Ubuntu:  sudo apt-get install tesseract-ocr")
        print("  Windows: https://github.com/UB-Mannheim/tesseract/wiki")
        print("\nFor HEIC support, install:")
        print("  pip install pillow-heif")
        sys.exit(1)


if __name__ == '__main__':
    main()