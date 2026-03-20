"""
Haptic Controller
Provides directional guidance using vibration motors
2-motor (left/right) via I2C MUX + DRV2605 haptic drivers

Uses Real-Time Playback (RTP) mode for continuous variable intensity.
Hardware: TCA9548A I2C multiplexer → DRV2605 haptic drivers (ERM mode)
"""
import sys
from pathlib import Path
from typing import Tuple

# Add config directory to path
config_dir = Path(__file__).parent.parent.parent / 'config'
sys.path.insert(0, str(config_dir))

# Check simulation config early
try:
    import hardware_config
    SIMULATE_MOTORS = getattr(hardware_config, 'SIMULATE_MOTORS', False)
except ImportError:
    SIMULATE_MOTORS = False

if not SIMULATE_MOTORS:
    import busio
    import board
    from adafruit_tca9548a import TCA9548A
    import adafruit_drv2605

# Add visualization directory to path
viz_dir = Path(__file__).parent.parent.parent.parent / 'visualization'
sys.path.insert(0, str(viz_dir))

# Try to import visualizer client (optional)
try:
    from haptic_client import HapticVisualizer
    VISUALIZER_AVAILABLE = True
except ImportError:
    VISUALIZER_AVAILABLE = False


class HapticController:
    """Controller for continuous variable haptic feedback via I2C MUX + DRV2605."""

    def __init__(self, enable_visualizer: bool = True):
        # State tracking for continuous intensities (0.0 to 1.0)
        self._left_intensity = 0.0
        self._right_intensity = 0.0

        self.num_motors = 2
        self._current_target = None
        
        # Check simulation config
        self._simulate = SIMULATE_MOTORS

        if not self._simulate:
            # ---- I2C + HAPTIC SETUP ----
            i2c = busio.I2C(board.SCL, board.SDA)
            mux = TCA9548A(i2c)

            self.drv_left = adafruit_drv2605.DRV2605(mux[6])
            self.drv_right = adafruit_drv2605.DRV2605(mux[7])

            self.drv_left.use_ERM()
            self.drv_right.use_ERM()

            # Switch to Real-Time Playback (RTP) to allow continuous variable vibration
            self.drv_left.mode = adafruit_drv2605.MODE_REALTIME
            self.drv_right.mode = adafruit_drv2605.MODE_REALTIME
            print("✅ Haptic motors initialized via I2C MUX (Real-Time Mode)")
        else:
            print("⚠️ Haptic motors simulated (hardware IO disabled)")

        # Visualizer (optional, for web UI)
        self.visualizer = None
        if enable_visualizer and VISUALIZER_AVAILABLE:
            try:
                self.visualizer = HapticVisualizer("http://localhost:8000")
                print("📺 Web visualizer connected")
            except Exception:
                pass

    def set_target(self, target_object: str):
        """Set the current target object name for visualization"""
        self._current_target = target_object
        if self.visualizer:
            self.visualizer.searching(target_object)

    def notify_searching(self):
        """Notify the visualizer we are actively searching"""
        if self.visualizer and self._current_target:
            self.visualizer.searching(self._current_target)

    def guide_to_target(self, target_center: Tuple[int, int],
                        frame_center: Tuple[int, int],
                        frame_width: int):
        """
        Compute continuous intensity mapping based on horizontal position.
        """
        if target_center is None:
            # Drop intensity to 0 if no target is found this frame
            self._left_intensity = 0.0
            self._right_intensity = 0.0
            return

        # Normalize X position from 0.0 (far left) to 1.0 (far right)
        x_norm = target_center[0] / frame_width
        x_norm = max(0.0, min(1.0, x_norm))  # Clamp between 0 and 1

        # Left motor logic: 100% from x=0 to 0.5, then drops linearly to 0% at x=1.0
        self._left_intensity = min(1.0, 2.0 * (1.0 - x_norm))

        # Right motor logic: 0% at x=0, climbs to 100% at x=0.5, stays 100% to x=1.0
        self._right_intensity = min(1.0, 2.0 * x_norm)

        # Visualizer update (optional)
        if self.visualizer:
            position = 'left' if x_norm < 0.33 else ('right' if x_norm > 0.66 else 'center')
            self.visualizer.update_motors(
                left=self._left_intensity > 0,
                right=self._right_intensity > 0,
                intensity_left=self._left_intensity,
                intensity_right=self._right_intensity,
                target_object=self._current_target,
                position=position
            )

    def update_motors(self):
        """
        Applies the computed intensities directly to the DRV2605 chips.
        Call this continuously in your main loop.
        """
        # Convert 0.0-1.0 float to 0-127 integer for DRV2605 Real-Time Value register
        # (Adafruit's library uses 0-127 for positive amplitude ERM drive)
        left_val = int(self._left_intensity * 127)
        right_val = int(self._right_intensity * 127)

        # Drive the motors continuously at the calculated amplitude
        if not self._simulate:
            self.drv_left.realtime_value = left_val
            self.drv_right.realtime_value = right_val

    def stop(self):
        """Stop all motors gracefully"""
        self._left_intensity = 0.0
        self._right_intensity = 0.0
        if not self._simulate:
            self.drv_left.realtime_value = 0
            self.drv_right.realtime_value = 0
        if self.visualizer:
            self.visualizer.stop()

    def cleanup(self):
        """Cleanup motor resources"""
        self.stop()
        print("Haptic motors cleaned up")