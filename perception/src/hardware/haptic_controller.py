"""
Haptic Controller
Provides directional guidance using vibration motors
2-motor (left/right) via I2C MUX + DRV2605 haptic drivers

Uses non-blocking pulse approach (no time.sleep) to avoid latency.
Hardware: TCA9548A I2C multiplexer → DRV2605 haptic drivers (ERM mode)

Identical motor logic to 7yolo.py — no fallbacks, no platform checks.
"""
import time
import sys
from pathlib import Path
from typing import Tuple, Dict, Optional

import busio
import board
from adafruit_tca9548a import TCA9548A
import adafruit_drv2605

# Add config directory to path
config_dir = Path(__file__).parent.parent.parent / 'config'
sys.path.insert(0, str(config_dir))

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
    """Controller for haptic feedback via I2C MUX + DRV2605.

    Motor updates are non-blocking: tracks timestamps and pulses
    motors for short durations each frame.
    """

    def __init__(self, enable_visualizer: bool = True):
        # ---- I2C + HAPTIC SETUP (identical to 7yolo.py) ----
        i2c = busio.I2C(board.SCL, board.SDA)
        mux = TCA9548A(i2c)

        self.drv_left = adafruit_drv2605.DRV2605(mux[6])
        self.drv_right = adafruit_drv2605.DRV2605(mux[7])

        self.drv_left.use_ERM()
        self.drv_right.use_ERM()

        self.drv_left.mode = adafruit_drv2605.MODE_INTTRIG
        self.drv_right.mode = adafruit_drv2605.MODE_INTTRIG

        print("✅ Haptic motors initialized via I2C MUX (left=ch6, right=ch7)")

        # ---- TUNING (identical to 7yolo.py) ----
        self.DEAD_ZONE = 0.12
        self.MIN_INTERVAL = 0.45
        self.MAX_INTERVAL = 0.55
        self.PULSE_DURATION = 0.05

        self._last_pulse_time = 0
        self._pulse_end_time = 0
        self._active_side = None  # "left" or "right"

        # Per-frame state (reset each frame)
        self._current_side = None
        self._current_strength = 0.0

        self.num_motors = 2
        self._is_pi = True
        self._current_target = None

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
        Compute offset and set per-frame side/strength.
        Identical to 7yolo.py FIND BEST DETECTION logic.
        """
        if target_center is None:
            return

        x_center = target_center[0]

        offset = (x_center - frame_width / 2) / (frame_width / 2)
        offset = max(-1, min(1, offset))

        if abs(offset) > self.DEAD_ZONE:
            self._current_strength = abs(offset)
            if offset < 0:
                self._current_side = "left"
            else:
                self._current_side = "right"

        # Visualizer update (optional)
        if self.visualizer:
            position = 'left' if offset < -0.33 else ('right' if offset > 0.33 else 'center')
            self.visualizer.update_motors(
                left=offset < 0,
                right=offset > 0,
                intensity_left=abs(offset) if offset < 0 else 0.0,
                intensity_right=abs(offset) if offset > 0 else 0.0,
                target_object=self._current_target,
                position=position
            )

    def update_motors(self):
        """
        Non-blocking motor pulse — call once per main-loop iteration.
        Identical to 7yolo.py PULSE LOGIC + DRIVE MOTORS sections.
        """
        current_time = time.time()
        side = self._current_side
        strength = self._current_strength

        # ---- PULSE LOGIC ----
        if side is not None:
            interval = self.MAX_INTERVAL - strength * (self.MAX_INTERVAL - self.MIN_INTERVAL)

            if current_time - self._last_pulse_time >= interval:
                self._pulse_end_time = current_time + self.PULSE_DURATION
                self._last_pulse_time = current_time
                self._active_side = side

        # ---- DRIVE MOTORS ----
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

        # Reset per-frame state (7yolo.py resets side=None at top of loop)
        self._current_side = None
        self._current_strength = 0.0

    def stop(self):
        """Stop all motors"""
        if self.visualizer:
            self.visualizer.stop()
        self.drv_left.stop()
        self.drv_right.stop()

    def cleanup(self):
        """Cleanup motor resources"""
        if self.visualizer:
            self.visualizer.stop()
        self.drv_left.stop()
        self.drv_right.stop()
        print("Haptic motors cleaned up")
