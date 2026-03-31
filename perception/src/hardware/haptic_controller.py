"""
Haptic Controller
Provides directional guidance using vibration motors.
2-motor (left/right) via I2C MUX + DRV2605 haptic drivers.

Uses Real-Time Playback (RTP) mode for continuous variable intensity.
Hardware: TCA9548A I2C multiplexer -> DRV2605 haptic drivers (ERM mode)
"""
import time
from typing import Optional, Tuple

import cv2
import numpy as np
import time
import argparse
import sys
from pathlib import Path
import datetime

# Ensure the project root is in sys.path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Ensure the config directory is in sys.path
config_dir = project_root / 'config'
sys.path.insert(0, str(config_dir))

from services.audio_feedback import AudioFeedback

DEFAULT_MAX_INTENSITY = 0.5
GRADIENT_EDGE_MARGIN = 0.15


def compute_motor_intensities(
    target_center: Optional[Tuple[int, int]],
    frame_width: int,
    max_intensity: float = DEFAULT_MAX_INTENSITY,
) -> Tuple[float, float]:
    """Compute left/right motor intensities from horizontal target position."""
    if target_center is None or frame_width <= 0:
        return 0.0, 0.0

    max_intensity = max(0.0, min(1.0, float(max_intensity)))
    x_norm = max(0.0, min(1.0, float(target_center[0]) / float(frame_width)))
    gradient_width = 1.0 - (2.0 * GRADIENT_EDGE_MARGIN)
    x_gradient = (x_norm - GRADIENT_EDGE_MARGIN) / gradient_width
    x_gradient = max(0.0, min(1.0, x_gradient))

    # Sharpened edge-to-center mapping in the middle 70% of frame.
    # x <= 0.15 -> (max, 0), x == 0.5 -> (max, max), x >= 0.85 -> (0, max)
    left_scale = min(1.0, (1.0 - x_gradient) / 0.5)
    right_scale = min(1.0, x_gradient / 0.5)
    left_intensity = max_intensity * left_scale
    right_intensity = max_intensity * right_scale

    return left_intensity, right_intensity


def test_all_channels():
    """Test all I2C channels for DRV2605 devices and vibrate motors."""
    try:
        import busio
        import board
        from adafruit_tca9548a import TCA9548A
        import adafruit_drv2605

        i2c = busio.I2C(board.SCL, board.SDA)
        mux = TCA9548A(i2c)

        found_channels = []

        for ch in range(8):
            print(f"Testing channel {ch}...")
            try:
                i2c_ch = mux[ch]
                drv = adafruit_drv2605.DRV2605(i2c_ch)
                drv.sequence[0] = adafruit_drv2605.Effect(47)  # buzz
                drv.play()
                time.sleep(0.3)
                drv.stop()
                print(f"  -> Successfully vibrated motor on channel {ch}")
                found_channels.append(ch)

                if len(found_channels) == 2:
                    break
            except Exception as e:
                print(f"  -> Failed to vibrate motor on channel {ch}: {e}")

        if len(found_channels) >= 2:
            return found_channels[0], found_channels[1]
        else:
            return None

    except Exception as e:
        print(f"Error during channel testing: {e}")
        return None


class HapticController:
    """Controller for continuous variable haptic feedback via I2C MUX + DRV2605."""

    def __init__(self, haptic_config: Optional[dict] = None):
        haptic_config = haptic_config or {}

        self.drv_left = None
        self.drv_right = None
        self._available = False

        self._left_intensity = 0.0
        self._right_intensity = 0.0
        configured_max_intensity = haptic_config.get(
            'max_intensity',
            haptic_config.get('default_strength', DEFAULT_MAX_INTENSITY),
        )
        self._max_intensity = max(0.01, min(1.0, float(configured_max_intensity)))
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

            # First try default channels from MOTOR_MUX_CHANNELS
            try:
                self.drv_left = adafruit_drv2605.DRV2605(mux[1])
                self.drv_right = adafruit_drv2605.DRV2605(mux[2])
                print("Using default channels from hardware_config.")
            except Exception as e:
                print(f"Default channels failed: {e}. Trying test_all_channels...")
                channels = test_all_channels()
                if channels:
                    self.drv_left = adafruit_drv2605.DRV2605(mux[channels[0]])
                    self.drv_right = adafruit_drv2605.DRV2605(mux[channels[1]])
                    print(f"Using detected channels: {channels[0]} (left), {channels[1]} (right)")
                else:
                    raise RuntimeError("No valid channels found for haptic motors.")

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
            print(f"Haptic max intensity: {self._max_intensity:.2f}")
        except Exception as e:
            print(f"⚠️  Haptic motors unavailable: {e}")

        self.audio = AudioFeedback()

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
        self._left_intensity, self._right_intensity = compute_motor_intensities(
            target_center,
            frame_width,
            max_intensity=self._max_intensity,
        )

    def get_current_intensities(self) -> Tuple[float, float]:
        """Return the currently computed left/right intensities."""
        return self._left_intensity, self._right_intensity

    def update_motors(self):
        """
        Apply computed intensities to DRV2605 RTP registers.
        Call continuously in the main loop.
        """
        left_val = int(max(0.0, min(1.0, self._left_intensity)) * 127)
        right_val = int(max(0.0, min(1.0, self._right_intensity)) * 127)

        print(f"Motors Updated as Left Intensity: {self._left_intensity:.2f} -> {left_val}, Right Intensity: {self._right_intensity:.2f} -> {right_val}")

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

        # Beep every 0.5 seconds instead, but skip if both intensities are zero
        beep_interval = 0.5  # seconds
        current_time = time.monotonic()
        if not hasattr(self, '_last_beep_time'):
            self._last_beep_time = 0

        if (left_val > 0 or right_val > 0) and current_time - self._last_beep_time >= beep_interval:
            self._last_beep_time = current_time
            print(f"Beep Direction Check - Left Val: {left_val}, Right Val: {right_val}")

            # Check if within middle tolerance first
            tolerance = 10  # Define a tolerance range for "straight ahead"
            print(abs(left_val - right_val))
            if abs(left_val - right_val) <= tolerance:
                self.audio.beep(frequency=400, duration=0.25, volume=0.5)
            elif left_val > right_val:  # Beep a low tone for left, high tone for right
                self.audio.beep(frequency=200, duration=0.2, volume=0.5)
            elif right_val > left_val:
                self.audio.beep(frequency=800, duration=0.2, volume=0.5)

                
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
