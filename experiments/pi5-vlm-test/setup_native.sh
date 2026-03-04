#!/bin/bash

# Native Python setup for M1/M2/M3 Mac (ARM64)
# This is BETTER than Docker for Pi 5 testing since both are ARM64

echo "========================================================================"
echo "Native ARM64 Setup for Raspberry Pi 5 Latency Testing"
echo "Your M2 Pro Mac is ARM64, similar to Raspberry Pi 5!"
echo "========================================================================"
echo ""

# Check architecture
ARCH=$(uname -m)
echo "Detected architecture: $ARCH"

if [[ "$ARCH" != "arm64" ]]; then
    echo "⚠ Warning: You're on $ARCH, not ARM64"
    echo "Results may not reflect actual Pi 5 performance"
    echo ""
fi

# Check Python
if ! command -v python3 &> /dev/null; then
    echo "✗ Python 3 not found"
    echo "Install with: brew install python3"
    exit 1
fi

echo "✓ Python 3 found: $(python3 --version)"
echo ""

# Create virtual environment
echo "Creating virtual environment..."
python3 -m venv venv
source venv/bin/activate

echo "✓ Virtual environment created"
echo ""

# Upgrade pip
echo "Upgrading pip..."
pip install --upgrade pip setuptools wheel

echo ""
echo "========================================================================"
echo "Installing Dependencies"
echo "========================================================================"
echo ""

# Install PyTorch (M1/M2/M3 optimized)
echo "1. Installing PyTorch (Apple Silicon optimized)..."
pip install torch torchvision

# Install YOLO
echo ""
echo "2. Installing YOLOv8 (for fast detection)..."
pip install ultralytics

# Install Transformers for Qwen
echo ""
echo "3. Installing Transformers (for Qwen VLM)..."
pip install "transformers>=4.45.0" accelerate

# Install other dependencies
echo ""
echo "4. Installing other dependencies..."
pip install pillow numpy opencv-python-headless qwen-vl-utils einops timm sentencepiece

echo ""
echo "========================================================================"
echo "✓ Installation Complete!"
echo "========================================================================"
echo ""
echo "Your setup is ready for testing. Since you have M2 Pro (ARM64),"
echo "these tests will give you performance close to Raspberry Pi 5."
echo ""
echo "Quick Start:"
echo ""
echo "1. Activate virtual environment:"
echo "   source venv/bin/activate"
echo ""
echo "2. Test YOLO (fast detection):"
echo "   python test_yolo_detection.py test_images/door.jpg"
echo ""
echo "3. Test Qwen VLM (slower, more accurate):"
echo "   python test_qwen_vlm.py test_images/door.jpg"
echo ""
echo "4. Compare both models:"
echo "   python compare_models.py test_images/door.jpg"
echo ""
echo "Note: You need to add door images to test_images/ first"
echo "      Run: ./generate_test_images.sh"
echo ""
echo "========================================================================"
