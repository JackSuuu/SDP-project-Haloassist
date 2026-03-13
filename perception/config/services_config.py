"""
Services Configuration
TTS, STT, and general system settings.
"""

# ============================================
# Text-to-Speech (Piper) Configuration
# ============================================
TTS_CONFIG = {
    'model_path': '/home/ubuntu/piper-voices/en_US-lessac-medium/en_US-lessac-medium.onnx',
    'output_sample_rate': 22050,
}

# ============================================
# Speech-to-Text (Vosk) Configuration
# ============================================
STT_CONFIG = {
    'model_path': '/home/ubuntu/vosk-model/vosk-model-small-en-us-0.15',
    'sample_rate': 16000,
    'duration': 3,
    'block_size': 8000,
}

# ============================================
# System Configuration
# ============================================
SYSTEM_CONFIG = {
    'show_display': True,
    'enable_speech': False,
    'enable_button': True,
    'fps_display': True,
    'detect_interval': 0.05,
}
