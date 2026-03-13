"""
Run Configuration
Feature flags to enable/disable components at runtime.
Flip flags here to test individual subsystems in isolation.
"""

RUN_CONFIG = {
    # Vision
    'enable_yolo':    True,   # YOLO detection (core — disabling stops all detection)

    # Hardware
    'enable_haptic':  True,   # HapticController + DRV2605 motors
    'enable_button':  True,   # ButtonInterface for STT trigger
    'enable_camera':  True,   # CameraInterface (disable to use static test frames)

    # Services
    'enable_speech':  False,  # STT via Vosk (button-held recording)
    'enable_tts':     False,  # Piper TTS spoken responses
    'enable_audio':   True,   # AudioFeedback beeps

    # Display
    'show_display':   True,   # OpenCV window with bounding boxes
    'fps_display':    True,   # FPS counter overlay

    # Timing
    'detect_interval': 0.05,  # seconds between detection passes
}
