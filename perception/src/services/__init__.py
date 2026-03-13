"""
Services Module
Provides software-level service abstractions (STT, TTS, audio feedback)
that are not tied to specific hardware components.
"""

from .speech_interface import SpeechInterface
from .tts_interface import TTSInterface
from .audio_feedback import AudioFeedback

__all__ = ['SpeechInterface', 'TTSInterface', 'AudioFeedback']
