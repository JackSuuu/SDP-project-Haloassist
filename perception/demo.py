#!/usr/bin/env python3
"""
Quick demo script for testing the perception system with Mac camera
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from main import PerceptionSystem


def main():
    print("=" * 60)
    print("Perception System - Quick Demo")
    print("=" * 60)
    print("\nThis demo will:")
    print("1. Use your Mac camera for testing")
    print("2. Detect objects using YOLO")
    print("3. Show haptic feedback simulation in console")
    print("4. Display real-time detection results")
    print("\nPress 'q' in the video window to quit")
    print("=" * 60)
    print()
    
    # Initialize with Mac-friendly settings
    system = PerceptionSystem(
        model_path='yolov8s-world.pt',  # Will auto-download if not present
        show_display=True,
        num_motors=8
    )
    
    # Run the system
    system.run()


if __name__ == '__main__':
    main()
