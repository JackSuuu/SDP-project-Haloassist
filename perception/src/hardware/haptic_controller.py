"""
Haptic Controller
Provides directional guidance using vibration motors.
2-motor (left/right) via I2C MUX + DRV2605 haptic drivers.

Uses Real-Time Playback (RTP) mode for continuous variable intensity.
Hardware: TCA9548A I2C multiplexer -> DRV2605 haptic drivers (ERM mode)
"""
from typing import Optional, Tuple
from pathlib import Path
import sys

config_dir = Path(__file__).parent.parent.parent / "config"
sys.path.insert(0, str(config_dir))

from run_config import RUN_CONFIG

# Haptic mapping knobs.
DEFAULT_MAX_INTENSITY = 0.65
CENTER_BAND = 0.22        # ±22% of half-width (~44% of frame) treated as center zone.
CENTER_INTENSITY = 0.25
INTENSITY_GAMMA = 1.8     # Emphasize differences as target moves away from center.
SUPPORT_RATIO = 0.08      # Non-dominant motor stays very weak for sharp L/R distinction.


class HapticController:
    """Controller for continuous variable haptic feedback via I2C MUX + DRV2605."""

    def __init__(self):
        self.drv_left = None
        self.drv_right = None
        self._available = False

        self.max_intensity = float(RUN_CONFIG.get("haptic_max_intensity", DEFAULT_MAX_INTENSITY))
        self.max_intensity = max(0.0, min(1.0, self.max_intensity))

        self._left_intensity = 0.0
        self._right_intensity = 0.0
        self.num_motors = 2

        try:
            import busio
            import board
            from adafruit_tca9548a import TCA9548A
            import adafruit_drv2605

            i2c = busio.I2C(board.SCL, board.SDA)
            mux = TCA9548A(i2c)

            self.drv_left = adafruit_drv2605.DRV2605(mux[6])
            self.drv_right = adafruit_drv2605.DRV2605(mux[7])

            self.drv_left.use_ERM()
            self.drv_right.use_ERM()

            self.drv_left.mode = adafruit_drv2605.MODE_REALTIME
            self.drv_right.mode = adafruit_drv2605.MODE_REALTIME

            self._available = True
            print("✅ Haptic motors initialized via I2C MUX (Real-Time Mode)")
        except Exception as e:
            print(f"⚠️  Haptic motors unavailable: {e}")

    def is_available(self) -> bool:
        return self._available

    def guide_to_target(
        self,
        target_center: Optional[Tuple[int, int]],
        frame_center: Tuple[int, int],
        frame_width: int,
    ):
        """
        Compute continuous left/right intensity mapping based on horizontal position.
        """
        _ = frame_center
        if target_center is None:
            self._left_intensity = 0.0
            self._right_intensity = 0.0
            return

        if frame_width <= 0:
            self._left_intensity = 0.0
            self._right_intensity = 0.0
            return

        frame_center_x = frame_center[0]
        offset = (target_center[0] - frame_center_x) / (frame_width / 2.0)
        offset = max(-1.0, min(1.0, offset))
        magnitude = abs(offset)

        # Include the exact boundary in the center zone to avoid edge flicker.
        if magnitude <= CENTER_BAND:
            self._left_intensity = CENTER_INTENSITY
            self._right_intensity = CENTER_INTENSITY
            return

        dominant = (magnitude ** INTENSITY_GAMMA) * self.max_intensity
        support = dominant * SUPPORT_RATIO

        if offset < 0:
            self._left_intensity = dominant
            self._right_intensity = support
        else:
            self._left_intensity = support
            self._right_intensity = dominant

    def calc_motor_strengths(
        self,
        target_center: Optional[Tuple[int, int]],
        frame_center: Tuple[int, int],
        frame_width: int,
    ):
        """Backward-compatible alias used by main.py."""
        self.guide_to_target(target_center, frame_center, frame_width)

    def update_motors(self):
        """
        Apply computed intensities to DRV2605 RTP registers.
        Call continuously in the main loop.
        """
        left_val = int(max(0.0, min(1.0, self._left_intensity)) * 127)
        right_val = int(max(0.0, min(1.0, self._right_intensity)) * 127)

        print(f"Motors Updated as Left Intensity: {self._left_intensity:.2f} -> {left_val}, Right Intensity: {self._right_intensity:.2f} -> {right_val}")

        if not self._available:
            return

        self.drv_left.realtime_value = left_val
        self.drv_right.realtime_value = right_val

    def stop(self):
        """Stop all motors gracefully."""
        self._left_intensity = 0.0
        self._right_intensity = 0.0
        if self._available:
            self.drv_left.realtime_value = 0
            self.drv_right.realtime_value = 0

    def cleanup(self):
        """Cleanup motor resources."""
        self.stop()
        print("Haptic motors cleaned up")
