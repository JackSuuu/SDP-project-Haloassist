"""
Haptic Controller
Provides directional guidance using vibration motors.
2-motor (left/right) driven directly from Raspberry Pi GPIO via a Grove Shield.

Hardware path:
  Pi GPIO (BCM 22 / 26)  -->  Grove Shield  -->  vibration motors
  No I2C, no MUX, no DRV2605.

Motor control uses gpiozero PWMOutputDevice so intensity maps
continuously from 0.0 (off) to 1.0 (full), capped by max_intensity.
"""
from typing import Optional, Tuple


class HapticController:
    """Left/right haptic feedback via GPIO PWM on the Grove Shield."""

    def __init__(
        self,
        left_pin: int = 22,
        right_pin: int = 26,
        max_intensity: float = 1.0,
    ):
        """
        Args:
            left_pin:      BCM GPIO pin for the left motor (Grove Shield).
            right_pin:     BCM GPIO pin for the right motor (Grove Shield).
            max_intensity: Ceiling applied to every PWM write (0.0–1.0).
                           Sourced from RUN_CONFIG['haptic_max_intensity'].
        """
        self._left_pin      = left_pin
        self._right_pin     = right_pin
        self._max_intensity = max(0.0, min(1.0, max_intensity))
        self._available     = False

        self._left_intensity  = 0.0
        self._right_intensity = 0.0
        self.num_motors = 2

        self._motor_left  = None
        self._motor_right = None

        try:
            from gpiozero import PWMOutputDevice

            self._motor_left  = PWMOutputDevice(left_pin)
            self._motor_right = PWMOutputDevice(right_pin)

            self._available = True
            print(
                f"Haptic motors initialized via Grove Shield "
                f"(BCM L={left_pin} R={right_pin}, max_intensity={self._max_intensity:.2f})"
            )
        except Exception as e:
            print(f"Haptic motors unavailable: {e}")

    def is_available(self) -> bool:
        return self._available

    def guide_to_target(
        self,
        target_center: Optional[Tuple[int, int]],
        frame_center: Tuple[int, int],
        frame_width: int,
    ):
        """
        Compute continuous left/right intensity based on horizontal position.
        Object on the left  -> left motor stronger.
        Object on the right -> right motor stronger.
        """
        _ = frame_center
        if target_center is None:
            self._left_intensity  = 0.0
            self._right_intensity = 0.0
            return

        x_norm = target_center[0] / frame_width          # 0.0 (left) … 1.0 (right)
        x_norm = max(0.0, min(1.0, x_norm))

        # Linear cross-fade: full left at x=0, full right at x=1, both 0.5 at centre
        self._left_intensity  = max(0.0, 1.0 - 2.0 * x_norm)
        self._right_intensity = max(0.0, 2.0 * x_norm - 0.0)
        # Clamp so neither side exceeds 0.5 at centre (matches original behaviour)
        self._left_intensity  = min(self._left_intensity,  0.5)
        self._right_intensity = min(self._right_intensity, 0.5)

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
        Write current intensities to GPIO PWM, capped at max_intensity.
        Call every iteration of the main loop.
        """
        left_val  = min(self._left_intensity,  self._max_intensity)
        right_val = min(self._right_intensity, self._max_intensity)

        print(
            f"Motors: L={self._left_intensity:.2f}->{left_val:.2f}  "
            f"R={self._right_intensity:.2f}->{right_val:.2f}"
        )

        if not self._available:
            return

        self._motor_left.value  = left_val
        self._motor_right.value = right_val

    def stop(self):
        """Zero both motors immediately."""
        self._left_intensity  = 0.0
        self._right_intensity = 0.0
        if self._available:
            self._motor_left.value  = 0
            self._motor_right.value = 0

    def cleanup(self):
        """Stop motors and release GPIO resources."""
        self.stop()
        if self._available:
            self._motor_left.close()
            self._motor_right.close()
        print("Haptic motors cleaned up")
