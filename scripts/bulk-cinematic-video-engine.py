#!/usr/bin/env python3
"""
Batch Video Orientation Detector
Processes folders recursively, identifies video orientations, and copies horizontal videos to output folder
"""

import sys
import os
import shutil
from pathlib import Path
from datetime import datetime

# CONFIGURATION 
# input folder - /Volumes/Seagate/Colorado 2025
OUTPUT_FOLDER = "/Users/jay/Desktop/CinematicVideosChicago"  # Change this to your desired output path
REPORT_FILE = "video_processing_report.txt"

# Supported video extensions
VIDEO_EXTENSIONS = {'.mp4', '.mov', '.avi', '.mkv', '.m4v', '.flv', '.wmv', '.mpg', '.mpeg', '.webm', '.3gp'}

def get_video_orientation(video_path):
    """
    Determine if a video is horizontal (landscape) or vertical (portrait)
    
    Args:
        video_path (str): Path to the video file
        
    Returns:
        dict: Information about the video orientation
    """
    try:
        import cv2
    except ImportError:
        print("Error: OpenCV (cv2) is not installed.")
        print("Install it with: pip install opencv-python")
        sys.exit(1)
    
    # Open the video file
    video = cv2.VideoCapture(video_path)
    
    if not video.isOpened():
        return {"error": f"Could not open video file: {video_path}"}
    
    # Get video properties
    width = int(video.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(video.get(cv2.CAP_PROP_FRAME_HEIGHT))
    fps = video.get(cv2.CAP_PROP_FPS)
    frame_count = int(video.get(cv2.CAP_PROP_FRAME_COUNT))
    
    # Release the video
    video.release()
    
    # Determine orientation
    if width > height:
        orientation = "Horizontal"
    elif height > width:
        orientation = "Vertical"
    else:
        orientation = "Square"
    
    # Calculate aspect ratio
    aspect_ratio = width / height if height > 0 else 0
    
    # Get file size
    file_size = os.path.getsize(video_path)
    file_size_mb = file_size / (1024 * 1024)
    
    return {
        "file": os.path.basename(video_path),
        "full_path": video_path,
        "orientation": orientation,
        "width": width,
        "height": height,
        "aspect_ratio": f"{aspect_ratio:.2f}",
        "fps": fps,
        "frames": frame_count,
        "duration": frame_count/fps if fps > 0 else 0,
        "file_size_mb": file_size_mb
    }


def find_all_videos(root_folder):
    """
    Recursively find all video files in a folder and its subfolders
    
    Args:
        root_folder (str): Root directory to search
        
    Returns:
        list: List of video file paths
    """
    video_files = []
    root_path = Path(root_folder)
    
    print(f"\nScanning folder: {root_folder}")
    print("Looking for video files...")
    
    for file_path in root_path.rglob('*'):
        if file_path.is_file() and file_path.suffix.lower() in VIDEO_EXTENSIONS:
            video_files.append(str(file_path))
    
    print(f"Found {len(video_files)} video files\n")
    return video_files


def copy_horizontal_video(source_path, output_folder):
    """
    Copy a horizontal video to the output folder, maintaining filename
    If filename exists, add a number suffix
    
    Args:
        source_path (str): Source video file path
        output_folder (str): Destination folder
        
    Returns:
        str: Destination file path
    """
    # Create output folder if it doesn't exist
    os.makedirs(output_folder, exist_ok=True)
    
    # Get the filename
    filename = os.path.basename(source_path)
    dest_path = os.path.join(output_folder, filename)
    
    # If file exists, add a number suffix
    counter = 1
    base_name, extension = os.path.splitext(filename)
    while os.path.exists(dest_path):
        new_filename = f"{base_name}_{counter}{extension}"
        dest_path = os.path.join(output_folder, new_filename)
        counter += 1
    
    # Copy the file
    shutil.copy2(source_path, dest_path)
    return dest_path


def generate_report(horizontal_videos, vertical_videos, square_videos, errors, report_path):
    """
    Generate a detailed text report of all processed videos
    
    Args:
        horizontal_videos (list): List of horizontal video info dicts
        vertical_videos (list): List of vertical video info dicts
        square_videos (list): List of square video info dicts
        errors (list): List of error messages
        report_path (str): Path to save the report
    """
    with open(report_path, 'w') as f:
        # Header
        f.write("="*80 + "\n")
        f.write("VIDEO PROCESSING REPORT\n")
        f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write("="*80 + "\n\n")
        
        # Summary
        f.write("SUMMARY\n")
        f.write("-" * 80 + "\n")
        f.write(f"Total Videos Processed: {len(horizontal_videos) + len(vertical_videos) + len(square_videos)}\n")
        f.write(f"Horizontal Videos: {len(horizontal_videos)}\n")
        f.write(f"Vertical Videos: {len(vertical_videos)}\n")
        f.write(f"Square Videos: {len(square_videos)}\n")
        f.write(f"Errors: {len(errors)}\n")
        f.write(f"Output Folder: {OUTPUT_FOLDER}\n")
        f.write("\n")
        
        # Horizontal Videos
        if horizontal_videos:
            f.write("="*80 + "\n")
            f.write("HORIZONTAL VIDEOS (COPIED TO OUTPUT FOLDER)\n")
            f.write("="*80 + "\n\n")
            for i, video in enumerate(horizontal_videos, 1):
                f.write(f"{i}. {video['file']}\n")
                f.write(f"   Path: {video['full_path']}\n")
                f.write(f"   Resolution: {video['width']} x {video['height']}\n")
                f.write(f"   Aspect Ratio: {video['aspect_ratio']}:1\n")
                f.write(f"   Duration: {video['duration']:.2f}s\n")
                f.write(f"   FPS: {video['fps']:.2f}\n")
                f.write(f"   File Size: {video['file_size_mb']:.2f} MB\n")
                f.write(f"   Status: ✓ Copied to output folder\n")
                f.write("\n")
        
        # Vertical Videos
        if vertical_videos:
            f.write("="*80 + "\n")
            f.write("VERTICAL VIDEOS (NOT COPIED)\n")
            f.write("="*80 + "\n\n")
            for i, video in enumerate(vertical_videos, 1):
                f.write(f"{i}. {video['file']}\n")
                f.write(f"   Path: {video['full_path']}\n")
                f.write(f"   Resolution: {video['width']} x {video['height']}\n")
                f.write(f"   Aspect Ratio: {video['aspect_ratio']}:1\n")
                f.write(f"   Duration: {video['duration']:.2f}s\n")
                f.write(f"   FPS: {video['fps']:.2f}\n")
                f.write(f"   File Size: {video['file_size_mb']:.2f} MB\n")
                f.write("\n")
        
        # Square Videos
        if square_videos:
            f.write("="*80 + "\n")
            f.write("SQUARE VIDEOS (NOT COPIED)\n")
            f.write("="*80 + "\n\n")
            for i, video in enumerate(square_videos, 1):
                f.write(f"{i}. {video['file']}\n")
                f.write(f"   Path: {video['full_path']}\n")
                f.write(f"   Resolution: {video['width']} x {video['height']}\n")
                f.write(f"   Duration: {video['duration']:.2f}s\n")
                f.write(f"   FPS: {video['fps']:.2f}\n")
                f.write(f"   File Size: {video['file_size_mb']:.2f} MB\n")
                f.write("\n")
        
        # Errors
        if errors:
            f.write("="*80 + "\n")
            f.write("ERRORS\n")
            f.write("="*80 + "\n\n")
            for i, error in enumerate(errors, 1):
                f.write(f"{i}. {error}\n")
            f.write("\n")
        
        f.write("="*80 + "\n")
        f.write("END OF REPORT\n")
        f.write("="*80 + "\n")


def main():
    """Main function to process videos in batch"""
    if len(sys.argv) < 2:
        print("Usage: python video_orientation_batch.py <root_folder_path>")
        print("Example: python video_orientation_batch.py /Users/jay/Videos")
        sys.exit(1)
    
    root_folder = sys.argv[1]
    
    # Check if folder exists
    if not os.path.exists(root_folder):
        print(f"Error: Folder not found: {root_folder}")
        sys.exit(1)
    
    if not os.path.isdir(root_folder):
        print(f"Error: Not a directory: {root_folder}")
        sys.exit(1)
    
    print("\n" + "="*80)
    print("BATCH VIDEO ORIENTATION PROCESSOR")
    print("="*80)
    print(f"Input Folder: {root_folder}")
    print(f"Output Folder: {OUTPUT_FOLDER}")
    print("="*80 + "\n")
    
    # Find all videos
    video_files = find_all_videos(root_folder)
    
    if not video_files:
        print("No video files found!")
        sys.exit(0)
    
    # Process videos
    horizontal_videos = []
    vertical_videos = []
    square_videos = []
    errors = []
    
    print("Processing videos...\n")
    for i, video_path in enumerate(video_files, 1):
        print(f"[{i}/{len(video_files)}] Processing: {os.path.basename(video_path)}")
        
        try:
            result = get_video_orientation(video_path)
            
            if "error" in result:
                errors.append(f"{video_path}: {result['error']}")
                print(f"   ✗ Error: {result['error']}")
                continue
            
            orientation = result['orientation']
            
            if orientation == "Horizontal":
                horizontal_videos.append(result)
                # Copy to output folder
                try:
                    dest_path = copy_horizontal_video(video_path, OUTPUT_FOLDER)
                    print(f"   ✓ Horizontal - Copied to: {os.path.basename(dest_path)}")
                except Exception as e:
                    errors.append(f"{video_path}: Failed to copy - {str(e)}")
                    print(f"   ✗ Error copying file: {str(e)}")
            elif orientation == "Vertical":
                vertical_videos.append(result)
                print(f"   ○ Vertical - Not copied")
            else:  # Square
                square_videos.append(result)
                print(f"   □ Square - Not copied")
                
        except Exception as e:
            errors.append(f"{video_path}: {str(e)}")
            print(f"   ✗ Error: {str(e)}")
    
    # Generate report
    report_path = os.path.join(root_folder, REPORT_FILE)
    generate_report(horizontal_videos, vertical_videos, square_videos, errors, report_path)
    
    # Print summary
    print("\n" + "="*80)
    print("PROCESSING COMPLETE")
    print("="*80)
    print(f"Total Videos Processed: {len(video_files)}")
    print(f"Horizontal Videos (copied): {len(horizontal_videos)}")
    print(f"Vertical Videos: {len(vertical_videos)}")
    print(f"Square Videos: {len(square_videos)}")
    print(f"Errors: {len(errors)}")
    print(f"\nHorizontal videos copied to: {OUTPUT_FOLDER}")
    print(f"Detailed report saved to: {report_path}")
    print("="*80 + "\n")


if __name__ == "__main__":
    main()

#/Volumes/Seagate/Smokies    