"""
Services Configuration
TTS and STT model paths and audio settings.
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
