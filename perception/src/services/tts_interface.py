"""
TTS Interface
Provides neural text-to-speech via Piper.
"""
import sys
import subprocess
from pathlib import Path
from typing import Optional

config_dir = Path(__file__).parent.parent.parent / 'config'
sys.path.insert(0, str(config_dir))

from services_config import TTS_CONFIG


class TTSInterface:
    """Neural TTS interface using Piper."""

    def __init__(self, tts_model: Optional[str] = None):
        """
        Initialize TTS interface.
        Imports numpy and sounddevice once here so speak() has zero import overhead.

        Args:
            tts_model: Path to Piper ONNX voice model.
        """
        self.tts_model = tts_model or TTS_CONFIG['model_path']
        self.sample_rate = TTS_CONFIG.get('output_sample_rate', 22050)
        self.volume = TTS_CONFIG.get("volume", 0.3)
        self.piper = None
        self._is_available = False
        self._np = None
        self._sd = None

        try:
            import numpy as np
            import sounddevice as sd
            self._np = np
            self._sd = sd
        except ImportError:
            print("Warning: numpy/sounddevice not available. TTS audio output disabled.")
            return

        self._start_piper()

    def _start_piper(self):
        """Launch the Piper TTS subprocess (stdin -> raw PCM stdout)."""
        try:
            self.piper = subprocess.Popen(
                ["piper", "--model", self.tts_model, "--output_raw"],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                bufsize=0,
            )
            self._is_available = True
            print(f"TTSInterface initialized (Piper model: {self.tts_model})")
        except FileNotFoundError:
            print("Warning: 'piper' binary not found. TTS disabled.")
        except Exception as e:
            print(f"Warning: Failed to start Piper TTS: {e}")

    def is_available(self) -> bool:
        return self._is_available

    def speak(self, text: str):
        """Synthesize text via Piper and play through the speaker."""
        if not self._is_available or self.piper is None:
            print(f"[TTS] (unavailable) Would say: {text}")
            return

        try:
            if not text.endswith("\n"):
                text += "\n"

            self.piper.stdin.write(text.encode())
            self.piper.stdin.flush()

            audio_chunks = []
            while True:
                chunk = self.piper.stdout.read(16000 * 2)
                if not chunk:
                    break
                audio_chunks.append(chunk)
                if len(chunk) < 16000 * 2:
                    break

            if not audio_chunks:
                return

            audio = b"".join(audio_chunks)
            data = (
                self._np.frombuffer(audio, dtype=self._np.int16)
                .astype(self._np.float32) / 32768.0
            )

            # apply volume + prevent clipping
            data = self._np.clip(data * self.volume, -1.0, 1.0)

            self._sd.play(data, self.sample_rate)
            self._sd.wait()
        except Exception as e:
            print(f"[TTS] speak error: {e}")

    def cleanup(self):
        """Terminate the Piper subprocess."""
        if self.piper is not None:
            try:
                self.piper.terminate()
                self.piper.wait(timeout=2)
            except Exception:
                pass
            self.piper = None




