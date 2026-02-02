"""
Feedback Components Module
Handles haptic feedback systems
"""
from .haptic_legacy import HapticFeedback
from .haptic_two_motor import TwoMotorHapticFeedback

__all__ = ['HapticFeedback', 'TwoMotorHapticFeedback']
