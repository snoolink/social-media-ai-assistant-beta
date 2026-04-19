#!/usr/bin/env python3
"""
Multi-Frame OCR
Extract frames at regular intervals and run OCR on each one
"""

import cv2
import pytesseract
from PIL import Image
import argparse
import sys
import os


def extract_and_ocr_frames(video_path, interval=1.0, output_dir='frames', min_confidence=30):
    """
    Extract frames at intervals and run OCR on each
    
    Args:
        video_path: Path to video file
        interval: Seconds between frames
        output_dir: Directory to save frames
        min_confidence: Minimum OCR confidence to display
    """
    # Check Tesseract
    try:
        pytesseract.get_tesseract_version()
    except Exception as e:
        print("Error: Tesseract OCR is not installed")
        return
    
    # Open video
    video = cv2.VideoCapture(video_path)
    if not video.isOpened():
        print(f"Error: Could not open video '{video_path}'")
        return
    
    # Get video info
    fps = video.get(cv2.CAP_PROP_FPS)
    total_frames = int(video.get(cv2.CAP_PROP_FRAME_COUNT))
    duration = total_frames / fps
    width = int(video.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(video.get(cv2.CAP_PROP_FRAME_HEIGHT))
    
    print(f"Video Information:")
    print(f"  File: {video_path}")
    print(f"  Resolution: {width}x{height}")
    print(f"  FPS: {fps:.2f}")
    print(f"  Duration: {duration:.2f} seconds")
    print(f"  Extracting frames every {interval} seconds")
    print("=" * 80)
    print()
    
    # Create output directory
    os.makedirs(output_dir, exist_ok=True)
    
    # Calculate frame positions
    frame_positions = []
    current_time = 0
    while current_time <= duration:
        frame_positions.append(current_time)
        current_time += interval
    
    print(f"Will extract {len(frame_positions)} frames\n")
    
    # Process each frame
    for idx, timestamp in enumerate(frame_positions):
        frame_number = int(timestamp * fps)
        
        # Read frame
        video.set(cv2.CAP_PROP_POS_FRAMES, frame_number)
        ret, frame = video.read()
        
        if not ret:
            continue
        
        # Save frame
        frame_filename = os.path.join(output_dir, f'frame_{idx:04d}_{timestamp:.1f}s.jpg')
        cv2.imwrite(frame_filename, frame)
        
        # Run OCR
        print(f"\n{'='*80}")
        print(f"Frame {idx + 1}/{len(frame_positions)} @ {timestamp:.2f}s")
        print(f"{'='*80}")
        
        try:
            # Convert to PIL Image for pytesseract
            image = Image.open(frame_filename)
            
            # Get simple text
            text = pytesseract.image_to_string(image)
            
            # Get detailed data
            data = pytesseract.image_to_data(image, output_type=pytesseract.Output.DICT)
            
            # Print text if found
            if text.strip():
                print(f"\n📄 TEXT FOUND:")
                print("-" * 80)
                print(text.strip())
                print("-" * 80)
                
                # Print word-by-word with confidence
                print(f"\n📊 DETAILS:")
                for i in range(len(data['text'])):
                    word = data['text'][i].strip()
                    if word:
                        try:
                            conf = int(data['conf'][i])
                            if conf >= min_confidence:
                                print(f"  '{word}' ({conf}%)")
                        except (ValueError, TypeError):
                            pass
            else:
                print(f"  [No text detected]")
        
        except Exception as e:
            print(f"  Error running OCR: {e}")
    
    video.release()
    
    print(f"\n{'='*80}")
    print(f"Complete! Frames saved to: {output_dir}/")
    print(f"{'='*80}")


def main():
    parser = argparse.ArgumentParser(
        description='Extract frames from video and run OCR on each',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Extract frames every 1 second and run OCR
  python multi_frame_ocr.py video.mp4
  
  # Extract frames every 5 seconds
  python multi_frame_ocr.py video.mp4 --interval 5
  
  # Custom output directory and lower confidence threshold
  python multi_frame_ocr.py video.mp4 --output my_frames --min-confidence 20
        """
    )
    
    parser.add_argument('video_path', help='Path to video file')
    parser.add_argument(
        '-i', '--interval',
        type=float,
        default=1.0,
        help='Seconds between frame extractions (default: 1.0)'
    )
    parser.add_argument(
        '-o', '--output',
        default='frames',
        help='Output directory for frames (default: frames/)'
    )
    parser.add_argument(
        '--min-confidence',
        type=int,
        default=30,
        help='Minimum confidence to show text (default: 30)'
    )
    
    args = parser.parse_args()
    
    extract_and_ocr_frames(
        args.video_path,
        interval=args.interval,
        output_dir=args.output,
        min_confidence=args.min_confidence
    )
    
    return 0

if __name__ == '__main__':
    sys.exit(main())