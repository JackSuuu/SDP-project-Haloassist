#!/usr/bin/env python3
"""
Hardware Integration Demo
Demonstrates the hardware-integrated perception system with 2-motor haptic feedback
"""
import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from hardware_main import HardwareIntegratedSystem

def main():
    """Run hardware demo in simulation mode"""
    print("="*60)
    print("Hardware Integration Demo - Simulation Mode")
    print("="*60)
    print()
    print("This demo simulates the hardware pipeline:")
    print("  Button Press -> TTS -> Camera Detection -> Motor Control")
    print()
    print("Hardware Components (Simulated):")
    print("  - Control Button: GPIO 5")
    print("  - Left Vibrational Motor: GPIO 17")
    print("  - Right Vibrational Motor: GPIO 18")
    print()
    print("Motor Output Format:")
    print("  - Object centered: LEFT: 50%, RIGHT: 50%")
    print("  - Object on left: LEFT: 100%, RIGHT: 30%")
    print("  - Object on right: LEFT: 30%, RIGHT: 100%")
    print()
    print("In simulation mode, button presses are auto-triggered.")
    print("="*60)
    print()
    
    # Create system in simulation mode
    system = HardwareIntegratedSystem(
        model_path='yolov8s-world.pt',
        button_pin=5,
        left_motor_pin=17,
        right_motor_pin=18,
        camera_id=0,
        simulation_mode=True  # Force simulation mode
    )
    
    # Run the system
    system.run()

if __name__ == '__main__':
    main()
