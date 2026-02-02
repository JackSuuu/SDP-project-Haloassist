"""
Two-Motor Haptic Feedback Module
Simplified haptic feedback using 2 vibrational motors (left and right)
for directional guidance
"""
from typing import Tuple
from hardware.motors import VibrationalMotorController


class TwoMotorHapticFeedback:
    """
    Haptic feedback system using 2 motors for left/right guidance
    Outputs format: {LEFT: X%, RIGHT: Y%}
    """
    
    def __init__(self, left_motor_pin: int = 17, right_motor_pin: int = 18,
                 simulation_mode: bool = None):
        """
        Initialize two-motor haptic feedback system
        
        Args:
            left_motor_pin: GPIO pin for left motor
            right_motor_pin: GPIO pin for right motor
            simulation_mode: Force simulation mode (None = auto-detect)
        """
        self.motor_controller = VibrationalMotorController(
            left_motor_pin=left_motor_pin,
            right_motor_pin=right_motor_pin,
            simulation_mode=simulation_mode
        )
    
    def provide_guidance(self, target_pos: Tuple[int, int], 
                        frame_shape: Tuple[int, int],
                        distance_score: float = 1.0) -> dict:
        """
        Provide haptic guidance towards target using 2-motor system
        
        Args:
            target_pos: (x, y) position of target object
            frame_shape: (height, width) of camera frame
            distance_score: 0.0 (far) to 1.0 (close)
            
        Returns:
            Dict with motor intensities: {'LEFT': X, 'RIGHT': Y}
        """
        target_x, target_y = target_pos
        frame_height, frame_width = frame_shape
        
        # Calculate motor intensities
        left_intensity, right_intensity = self.motor_controller.calculate_motor_intensities(
            target_x, frame_width, distance_score
        )
        
        # Set motor intensities
        self.motor_controller.set_motor_intensities(left_intensity, right_intensity)
        
        # Return feedback information
        feedback = {
            'LEFT': f"{left_intensity:.0f}%",
            'RIGHT': f"{right_intensity:.0f}%"
        }
        
        return feedback
    
    def stop_motors(self):
        """Stop all motor vibrations"""
        self.motor_controller.vibrational_motor_control(set=False, intensity=0, motor=[0, 0])
    
    def cleanup(self):
        """Clean up motor controller resources"""
        self.motor_controller.cleanup()
