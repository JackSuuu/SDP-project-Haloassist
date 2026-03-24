"""Unit tests for two-motor haptic intensity mapping."""

import os
import sys
import unittest


SRC_DIR = os.path.join(os.path.dirname(__file__), "..", "src")
sys.path.insert(0, os.path.abspath(SRC_DIR))

from hardware.haptic_controller import CENTER_BAND, CENTER_INTENSITY, HapticController


class TestHapticControllerMapping(unittest.TestCase):
    def setUp(self):
        self.haptic = HapticController()
        self.frame_center = (320, 240)
        self.frame_width = 640

    def test_exact_center_drives_both_motors(self):
        self.haptic.guide_to_target((320, 240), self.frame_center, self.frame_width)
        self.assertAlmostEqual(self.haptic._left_intensity, CENTER_INTENSITY)
        self.assertAlmostEqual(self.haptic._right_intensity, CENTER_INTENSITY)

    def test_center_band_edge_is_still_center(self):
        edge_delta = int((self.frame_width / 2.0) * CENTER_BAND)
        self.haptic.guide_to_target((320 + edge_delta, 240), self.frame_center, self.frame_width)
        self.assertAlmostEqual(self.haptic._left_intensity, CENTER_INTENSITY)
        self.assertAlmostEqual(self.haptic._right_intensity, CENTER_INTENSITY)

    def test_outside_center_band_favors_one_side(self):
        self.haptic.guide_to_target((353, 240), self.frame_center, self.frame_width)
        self.assertGreater(self.haptic._right_intensity, self.haptic._left_intensity)


if __name__ == "__main__":
    unittest.main()
