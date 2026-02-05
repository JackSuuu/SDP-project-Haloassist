#!/usr/bin/env python3
"""
Main demo script for Raspberry Pi
Full workflow: Button → Speech → Detection → Haptic Guidance
"""
import sys
import os

# Add perception/src to path
perception_src = os.path.join(os.path.dirname(__file__), '..', 'perception', 'src')
sys.path.insert(0, perception_src)

from main import PerceptionSystem


def main():
    print("=" * 60)
    print("Perception System - Raspberry Pi Demo")
    print("=" * 60)
    print("\nFull Workflow Pipeline:")
    print("1. 🔘 Press button (GPIO 5)")
    print("2. 🎤 Say object name (e.g., 'bottle', 'cup', 'phone')")
    print("3. 🎯 Camera detects ONLY that specific object")
    print("4. 📳 Haptic feedback guides you:")
    print("   - Left object → Left motor vibrates (GPIO 22)")
    print("   - Right object → Right motor vibrates (GPIO 26)")
    print("   - Center object → Both motors vibrate")
    print()
    print("Hardware Setup:")
    print("- Button: GPIO 5 → GND")
    print("- Left Motor: GPIO 22")
    print("- Right Motor: GPIO 26")
    print("- Camera: CSI port")
    print("\nPress Ctrl+C to quit")
    print("=" * 60)
    print()
    
    # Initialize with Pi settings
    system = PerceptionSystem(
        model_name='nano',  # yolov8n.pt - tested on Pi3
        show_display=False,  # No display on Pi (headless)
        enable_speech=True   # Enable full STT workflow
    )
    
    # Run the system
    system.run()


if __name__ == '__main__':
    main()
