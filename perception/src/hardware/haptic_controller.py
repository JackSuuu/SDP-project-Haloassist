"""
Haptic Controller
Provides directional guidance using vibration motors
Supports 2-motor (left/right) or 8-motor (circular array) configurations

Uses non-blocking pulse approach (no time.sleep) to avoid latency.
Ported from 1-integration branch: HaloAssistV2-backup/motor.py
"""
import time
import sys
from pathlib import Path
from typing import Tuple, Dict, Optional

# Add config directory to path
config_dir = Path(__file__).parent.parent.parent / 'config'
sys.path.insert(0, str(config_dir))

# Add visualization directory to path
viz_dir = Path(__file__).parent.parent.parent.parent / 'visualization'
sys.path.insert(0, str(viz_dir))

from hardware_config import MOTOR_PINS, HAPTIC_CONFIG

# Try to import visualizer client
try:
    from haptic_client import HapticVisualizer
    VISUALIZER_AVAILABLE = True
except ImportError:
    VISUALIZER_AVAILABLE = False


class HapticController:
    """Controller for haptic feedback using vibration motors (2 or 8 motors).
    
    Motor updates are **non-blocking**: instead of sleeping, the controller
    tracks timestamps and pulses motors for short durations each frame.
    """
    
    def __init__(self, motor_pins: Optional[Dict[str, int]] = None, enable_visualizer: bool = True):
        """
        Initialize haptic controller
        
        Args:
            motor_pins: Dictionary of motor name to GPIO pin mapping
            enable_visualizer: Whether to send updates to web visualizer
        """
        self.motor_pins = motor_pins or MOTOR_PINS
        self.motors = {}
        self.num_motors = len(self.motor_pins)
        self._is_pi = self._check_raspberry_pi()
        self._current_target = None
        
        # Non-blocking pulse state (replaces time.sleep latency)
        self.pulse_interval = HAPTIC_CONFIG.get('pulse_interval', 0.5)
        self.pulse_duration = HAPTIC_CONFIG.get('pulse_duration', 0.05)
        self._last_pulse_time = 0.0
        self._pulse_end_time = 0.0
        self._pending_strengths: Dict[str, float] = {}
        
        # Initialize visualizer
        self.visualizer = None
        if enable_visualizer and VISUALIZER_AVAILABLE:
            try:
                self.visualizer = HapticVisualizer("http://localhost:8000")
                print("📺 Web visualizer connected")
            except Exception as e:
                print(f"⚠️  Visualizer not available: {e}")
        
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
    
    def set_target(self, target_object: str):
        """Set the current target object name for visualization"""
        self._current_target = target_object
        # Notify visualizer we're now searching for this target
        if self.visualizer:
            self.visualizer.searching(target_object)
    
    def notify_searching(self):
        """Notify the visualizer we are actively searching (no detection yet)"""
        if self.visualizer and self._current_target:
            self.visualizer.searching(self._current_target)
    
    def trigger_vibration(self, motor_strengths: Optional[Dict[str, float]] = None, 
                         duration: Optional[float] = None,
                         position: Optional[str] = None):
        """
        Schedule a non-blocking motor pulse (no time.sleep).
        
        The actual GPIO writes happen in update_motors(), which must be
        called every iteration of the main loop.
        
        Args:
            motor_strengths: Dictionary of motor name to strength (0.0 to 1.0)
            duration: Ignored (kept for API compat) – pulse_duration is used.
            position: Position for visualizer ("left", "right", "center")
        """
        if motor_strengths is None:
            motor_strengths = {}
        
        # Store strengths for the pulse system
        self._pending_strengths = motor_strengths
        
        # Send update to visualizer
        if self.visualizer:
            left_strength = motor_strengths.get('left', 0.0)
            right_strength = motor_strengths.get('right', 0.0)
            self.visualizer.update_motors(
                left=left_strength > 0,
                right=right_strength > 0,
                intensity_left=left_strength,
                intensity_right=right_strength,
                target_object=self._current_target,
                position=position
            )
    
    def update_motors(self):
        """
        Non-blocking motor update – call once per main-loop iteration.
        
        Instead of sleeping, this method checks elapsed time and turns
        motors on/off in short pulses, preventing frame-rate drops.
        """
        current_time = time.time()
        left = self._pending_strengths.get('left', 0.0)
        right = self._pending_strengths.get('right', 0.0)
        
        # Start a new pulse if interval has elapsed and there is demand
        if (left > 0 or right > 0) and \
           current_time - self._last_pulse_time >= self.pulse_interval:
            self._pulse_end_time = current_time + self.pulse_duration
            self._last_pulse_time = current_time
        
        if not self._is_pi or not self.motors:
            # Simulation path – print only at pulse start
            if current_time < self._pulse_end_time and \
               current_time - self._last_pulse_time < 0.01:
                active = {k: int(v*100) for k, v in self._pending_strengths.items() if v > 0}
                if active:
                    print(f"[HAPTIC] pulse {active}")
            return
        
        try:
            if current_time < self._pulse_end_time:
                for name, motor in self.motors.items():
                    motor.value = self._pending_strengths.get(name, 0.0)
            else:
                for motor in self.motors.values():
                    motor.value = 0.0
        except Exception as e:
            print(f"Error during motor update: {e}")
    
    def guide_to_target(self, target_center: Tuple[int, int], 
                       frame_center: Tuple[int, int],
                       frame_width: int):
        """
        Provide directional guidance to target object.
        
        Uses smooth gradient motor strengths (from 1-integration branch)
        instead of fixed 3-zone thresholds for more intuitive feedback.
        
        Args:
            target_center: (x, y) coordinates of target center
            frame_center: (x, y) coordinates of frame center
            frame_width: Width of the frame
        """
        if target_center is None:
            return
        
        x_center = target_center[0]
        
        # 2-motor configuration – smooth gradient approach
        if self.num_motors == 2:
            # Normalised offset: -1 (far left) … 0 (centre) … +1 (far right)
            offset = (x_center - frame_width / 2) / (frame_width / 2)
            offset = max(-1.0, min(1.0, float(offset)))

            left_strength = max(0.0, -offset)
            right_strength = max(0.0, offset)

            # Add centre boost so both motors buzz when on-target
            center_strength = 1.0 - abs(offset)
            left_strength += 0.6 * center_strength
            right_strength += 0.6 * center_strength

            left_strength = min(1.0, left_strength)
            right_strength = min(1.0, right_strength)

            position = 'left' if offset < -0.33 else ('right' if offset > 0.33 else 'center')
            self.trigger_vibration(
                {'left': left_strength, 'right': right_strength},
                position=position,
            )
        
        # 8-motor configuration (circular array)
        elif self.num_motors == 8:
            import math
            dx = x_center - frame_center[0]
            dy = target_center[1] - frame_center[1]
            angle = math.atan2(dy, dx) * 180 / math.pi
            
            motor_map = [
                (0, 'right'), (45, 'front_right'), (90, 'front'),
                (135, 'front_left'), (180, 'left'), (-135, 'back_left'),
                (-90, 'back'), (-45, 'back_right')
            ]
            
            closest = min(motor_map, key=lambda x: abs(x[0] - angle))
            motor_name = closest[1]
            strength = HAPTIC_CONFIG['default_strength']
            self.trigger_vibration({motor_name: strength})
    
    def stop(self):
        """Stop all motors"""
        # Update visualizer
        if self.visualizer:
            self.visualizer.stop()
        
        if self._is_pi and self.motors:
            try:
                for motor in self.motors.values():
                    motor.off()
            except Exception as e:
                print(f"Error stopping motors: {e}")
    
    def cleanup(self):
        """Cleanup motor resources"""
        # Stop visualizer
        if self.visualizer:
            self.visualizer.stop()
        
        if self._is_pi and self.motors:
            try:
                for motor in self.motors.values():
                    motor.off()
                print("Haptic motors cleaned up")
            except Exception as e:
                print(f"Error cleaning up motors: {e}")
