"""
TTS Interface (Speaker)
Provides text-to-speech and audio feedback via Piper neural TTS.
Ported from 1-integration branch: HaloAssistV2-backup/speaker.py
"""
import sys
from pathlib import Path
from typing import Optional

# Add config directory to path
config_dir = Path(__file__).parent.parent.parent / 'config'
sys.path.insert(0, str(config_dir))

from settings import TTS_CONFIG


class Speaker:
    """Neural TTS and audio feedback interface using Piper."""

    def __init__(self, tts_model: Optional[str] = None, sample_rate: int = 44100):
        """
        Initialize speaker.

        Args:
            tts_model: Path to Piper ONNX voice model.
            sample_rate: Sample rate for beep generation (default 44100).
        """
        self.sample_rate = sample_rate
        self.tts_model = tts_model or TTS_CONFIG['model_path']
        self.piper = None
        self._is_available = False

        self._start_piper()

    # ------------------------------------------------------------------
    # Piper lifecycle
    # ------------------------------------------------------------------
    def _start_piper(self):
        """Launch the Piper TTS subprocess (stdin → raw PCM stdout)."""
        try:
            import subprocess
            self.piper = subprocess.Popen(
                ["piper", "--model", self.tts_model, "--output_raw"],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                bufsize=0,
            )
            self._is_available = True
            print(f"Speaker initialized (Piper model: {self.tts_model})")
        except FileNotFoundError:
            print("Warning: 'piper' binary not found. TTS disabled.")
        except Exception as e:
            print(f"Warning: Failed to start Piper TTS: {e}")

    def is_available(self) -> bool:
        return self._is_available

    # ------------------------------------------------------------------
    # Beep / patterns
    # ------------------------------------------------------------------
    def beep(self, frequency: float = 440, duration: float = 0.2,
             volume: float = 0.5, waveform: str = "sine"):
        """Play a short tone through the speaker."""
        try:
            import numpy as np
            import sounddevice as sd

            t = np.linspace(0, duration, int(self.sample_rate * duration), False)

            if waveform == "sine":
                tone = np.sin(frequency * 2 * np.pi * t)
            elif waveform == "square":
                tone = np.sign(np.sin(frequency * 2 * np.pi * t))
            elif waveform == "saw":
                tone = 2 * (t * frequency - np.floor(0.5 + t * frequency))
            else:
                raise ValueError(f"Unsupported waveform: {waveform}")

            audio = volume * tone
            sd.play(audio, self.sample_rate)
            sd.wait()
        except ImportError:
            print("[TTS] numpy/sounddevice not available – skipping beep")
        except Exception as e:
            print(f"[TTS] beep error: {e}")

    def success(self):
        self.beep(600, 0.1, 0.3)
        self.beep(900, 0.1, 0.4)

    def error(self):
        self.beep(200, 0.3, 0.6)

    def alert(self, repeats: int = 3):
        for _ in range(repeats):
            self.beep(1000, 0.05, 0.4)

    # ------------------------------------------------------------------
    # Neural TTS
    # ------------------------------------------------------------------
    def speak(self, text: str):
        """Synthesize *text* via Piper and play through the speaker."""
        if not self._is_available or self.piper is None:
            print(f"[TTS] (unavailable) Would say: {text}")
            return

        try:
            import numpy as np
            import sounddevice as sd

            if not text.endswith("\n"):
                text += "\n"

            self.piper.stdin.write(text.encode())
            self.piper.stdin.flush()

            # Read all available audio until Piper stops outputting
            audio_chunks = []
            while True:
                chunk = self.piper.stdout.read(16000 * 2)
                if not chunk:
                    break
                audio_chunks.append(chunk)
                # Break if chunk is smaller than expected (end of stream)
                if len(chunk) < 16000 * 2:
                    break

            if not audio_chunks:
                return

            audio = b"".join(audio_chunks)
            data = np.frombuffer(audio, dtype=np.int16).astype(np.float32) / 32768.0

            sd.play(data, TTS_CONFIG.get('output_sample_rate', 22050))
            sd.wait()
        except Exception as e:
            print(f"[TTS] speak error: {e}")

    # ------------------------------------------------------------------
    def cleanup(self):
        """Terminate the Piper subprocess."""
        if self.piper is not None:
            try:
                self.piper.terminate()
                self.piper.wait(timeout=2)
            except Exception:
                pass
            self.piper = None
