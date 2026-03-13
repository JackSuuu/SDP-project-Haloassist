"""
Services Module
Provides software-level service abstractions (STT, TTS) that are
not tied to specific hardware components.
"""

from .speech_interface import SpeechInterface
from .tts_interface import Speaker

__all__ = ['SpeechInterface', 'Speaker']
