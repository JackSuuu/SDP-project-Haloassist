"""
Run Configuration
Feature flags to enable/disable components at runtime.
Flip flags here to test individual subsystems in isolation.
"""

RUN_CONFIG = {
        # Hardware
    'enable_haptic':     True,   # HapticController + DRV2605 motors
    'enable_button':     True,   # ButtonInterface for STT trigger
    'enable_camera':     True,   # CameraInterface

    # Services
    'enable_speech':     True,  # STT via Vosk (button-held recording)
    'enable_tts':        True,  # Piper TTS spoken responses
    'enable_audio':      True,   # AudioFeedback beeps

    # Debug / tooling
    'enable_visualizer': True,  # Web visualizer (visualization/haptic_client.py)
    'show_display':      True,   # OpenCV window with bounding boxes
    'fps_display':       True,   # FPS counter overlay

}
