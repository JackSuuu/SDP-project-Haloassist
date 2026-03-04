#!/usr/bin/env python3
"""
Local demo script for testing on Mac
Tests camera + YOLO detection without hardware dependencies
"""
import sys
import os

# Add perception/src to path
perception_src = os.path.join(os.path.dirname(__file__), '..', 'perception', 'src')
sys.path.insert(0, perception_src)

from main import PerceptionSystem


def main():
    print("=" * 60)
    print("Perception System - Mac Local Demo")
    print("=" * 60)
    print("\nMac Demo Mode:")
    print("- Camera detection only (no button/speech)")
    print("- Detects common objects from priority list")
    print("- Guides to closest object automatically")
    print("- Haptic feedback simulated in console")
    print()
    print("Output format:")
    print("  🎯 Closest: bottle at (320, 240) (conf: 0.85)")
    print("  [HAPTIC] {'left': 50} for 0.25s")
    print("\nPress 'q' in the video window to quit")
    print("=" * 60)
    print()
    
    # Initialize with Mac-friendly settings
    system = PerceptionSystem(
        model_name='world-small',  # YOLO-World for custom object detection
        show_display=True,
        enable_speech=False  # Disabled for Mac (no hardware)
    )
    
    print("💡 Running in continuous detection mode")
    print("   Detecting all objects and guiding to closest\n")
    
    # Run the system
    system.run()


if __name__ == '__main__':
    main()
