"""
Hardware Interface Module
Re-exports hardware components from the hardware/ subfolder for easy importing.

This module provides a centralized import point for:
- ButtonInterface: Button input control
- TTSInterface: Text-to-Speech
- VibrationalMotorController: Vibrational motor control (2 motors for left/right guidance)
"""
from hardware.button import ButtonInterface
from hardware.tts import TTSInterface
from hardware.motors import VibrationalMotorController

# Re-export for convenient importing
__all__ = ['ButtonInterface', 'TTSInterface', 'VibrationalMotorController']
