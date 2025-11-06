#!/usr/bin/env python3
"""
Sleeve Rolling Detector - Batch Processor
Analyzes all images in a folder and copies images with rolled sleeves to output folder
Uses Google Gemini AI API
"""

import os
import sys
import shutil
import json
import random
from pathlib import Path
from google import genai
from google.genai import types

def load_api_key():
    """Load and randomly select an API key from creds.json"""
    creds_file = Path(__file__).parent / "creds.json"
    
    if not creds_file.exists():
        print("Error: creds.json file not found in the script directory.")
        print("\nPlease create a creds.json file with the following format:")
        print('''
{
  "api_keys": [
    "YOUR_API_KEY_1",
    "YOUR_API_KEY_2",
    "YOUR_API_KEY_3",
    "YOUR_API_KEY_4",
    "YOUR_API_KEY_5"
  ]
}
        ''')
        sys.exit(1)
    
    try:
        with open(creds_file, 'r') as f:
            creds = json.load(f)
        
        api_keys = creds.get('api_keys', [])
        
        if not api_keys:
            print("Error: No API keys found in creds.json")
            sys.exit(1)
        
        # Randomly select one API key
        selected_key = random.choice(api_keys)
        print(f"Using API key: {selected_key[:20]}...")
        
        return selected_key
        
    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON format in creds.json: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"Error reading creds.json: {e}")
        sys.exit(1)

def get_mime_type(image_path):
    """Determine MIME type from file extension"""
    extension = Path(image_path).suffix.lower()
    mime_types = {
        '.jpg': 'image/jpeg',
        '.jpeg': 'image/jpeg',
        '.png': 'image/png',
        '.webp': 'image/webp',
        '.gif': 'image/gif',
        '.bmp': 'image/bmp'
    }
    return mime_types.get(extension, 'image/jpeg')

def is_image_file(filename):
    """Check if file is an image based on extension"""
    image_extensions = {'.jpg', '.jpeg', '.png', '.webp', '.gif', '.bmp', '.heic'}
    return Path(filename).suffix.lower() in image_extensions

def analyze_image(image_path, client):
    """
    Analyze a single image to detect sleeve rolling
    Returns: True if sleeves are being rolled, False otherwise
    """
    try:
        # Load image
        with open(image_path, 'rb') as f:
            image_bytes = f.read()
        
        mime_type = get_mime_type(image_path)
        
        # Create image part
        image = types.Part.from_bytes(
            data=image_bytes,
            mime_type=mime_type
        )
        
        # Generate content 
        prompt = """Find images of a person wearing a black long-sleeve shirt (e.g., dress shirt or button-up). The sleeves must be rolled up past the wrist and the forearms visible. Exclude t-shirts, polos, short-sleeve shirts, tank tops, and sleeveless garments.
Answer ONLY "Yes" or "No", followed by a brief explanation.
"""

        response = client.models.generate_content(
            model="gemini-2.0-flash-exp",
            contents=[prompt, image]
        )
        
        response_text = response.text.strip()
        
        # Check if response indicates sleeve rolling
        is_rolling = response_text.lower().startswith('yes')
        
        return is_rolling, response_text
        
    except Exception as e:
        print(f"  ⚠ Error analyzing {image_path}: {e}")
        return False, str(e)

def process_folder(input_folder, output_folder):
    """
    Process all images in input folder and copy matching ones to output folder
    """
    # Load API key from creds.json
    api_key = load_api_key()
    
    # Create client with API key directly
    client = genai.Client(api_key=api_key)
    
    # Create output folder if it doesn't exist
    os.makedirs(output_folder, exist_ok=True)
    
    # Get all image files
    input_path = Path(input_folder)
    if not input_path.exists():
        print(f"Error: Input folder '{input_folder}' does not exist.")
        sys.exit(1)
    
    image_files = [f for f in input_path.iterdir() if f.is_file() and is_image_file(f.name)]
    
    if not image_files:
        print(f"No image files found in '{input_folder}'")
        sys.exit(1)
    
    print(f"Found {len(image_files)} images to process")
    print(f"Output folder: {output_folder}")
    print("-" * 60)
    
    processed = 0
    matched = 0
    
    for image_file in image_files:
        print(f"\n[{processed + 1}/{len(image_files)}] Processing: {image_file.name}")
        
        is_rolling, explanation = analyze_image(image_file, client)
        
        if is_rolling:
            # Copy file to output folder with same filename
            output_path = Path(output_folder) / image_file.name
            shutil.copy2(image_file, output_path)
            print(f"  ✓ MATCH - Copied to output folder")
            print(f"  Response: {explanation}")
            matched += 1
        else:
            print(f"  ✗ No match")
            print(f"  Response: {explanation}")
        
        processed += 1
    
    print("\n" + "=" * 60)
    print(f"PROCESSING COMPLETE")
    print("=" * 60)
    print(f"Total images processed: {processed}")
    print(f"Images with rolled sleeves: {matched}")
    print(f"Output folder: {output_folder}")
    print("=" * 60 + "\n")

def main():
    """Main function"""
    if len(sys.argv) < 3:
        print("Usage: python sleeve_detector.py <input_folder> <output_folder>")
        print("\nExample:")
        print("  python sleeve_detector.py ./images ./rolled_sleeves")
        sys.exit(1)
    
    input_folder = sys.argv[1]
    output_folder = sys.argv[2]
    
    # Process folder
    process_folder(input_folder, output_folder)

if __name__ == "__main__":
    main()