"""
Services Configuration
TTS and STT model paths and audio settings.
"""

from pathlib import Path
import os

_LOCAL_VOSK_MODEL = Path(__file__).parent.parent / "models" / "vosk-model-small-en-us-0.15"

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
if os.environ.get("HALOASSIST_VOSK_MODEL"):
    MODEL_PATH = os.environ["HALOASSIST_VOSK_MODEL"]
elif os.name != "posix" or not Path(MODEL_PATH).exists():
    # macOS and dev machines use the bundled model under perception/models.
    MODEL_PATH = str(_LOCAL_VOSK_MODEL)

STT_CONFIG = {
    'model_path': MODEL_PATH,
    'sample_rate': 16000,
    'duration': 3,
    'block_size': 8000,
}
