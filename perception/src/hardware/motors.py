"""
Vibrational Motor Controller
Controls 2 vibrational motors for left/right directional guidance
"""
from typing import Tuple

try:
    import RPi.GPIO as GPIO
    RPI_AVAILABLE = True
except ImportError:
    RPI_AVAILABLE = False


class VibrationalMotorController:
    """
    Vibrational motor controller for 2-motor left/right guidance
    Outputs intensity for left and right motors based on object position
    
    Hardware Function Signature:
        vibrational_motor_control(set=True, intensity=50, motor=[1,1])
    
    Where:
        - set: True to activate, False to deactivate
        - intensity: 0-100% power level
        - motor: [left_motor, right_motor] where 1=active, 0=inactive
    """
    
    def __init__(self, left_motor_pin: int = 17, right_motor_pin: int = 18, 
                 simulation_mode: bool = None):
        """
        Initialize motor controller
        
        Args:
            left_motor_pin: GPIO pin for left motor (default: 17)
            right_motor_pin: GPIO pin for right motor (default: 18)
            simulation_mode: Force simulation mode (None = auto-detect)
        """
        self.left_motor_pin = left_motor_pin
        self.right_motor_pin = right_motor_pin
        self.simulation_mode = not RPI_AVAILABLE if simulation_mode is None else simulation_mode
        
        self.left_pwm = None
        self.right_pwm = None
        
        if not self.simulation_mode:
            GPIO.setmode(GPIO.BCM)
            GPIO.setup(self.left_motor_pin, GPIO.OUT)
            GPIO.setup(self.right_motor_pin, GPIO.OUT)
            
            # Setup PWM for intensity control (1000 Hz frequency)
            self.left_pwm = GPIO.PWM(self.left_motor_pin, 1000)
            self.right_pwm = GPIO.PWM(self.right_motor_pin, 1000)
            self.left_pwm.start(0)
            self.right_pwm.start(0)
    
    def calculate_motor_intensities(self, target_x: int, frame_width: int, 
                                    distance_score: float = 1.0) -> Tuple[float, float]:
        """
        Calculate left and right motor intensities based on target position
        
        Output format: {LEFT: X%, RIGHT: Y%}
        - Object centered: LEFT: 50%, RIGHT: 50%
        - Object on left: LEFT: 100%, RIGHT: 30%
        - Object on right: LEFT: 30%, RIGHT: 100%
        
        Args:
            target_x: X position of target object
            frame_width: Width of camera frame
            distance_score: Score indicating closeness (0=far, 1=close)
            
        Returns:
            Tuple of (left_intensity, right_intensity) as percentages (0-100)
        """
        frame_center_x = frame_width / 2
        
        # Calculate horizontal offset (-1 = far left, 0 = center, 1 = far right)
        offset = (target_x - frame_center_x) / (frame_width / 2)
        offset = max(-1.0, min(1.0, offset))  # Clamp to [-1, 1]
        
        # Calculate base intensity based on distance
        base_intensity = distance_score * 100  # 0-100%
        
        if offset < -0.1:  # Object is on the left
            # Stronger left motor, weaker right motor
            left_intensity = base_intensity
            right_intensity = base_intensity * (1.0 + offset)  # Reduces as offset goes more negative
        elif offset > 0.1:  # Object is on the right
            # Stronger right motor, weaker left motor
            right_intensity = base_intensity
            left_intensity = base_intensity * (1.0 - offset)  # Reduces as offset goes more positive
        else:  # Object is centered (-0.1 to 0.1)
            # Both motors at equal intensity (50% when centered)
            left_intensity = base_intensity
            right_intensity = base_intensity
        
        # Ensure minimum intensity for active feedback
        if left_intensity > 10:
            left_intensity = max(30, left_intensity)
        if right_intensity > 10:
            right_intensity = max(30, right_intensity)
        
        return round(left_intensity, 1), round(right_intensity, 1)
    
    def vibrational_motor_control(self, set: bool = True, intensity: int = 50, 
                                  motor: list = [1, 1]):
        """
        Control vibrational motors
        This is the main interface matching the requested hardware function signature:
        vibrational_motor_control(set=True, intensity=50, motor=[1,1])
        
        Args:
            set: True to activate motors, False to deactivate
            intensity: Intensity percentage (0-100)
            motor: List [left_motor, right_motor] where 1=active, 0=inactive
        
        Example usage:
            vibrational_motor_control(set=True, intensity=50, motor=[1,1])  # Both at 50%
            vibrational_motor_control(set=True, intensity=100, motor=[1,0]) # Left at 100%
            vibrational_motor_control(set=False, intensity=0, motor=[0,0])  # Off
        
        TODO: Replace with actual external hardware function call
        Example: your_hardware_lib.vibrational_motor_control(set=set, intensity=intensity, motor=motor)
        """
        left_active = motor[0] == 1
        right_active = motor[1] == 1
        
        if not set:
            # Turn off motors
            if self.simulation_mode:
                print(f"[MOTOR] Deactivated - LEFT: 0%, RIGHT: 0%")
            else:
                self.left_pwm.ChangeDutyCycle(0)
                self.right_pwm.ChangeDutyCycle(0)
            return
        
        left_intensity = intensity if left_active else 0
        right_intensity = intensity if right_active else 0
        
        if self.simulation_mode:
            print(f"[MOTOR] Activated - LEFT: {left_intensity}%, RIGHT: {right_intensity}%")
        else:
            self.left_pwm.ChangeDutyCycle(left_intensity)
            self.right_pwm.ChangeDutyCycle(right_intensity)
    
    def set_motor_intensities(self, left_intensity: float, right_intensity: float):
        """
        Set motor intensities directly
        
        Args:
            left_intensity: Left motor intensity (0-100)
            right_intensity: Right motor intensity (0-100)
        """
        if self.simulation_mode:
            print(f"[MOTOR] LEFT: {left_intensity:.0f}%, RIGHT: {right_intensity:.0f}%")
        else:
            self.left_pwm.ChangeDutyCycle(left_intensity)
            self.right_pwm.ChangeDutyCycle(right_intensity)
    
    def cleanup(self):
        """Stop motors and cleanup GPIO resources"""
        if not self.simulation_mode:
            self.left_pwm.stop()
            self.right_pwm.stop()
            GPIO.cleanup([self.left_motor_pin, self.right_motor_pin])
