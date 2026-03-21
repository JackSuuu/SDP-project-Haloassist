"""
Run Configuration
Feature flags to enable/disable components at runtime.
Flip flags here to test individual subsystems in isolation.
"""

RUN_CONFIG = {
        # Hardware
    'enable_haptic':     False,   # HapticController + DRV2605 motors
    'enable_button':     False,   # ButtonInterface for STT trigger
    'enable_camera':     False,   # CameraInterface

    # Services
    'enable_speech':     False,  # STT via Vosk (button-held recording)
    'enable_tts':        False,  # Piper TTS spoken responses
    'enable_audio':      False,   # AudioFeedback beeps

    # Debug / tooling
    'enable_visualizer': False,  # Web visualizer (visualization/haptic_client.py)
    'show_display':      True,   # OpenCV window with bounding boxes
    'fps_display':       True,   # FPS counter overlay

}
