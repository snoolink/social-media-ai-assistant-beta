#!/bin/bash
# Setup script for Video Orientation Detector on macOS
# This creates a virtual environment and installs OpenCV

echo "=========================================="
echo "Setting up Video Orientation Detector"
echo "=========================================="

# Create virtual environment
echo ""
echo "Step 1: Creating virtual environment..."
python3 -m venv video_env

# Activate virtual environment
echo ""
echo "Step 2: Activating virtual environment..."
source video_env/bin/activate

# Upgrade pip
echo ""
echo "Step 3: Upgrading pip..."
pip install --upgrade pip

# Install OpenCV
echo ""
echo "Step 4: Installing opencv-python..."
pip install opencv-python

# Verify installation
echo ""
echo "Step 5: Verifying installation..."
python -c "import cv2; print(f'✓ OpenCV {cv2.__version__} installed successfully!')"

echo ""
echo "=========================================="
echo "Setup Complete!"
echo "=========================================="
echo ""
echo "To use the video orientation detector:"
echo "1. Activate the virtual environment:"
echo "   source video_env/bin/activate"
echo ""
echo "2. Run the script:"
echo "   python video_orientation.py your_video.mp4"
echo ""
echo "3. When done, deactivate the environment:"
echo "   deactivate"
echo "=========================================="