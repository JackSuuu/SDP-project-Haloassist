"""
Services Configuration
TTS and STT model paths and audio settings.
"""

from pathlib import Path
import os

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
MODEL_PATH = "/home/ubuntu/vosk-model/vosk-model-small-en-us-0.15"
if os.name == "nt":  # Check if running on Windows
    MODEL_PATH = str(Path(__file__).parent.parent / "models" / "vosk-model-small-en-us-0.15")

STT_CONFIG = {
    'model_path': MODEL_PATH,
    'sample_rate': 16000,
    'duration': 3,
    'block_size': 8000,
}
