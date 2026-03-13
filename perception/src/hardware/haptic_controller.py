"""
Haptic Controller
Provides directional guidance using vibration motors.
2-motor (left/right) via I2C MUX + DRV2605 haptic drivers.

Uses non-blocking pulse approach (no time.sleep) to avoid latency.
Hardware: TCA9548A I2C multiplexer → DRV2605 haptic drivers (ERM mode)
"""
import time
from typing import Tuple

import busio
import board
from adafruit_tca9548a import TCA9548A
import adafruit_drv2605


class HapticController:
    """Controller for haptic feedback via I2C MUX + DRV2605.

    Motor updates are non-blocking: tracks timestamps and pulses
    motors for short durations each frame.
    """

    def __init__(self):
        i2c = busio.I2C(board.SCL, board.SDA)
        mux = TCA9548A(i2c)

        self.drv_left  = adafruit_drv2605.DRV2605(mux[6])
        self.drv_right = adafruit_drv2605.DRV2605(mux[7])

        self.drv_left.use_ERM()
        self.drv_right.use_ERM()

        self.drv_left.mode  = adafruit_drv2605.MODE_INTTRIG
        self.drv_right.mode = adafruit_drv2605.MODE_INTTRIG

        print("✅ Haptic motors initialized via I2C MUX (left=ch6, right=ch7)")

        # Tuning
        self.DEAD_ZONE      = 0.12
        self.MIN_INTERVAL   = 0.45
        self.MAX_INTERVAL   = 0.55
        self.PULSE_DURATION = 0.05

        self._last_pulse_time = 0
        self._pulse_end_time  = 0
        self._active_side     = None  # "left" or "right"

        # Per-frame state (reset each update_motors call)
        self._current_side     = None
        self._current_strength = 0.0

        self.num_motors = 2

    def guide_to_target(self, target_center: Tuple[int, int],
                        frame_center: Tuple[int, int],
                        frame_width: int):
        """
        Compute horizontal offset and set per-frame side/strength.

        Args:
            target_center: (x, y) pixel position of the target
            frame_center:  (x, y) centre of the frame
            frame_width:   width of the frame in pixels
        """
        if target_center is None:
            return

        offset = (target_center[0] - frame_width / 2) / (frame_width / 2)
        offset = max(-1.0, min(1.0, offset))

        if abs(offset) > self.DEAD_ZONE:
            self._current_strength = abs(offset)
            self._current_side     = "left" if offset < 0 else "right"

    def update_motors(self):
        """
        Non-blocking motor pulse — call once per main-loop iteration.
        """
        current_time = time.time()
        side     = self._current_side
        strength = self._current_strength

        # Pulse scheduling
        if side is not None:
            interval = self.MAX_INTERVAL - strength * (self.MAX_INTERVAL - self.MIN_INTERVAL)
            if current_time - self._last_pulse_time >= interval:
                self._pulse_end_time  = current_time + self.PULSE_DURATION
                self._last_pulse_time = current_time
                self._active_side     = side

        # Drive motors
        if current_time < self._pulse_end_time:
            if self._active_side == "left":
                self.drv_right.stop()
                self.drv_left.sequence[0] = adafruit_drv2605.Effect(47)
                self.drv_left.play()
            elif self._active_side == "right":
                self.drv_left.stop()
                self.drv_right.sequence[0] = adafruit_drv2605.Effect(47)
                self.drv_right.play()
        else:
            self.drv_left.stop()
            self.drv_right.stop()

        # Reset per-frame state
        self._current_side     = None
        self._current_strength = 0.0

    def stop(self):
        """Stop all motors immediately."""
        self.drv_left.stop()
        self.drv_right.stop()

    def cleanup(self):
        """Stop motors and release resources."""
        self.stop()
        print("Haptic motors cleaned up")
