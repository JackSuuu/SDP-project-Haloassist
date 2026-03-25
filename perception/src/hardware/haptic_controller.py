"""
Haptic Controller
Provides directional guidance using vibration motors.
2-motor (left/right) via I2C MUX + DRV2605 haptic drivers.

Uses Real-Time Playback (RTP) mode for continuous variable intensity.
Hardware: TCA9548A I2C multiplexer -> DRV2605 haptic drivers (ERM mode)
"""
import time
from typing import Optional, Tuple


class HapticController:
    """Controller for continuous variable haptic feedback via I2C MUX + DRV2605."""

    def __init__(self, haptic_config: Optional[dict] = None):
        haptic_config = haptic_config or {}

        self.drv_left = None
        self.drv_right = None
        self._available = False

        self._left_intensity = 0.0
        self._right_intensity = 0.0
        self.num_motors = 2

        # Optional pulse gating to reduce constant motor-induced camera shake.
        self._pulse_enabled = bool(haptic_config.get('enable_pulsing', False))
        self._pulse_interval = max(0.01, float(haptic_config.get('pulse_interval', 0.5)))
        self._pulse_duration = max(0.01, float(haptic_config.get('pulse_duration', 0.05)))
        self._pulse_active_until = 0.0
        self._last_pulse_start = -self._pulse_interval

        try:
            import busio
            import board
            from adafruit_tca9548a import TCA9548A
            import adafruit_drv2605

            i2c = busio.I2C(board.SCL, board.SDA)
            mux = TCA9548A(i2c)

            self.drv_left = adafruit_drv2605.DRV2605(mux[1])
            self.drv_right = adafruit_drv2605.DRV2605(mux[2])

            self.drv_left.use_ERM()
            self.drv_right.use_ERM()

            self.drv_left.mode = adafruit_drv2605.MODE_REALTIME
            self.drv_right.mode = adafruit_drv2605.MODE_REALTIME

            self._available = True
            print("✅ Haptic motors initialized via I2C MUX (Real-Time Mode)")
            print(
                f"Haptic pulse mode: {'enabled' if self._pulse_enabled else 'disabled'} "
                f"(interval={self._pulse_interval:.2f}s, duration={self._pulse_duration:.2f}s)"
            )
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

        x_norm = target_center[0] / frame_width
        x_norm = max(0.0, min(0.5, x_norm))

        self._left_intensity = min(0.5, 2.0 * (0.5 - x_norm))
        self._right_intensity = min(0.5, 2.0 * x_norm)

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

        if self._pulse_enabled and (left_val > 0 or right_val > 0):
            now = time.monotonic()
            in_pulse_window = now <= self._pulse_active_until

            if not in_pulse_window and (now - self._last_pulse_start) >= self._pulse_interval:
                self._last_pulse_start = now
                self._pulse_active_until = now + self._pulse_duration
                in_pulse_window = True

            if not in_pulse_window:
                left_val = 0
                right_val = 0
        elif left_val == 0 and right_val == 0:
            self._pulse_active_until = 0.0

        if not self._available:
            return

        self.drv_left.realtime_value = left_val
        self.drv_right.realtime_value = right_val

    def stop(self):
        """Stop all motors gracefully."""
        self._left_intensity = 0.0
        self._right_intensity = 0.0
        self._pulse_active_until = 0.0
        if self._available:
            self.drv_left.realtime_value = 0
            self.drv_right.realtime_value = 0

    def cleanup(self):
        """Cleanup motor resources."""
        self.stop()
        print("Haptic motors cleaned up")
