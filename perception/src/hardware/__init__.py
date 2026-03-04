"""
Hardware Interface Module
Provides clean interfaces to hardware components for perception system
"""

from .button_interface import ButtonInterface
from .speech_interface import SpeechInterface
from .haptic_controller import HapticController
from .tts_interface import Speaker

__all__ = ['ButtonInterface', 'SpeechInterface', 'HapticController', 'Speaker']
