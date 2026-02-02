"""
Haptic Feedback Module
Controls vibration motor array for directional guidance
"""
import time
from typing import Tuple
try:
    import RPi.GPIO as GPIO
    RPI_AVAILABLE = True
except ImportError:
    RPI_AVAILABLE = False
    print("RPi.GPIO not available - running in simulation mode")


class HapticFeedback:
    def __init__(self, motor_pins: list = None, num_motors: int = 8):
        """
        Initialize haptic feedback system
        
        Args:
            motor_pins: GPIO pins for motors (default: [17,18,27,22,23,24,25,4])
            num_motors: Number of motors in array (6-8)
        """
        self.num_motors = num_motors
        
        if motor_pins is None:
            # Default GPIO pins for Raspberry Pi
            self.motor_pins = [17, 18, 27, 22, 23, 24, 25, 4][:num_motors]
        else:
            self.motor_pins = motor_pins[:num_motors]
        
        self.simulation_mode = not RPI_AVAILABLE
        
        if not self.simulation_mode:
            GPIO.setmode(GPIO.BCM)
            for pin in self.motor_pins:
                GPIO.setup(pin, GPIO.OUT)
                GPIO.output(pin, GPIO.LOW)
    
    def calculate_direction(self, target_pos: Tuple[int, int], 
                          frame_center: Tuple[int, int]) -> int:
        """
        Calculate which motor(s) to activate based on target position
        
        Args:
            target_pos: (x, y) position of target object
            frame_center: (x, y) center of frame
            
        Returns:
            Motor index (0 = right, increasing counter-clockwise)
        """
        dx = target_pos[0] - frame_center[0]
        dy = target_pos[1] - frame_center[1]
        
        # Calculate angle (-180 to 180, 0 = right)
        import math
        angle = math.atan2(-dy, dx)  # Negative dy because y increases downward
        angle_deg = math.degrees(angle)
        
        # Map angle to motor index
        # 0: Right, 1: Top-right, 2: Top, 3: Top-left, 
        # 4: Left, 5: Bottom-left, 6: Bottom, 7: Bottom-right
        sector = int(((angle_deg + 180) / 360) * self.num_motors) % self.num_motors
        
        return sector
    
    def activate_motor(self, motor_idx: int, duration: float = 0.2, intensity: float = 1.0):
        """
        Activate specific motor
        
        Args:
            motor_idx: Index of motor to activate (0 to num_motors-1)
            duration: Vibration duration in seconds
            intensity: Intensity (0.0 to 1.0) - for PWM control
        """
        if motor_idx < 0 or motor_idx >= self.num_motors:
            return
        
        if self.simulation_mode:
            directions = ['→', '↗', '↑', '↖', '←', '↙', '↓', '↘']
            direction = directions[motor_idx % 8]
            print(f"[HAPTIC] Motor {motor_idx} ({direction}) - Duration: {duration:.2f}s, Intensity: {intensity:.1f}")
        else:
            pin = self.motor_pins[motor_idx]
            GPIO.output(pin, GPIO.HIGH)
            time.sleep(duration)
            GPIO.output(pin, GPIO.LOW)
    
    def guide_to_target(self, target_pos: Tuple[int, int], 
                       frame_center: Tuple[int, int],
                       distance_score: float = 0.5):
        """
        Provide haptic guidance towards target
        
        Args:
            target_pos: (x, y) position of target
            frame_center: (x, y) center of frame
            distance_score: 0.0 (far) to 1.0 (close)
        """
        motor_idx = self.calculate_direction(target_pos, frame_center)
        
        # Adjust duration based on distance (shorter = closer)
        duration = 0.1 + (1.0 - distance_score) * 0.3
        
        self.activate_motor(motor_idx, duration=duration)
    
    def cleanup(self):
        """Clean up GPIO resources"""
        if not self.simulation_mode:
            GPIO.cleanup()
