"""
Haptic Controller
Provides directional guidance using vibration motors
Supports 2-motor (left/right) or 8-motor (circular array) configurations
Based on hardware/yolo_haptic.py implementation
"""
import time
import sys
from pathlib import Path
from typing import Tuple, Dict, Optional

# Add config directory to path
config_dir = Path(__file__).parent.parent.parent / 'config'
sys.path.insert(0, str(config_dir))

from hardware_config import MOTOR_PINS, HAPTIC_CONFIG


class HapticController:
    """Controller for haptic feedback using vibration motors (2 or 8 motors)"""
    
    def __init__(self, motor_pins: Optional[Dict[str, int]] = None):
        """
        Initialize haptic controller
        
        Args:
            motor_pins: Dictionary of motor name to GPIO pin mapping
                       If None, uses configuration from hardware_config
                       Example: {'left': 22, 'right': 26} for 2 motors
                       Example: {'front': 17, 'front_right': 18, ...} for 8 motors
        """
        self.motor_pins = motor_pins or MOTOR_PINS
        self.motors = {}
        self.num_motors = len(self.motor_pins)
        self._is_pi = self._check_raspberry_pi()
        
        print(f"Initializing {self.num_motors}-motor haptic controller")
        
        if self._is_pi:
            self._setup_motors()
    
    def _check_raspberry_pi(self) -> bool:
        """Check if running on Raspberry Pi"""
        try:
            with open('/proc/device-tree/model', 'r') as f:
                model = f.read()
                return 'raspberry pi' in model.lower()
        except:
            return False
    
    def _setup_motors(self):
        """Setup PWM output devices for motors"""
        try:
            from gpiozero import PWMOutputDevice
            for name, pin in self.motor_pins.items():
                self.motors[name] = PWMOutputDevice(pin)
            print(f"Haptic motors initialized: {self.motor_pins}")
        except ImportError:
            print("Warning: gpiozero not available. Haptic feedback disabled.")
            self._is_pi = False
        except Exception as e:
            print(f"Warning: Failed to setup motors: {e}")
            self._is_pi = False
    
    def trigger_vibration(self, motor_strengths: Optional[Dict[str, float]] = None, 
                         duration: Optional[float] = None):
        """
        Vibrate motors with specified strengths
        
        Args:
            motor_strengths: Dictionary of motor name to strength (0.0 to 1.0)
                           Example: {'left': 0.5, 'right': 0.0}
            duration: Duration of vibration in seconds (uses config default if None)
        """
        if motor_strengths is None:
            motor_strengths = {}
        
        duration = duration or HAPTIC_CONFIG['default_duration']
        
        if not self._is_pi or not self.motors:
            # Simulate vibration on non-Pi systems
            active = {k: int(v*100) for k, v in motor_strengths.items() if v > 0}
            print(f"[HAPTIC] {active} for {duration}s")
            return
        
        try:
            # Set motor values
            for name, motor in self.motors.items():
                strength = motor_strengths.get(name, 0.0)
                motor.value = strength
            
            active = {k: int(v*100) for k, v in motor_strengths.items() if v > 0}
            print(f"Vibrating {active} for {duration}s")
            
            time.sleep(duration)
            
            # Turn off all motors
            for motor in self.motors.values():
                motor.off()
        except Exception as e:
            print(f"Error during vibration: {e}")
    
    def guide_to_target(self, target_center: Tuple[int, int], 
                       frame_center: Tuple[int, int],
                       frame_width: int):
        """
        Provide directional guidance to target object
        Supports both 2-motor and 8-motor configurations
        
        Args:
            target_center: (x, y) coordinates of target center
            frame_center: (x, y) coordinates of frame center
            frame_width: Width of the frame
        """
        if target_center is None:
            return
        
        x_center = target_center[0]
        strength = HAPTIC_CONFIG['default_strength']
        
        # 2-motor configuration (left/right)
        if self.num_motors == 2:
            # Left third: vibrate left motor
            if x_center < frame_width / 3:
                self.trigger_vibration({'left': strength, 'right': 0.0})
            # Right third: vibrate right motor
            elif x_center > 2 * frame_width / 3:
                self.trigger_vibration({'left': 0.0, 'right': strength})
            # Middle third: vibrate both motors
            else:
                self.trigger_vibration({'left': strength, 'right': strength})
        
        # 8-motor configuration (circular array)
        elif self.num_motors == 8:
            # Calculate angle from center (-180 to 180 degrees)
            import math
            dx = x_center - frame_center[0]
            dy = target_center[1] - frame_center[1]
            angle = math.atan2(dy, dx) * 180 / math.pi
            
            # Map angle to motor (8 directions)
            motor_map = [
                (0, 'right'), (45, 'front_right'), (90, 'front'),
                (135, 'front_left'), (180, 'left'), (-135, 'back_left'),
                (-90, 'back'), (-45, 'back_right')
            ]
            
            # Find closest motor
            closest = min(motor_map, key=lambda x: abs(x[0] - angle))
            motor_name = closest[1]
            
            # Activate closest motor
            self.trigger_vibration({motor_name: strength})
    
    def stop(self):
        """Stop all motors"""
        if self._is_pi and self.motors:
            try:
                for motor in self.motors.values():
                    motor.off()
            except Exception as e:
                print(f"Error stopping motors: {e}")
    
    def cleanup(self):
        """Cleanup motor resources"""
        if self._is_pi and self.motors:
            try:
                for motor in self.motors.values():
                    motor.off()
                print("Haptic motors cleaned up")
            except Exception as e:
                print(f"Error cleaning up motors: {e}")
