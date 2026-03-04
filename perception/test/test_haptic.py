"""
Unit tests for haptic feedback
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

import pytest
from feedback.haptic_legacy import HapticFeedback


def test_haptic_initialization():
    """Test haptic system can be initialized"""
    haptic = HapticFeedback(num_motors=8)
    assert haptic is not None
    assert haptic.num_motors == 8
    assert haptic.simulation_mode == True  # Should be True on Mac


def test_calculate_direction_right():
    """Test direction calculation for right"""
    haptic = HapticFeedback(num_motors=8)
    
    # Target to the right of center
    motor_idx = haptic.calculate_direction((400, 240), (320, 240))
    assert motor_idx == 0  # Right


def test_calculate_direction_left():
    """Test direction calculation for left"""
    haptic = HapticFeedback(num_motors=8)
    
    # Target to the left of center
    motor_idx = haptic.calculate_direction((100, 240), (320, 240))
    assert motor_idx == 4  # Left


def test_calculate_direction_top():
    """Test direction calculation for top"""
    haptic = HapticFeedback(num_motors=8)
    
    # Target above center
    motor_idx = haptic.calculate_direction((320, 100), (320, 240))
    assert motor_idx == 2  # Top


def test_calculate_direction_bottom():
    """Test direction calculation for bottom"""
    haptic = HapticFeedback(num_motors=8)
    
    # Target below center
    motor_idx = haptic.calculate_direction((320, 400), (320, 240))
    assert motor_idx == 6  # Bottom


def test_activate_motor():
    """Test motor activation in simulation mode"""
    haptic = HapticFeedback(num_motors=8)
    
    # Should not raise error in simulation mode
    haptic.activate_motor(0, duration=0.1)
    haptic.activate_motor(4, duration=0.2)


def test_guide_to_target():
    """Test guide to target functionality"""
    haptic = HapticFeedback(num_motors=8)
    
    # Should not raise error
    haptic.guide_to_target((400, 240), (320, 240), distance_score=0.7)


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
