"""
Run Configuration
Feature flags to enable/disable components at runtime.
Flip flags here to test individual subsystems in isolation.
"""

RUN_CONFIG = {
        # Hardware
    'enable_haptic':     True,   # HapticController + DRV2605 motors
    'haptic_max_intensity': 0.65, # Max motor intensity scaling (0.0 - 1.0)
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

    # LLM extractor model (GGUF)
    # Accepts absolute path, or path relative to repo root.
    # Example local file: 'gemma3-vosk-q4.gguf'
    # Alternative model after download: 'models/functiongemma-270M-vosk-extractor-Q8_0-LoRA.gguf'
    'llm_extractor_model': 'functiongemma-270M-vosk-extractor-Q8_0-LoRA.gguf',

}
