"""
Hardware Interface Module
Provides clean interfaces to physical hardware components.
"""

from .button_interface import ButtonInterface
from .haptic_controller import HapticController
from .camera_interface import CameraInterface

__all__ = ['ButtonInterface', 'HapticController', 'CameraInterface']
