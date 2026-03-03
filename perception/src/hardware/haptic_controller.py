"""
Haptic Controller
Provides directional guidance using vibration motors
Supports 2-motor (left/right) via I2C MUX + DRV2605 haptic drivers

Uses non-blocking pulse approach (no time.sleep) to avoid latency.
Hardware: TCA9548A I2C multiplexer → DRV2605 haptic drivers (ERM mode)
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

# Try to import MUX channel config
try:
    from hardware_config import MOTOR_MUX
except ImportError:
    MOTOR_MUX = {'left': 6, 'right': 7}

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
            motor_pins: Dictionary of motor name to GPIO pin mapping (legacy, unused with MUX)
            enable_visualizer: Whether to send updates to web visualizer
        """
        self.motor_pins = motor_pins or MOTOR_PINS
        self.motors = {}       # Legacy GPIO motors
        self.drv_motors = {}   # DRV2605 motors via I2C MUX
        self.num_motors = 2    # left + right via MUX
        self._is_pi = self._check_raspberry_pi()
        self._current_target = None
        self._use_mux = False  # Will be set True if MUX setup succeeds
        
        # Non-blocking pulse state – matches 7yolo.py tuning exactly
        self.DEAD_ZONE = 0.12        # center region where no vibration
        self.MIN_INTERVAL = 0.45     # fastest pulse (strongest offset)
        self.MAX_INTERVAL = 0.55     # slowest pulse (weakest offset)
        self.PULSE_DURATION = 0.05   # duration of each motor pulse
        
        self._last_pulse_time = 0.0
        self._pulse_end_time = 0.0
        self._active_side = None     # "left" or "right"
        
        # Per-frame detection state (reset each frame via guide_to_target)
        self._current_side = None    # which side to pulse this frame
        self._current_strength = 0.0 # how strong the offset is
        self._pending_strengths: Dict[str, float] = {}  # for visualizer compat
        
        # Initialize visualizer
        self.visualizer = None
        if enable_visualizer and VISUALIZER_AVAILABLE:
            try:
                self.visualizer = HapticVisualizer("http://localhost:8000")
                print("📺 Web visualizer connected")
            except Exception as e:
                print(f"⚠️  Visualizer not available: {e}")
        
        print(f"Initializing {self.num_motors}-motor haptic controller")
        
        # Always try MUX setup first (matches 7yolo.py – no platform check)
        self._setup_mux_motors()
    
    def _check_raspberry_pi(self) -> bool:
        """Check if running on Raspberry Pi"""
        try:
            with open('/proc/device-tree/model', 'r') as f:
                model = f.read()
                return 'raspberry pi' in model.lower()
        except:
            return False
    
    def _setup_mux_motors(self):
        """Setup DRV2605 haptic drivers via TCA9548A I2C multiplexer"""
        try:
            import busio
            import board
            from adafruit_tca9548a import TCA9548A
            import adafruit_drv2605
            
            i2c = busio.I2C(board.SCL, board.SDA)
            mux = TCA9548A(i2c)
            
            for name, channel in MOTOR_MUX.items():
                drv = adafruit_drv2605.DRV2605(mux[channel])
                drv.use_ERM()
                drv.mode = adafruit_drv2605.MODE_INTTRIG
                self.drv_motors[name] = drv
            
            self._use_mux = True
            self._is_pi = True  # MUX works, so we're on real hardware
            print(f"✅ Haptic motors initialized via I2C MUX: {MOTOR_MUX}")
        except ImportError as e:
            print(f"Warning: I2C/DRV2605 libraries not available ({e}). Trying GPIO fallback...")
            self._setup_gpio_motors()
        except Exception as e:
            print(f"Warning: Failed to setup MUX motors ({e}). Trying GPIO fallback...")
            self._setup_gpio_motors()
    
    def _setup_gpio_motors(self):
        """Legacy fallback: Setup PWM output devices for motors via GPIO"""
        try:
            from gpiozero import PWMOutputDevice
            for name, pin in self.motor_pins.items():
                self.motors[name] = PWMOutputDevice(pin)
            self._is_pi = True  # GPIO works, so we're on real hardware
            print(f"Haptic motors initialized (GPIO fallback): {self.motor_pins}")
        except ImportError:
            print("Warning: gpiozero not available. Haptic feedback disabled (simulation mode).")
            self._is_pi = False
        except Exception as e:
            print(f"Warning: Failed to setup GPIO motors: {e}")
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
        
        Logic matches 7yolo.py exactly:
        1. Use _current_side/_current_strength set by guide_to_target()
        2. Compute pulse interval from strength (stronger → faster)
        3. Drive DRV2605 Effect(47) on active side, stop the other
        4. Reset per-frame state so motors stop when no detection
        """
        current_time = time.time()
        side = self._current_side
        strength = self._current_strength
        
        # ---- PULSE LOGIC (identical to 7yolo.py) ----
        if side is not None:
            # Stronger offset = faster pulses
            interval = self.MAX_INTERVAL - strength * (self.MAX_INTERVAL - self.MIN_INTERVAL)
            
            if current_time - self._last_pulse_time >= interval:
                self._pulse_end_time = current_time + self.PULSE_DURATION
                self._last_pulse_time = current_time
                self._active_side = side
        
        # ---- DRIVE MOTORS (identical to 7yolo.py) ----
        # MUX + DRV2605 path
        if self._use_mux and self.drv_motors:
            try:
                import adafruit_drv2605
                if current_time < self._pulse_end_time:
                    if self._active_side == 'left':
                        self.drv_motors['right'].stop()
                        self.drv_motors['left'].sequence[0] = adafruit_drv2605.Effect(47)
                        self.drv_motors['left'].play()
                    elif self._active_side == 'right':
                        self.drv_motors['left'].stop()
                        self.drv_motors['right'].sequence[0] = adafruit_drv2605.Effect(47)
                        self.drv_motors['right'].play()
                else:
                    self.drv_motors['left'].stop()
                    self.drv_motors['right'].stop()
            except Exception as e:
                print(f"Error during MUX motor update: {e}")
        
        # Legacy GPIO path
        elif self._is_pi and self.motors:
            try:
                if current_time < self._pulse_end_time:
                    for name, motor in self.motors.items():
                        motor.value = self._pending_strengths.get(name, 0.0)
                else:
                    for motor in self.motors.values():
                        motor.value = 0.0
            except Exception as e:
                print(f"Error during GPIO motor update: {e}")
        
        # Simulation path (not on Pi)
        else:
            if current_time < self._pulse_end_time and \
               current_time - self._last_pulse_time < 0.01:
                if self._active_side:
                    print(f"[HAPTIC] pulse {self._active_side} (strength={strength:.0%})")
        
        # Reset per-frame state so next frame starts clean
        # (7yolo.py resets side=None, strength=0.0 at top of each loop)
        self._current_side = None
        self._current_strength = 0.0
    
    def guide_to_target(self, target_center: Tuple[int, int], 
                       frame_center: Tuple[int, int],
                       frame_width: int):
        """
        Provide directional guidance to target object.
        
        Logic matches 7yolo.py exactly:
        - Compute normalised offset from frame center
        - Apply dead zone (no vibration when centered)
        - Set single side + strength for pulse system
        
        Args:
            target_center: (x, y) coordinates of target center
            frame_center: (x, y) coordinates of frame center
            frame_width: Width of the frame
        """
        if target_center is None:
            return
        
        x_center = target_center[0]
        
        # ---- Identical to 7yolo.py offset calculation ----
        offset = (x_center - frame_width / 2) / (frame_width / 2)
        offset = max(-1.0, min(1.0, float(offset)))
        
        # Apply dead zone – no vibration when object is near center
        if abs(offset) > self.DEAD_ZONE:
            self._current_strength = abs(offset)
            
            if offset < 0:
                self._current_side = 'left'
            else:
                self._current_side = 'right'
        else:
            # Object is centered – no vibration needed
            self._current_side = None
            self._current_strength = 0.0
        
        # Update visualizer (keep compat with web UI)
        position = 'left' if offset < -0.33 else ('right' if offset > 0.33 else 'center')
        left_strength = abs(offset) if offset < 0 else 0.0
        right_strength = abs(offset) if offset > 0 else 0.0
        self.trigger_vibration(
            {'left': left_strength, 'right': right_strength},
            position=position,
        )
    
    def stop(self):
        """Stop all motors"""
        # Update visualizer
        if self.visualizer:
            self.visualizer.stop()
        
        # Stop DRV2605 motors via MUX
        if self._use_mux and self.drv_motors:
            try:
                for drv in self.drv_motors.values():
                    drv.stop()
            except Exception as e:
                print(f"Error stopping MUX motors: {e}")
        
        # Stop legacy GPIO motors
        if self._is_pi and self.motors:
            try:
                for motor in self.motors.values():
                    motor.off()
            except Exception as e:
                print(f"Error stopping GPIO motors: {e}")
    
    def cleanup(self):
        """Cleanup motor resources"""
        # Stop visualizer
        if self.visualizer:
            self.visualizer.stop()
        
        # Cleanup DRV2605 motors via MUX
        if self._use_mux and self.drv_motors:
            try:
                for drv in self.drv_motors.values():
                    drv.stop()
                print("Haptic motors (MUX/DRV2605) cleaned up")
            except Exception as e:
                print(f"Error cleaning up MUX motors: {e}")
        
        # Cleanup legacy GPIO motors
        if self._is_pi and self.motors:
            try:
                for motor in self.motors.values():
                    motor.off()
                print("Haptic motors (GPIO) cleaned up")
            except Exception as e:
                print(f"Error cleaning up GPIO motors: {e}")
