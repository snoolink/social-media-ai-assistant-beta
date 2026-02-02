#!/usr/bin/env python3
"""
Video Orientation Detector
Identifies whether a video is horizontal (landscape) or vertical (portrait)
"""

import sys
import os

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
    
    # Check if file exists
    if not os.path.exists(video_path):
        return {"error": f"File not found: {video_path}"}
    
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
        orientation = "Horizontal (Landscape)"
    elif height > width:
        orientation = "Vertical (Portrait)"
    else:
        orientation = "Square"
    
    # Calculate aspect ratio
    aspect_ratio = width / height if height > 0 else 0
    
    return {
        "file": os.path.basename(video_path),
        "orientation": orientation,
        "width": width,
        "height": height,
        "aspect_ratio": f"{aspect_ratio:.2f}:1",
        "fps": f"{fps:.2f}",
        "frames": frame_count,
        "duration": f"{frame_count/fps:.2f}s" if fps > 0 else "N/A"
    }


def main():
    """Main function to handle command-line usage"""
    if len(sys.argv) < 2:
        print("Usage: python video_orientation.py <video_file_path>")
        print("Example: python video_orientation.py /path/to/video.mp4")
        sys.exit(1)
    
    video_path = sys.argv[1]
    result = get_video_orientation(video_path)
    
    if "error" in result:
        print(f"Error: {result['error']}")
        sys.exit(1)
    
    # Print results
    print("\n" + "="*50)
    print("VIDEO ORIENTATION ANALYSIS")
    print("="*50)
    print(f"File:         {result['file']}")
    print(f"Orientation:  {result['orientation']}")
    print(f"Resolution:   {result['width']} x {result['height']}")
    print(f"Aspect Ratio: {result['aspect_ratio']}")
    print(f"FPS:          {result['fps']}")
    print(f"Total Frames: {result['frames']}")
    print(f"Duration:     {result['duration']}")
    print("="*50 + "\n")


if __name__ == "__main__":
    main()

#/Users/jay/Downloads/IMG_3764.MOV - verticalsource 
#/Users/jay/Downloads/IMG_3765.MOV - horizontalsource 