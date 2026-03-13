"""
Audio Feedback
Provides simple beep and tone patterns for user feedback.
No TTS or ML model required — only numpy and sounddevice.
"""


class AudioFeedback:
    """Lightweight audio feedback using generated tones."""

    def __init__(self, sample_rate: int = 44100):
        """
        Initialize audio feedback.

        Args:
            sample_rate: Sample rate for tone generation (default 44100).
        """
        self.sample_rate = sample_rate

    def beep(self, frequency: float = 440, duration: float = 0.2,
             volume: float = 0.5, waveform: str = "sine"):
        """Play a short tone."""
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
            print("[AudioFeedback] numpy/sounddevice not available - skipping beep")
        except Exception as e:
            print(f"[AudioFeedback] beep error: {e}")

    def success(self):
        """Play a two-tone success sound."""
        self.beep(600, 0.1, 0.3)
        self.beep(900, 0.1, 0.4)

    def error(self):
        """Play a low error tone."""
        self.beep(200, 0.3, 0.6)

    def alert(self, repeats: int = 3):
        """Play a repeated alert beep."""
        for _ in range(repeats):
            self.beep(1000, 0.05, 0.4)
