"""
Audio Feedback
Provides simple beep and tone patterns for user feedback.
No TTS or ML model required — only numpy and sounddevice.
"""
import threading
import time

class AudioFeedback:
    """Lightweight audio feedback using generated tones."""

    def __init__(self, sample_rate: int = 44100):
        """
        Initialize audio feedback.
        Imports numpy and sounddevice once here so beep() has zero import overhead.

        Args:
            sample_rate: Sample rate for tone generation (default 44100).
        """
        self.sample_rate = sample_rate
        self._available = False
        self._np = None
        self._sd = None

        try:
            import numpy as np
            import sounddevice as sd
            self._np = np
            self._sd = sd
            self._available = True
        except ImportError:
            print("[AudioFeedback] numpy/sounddevice not available - audio feedback disabled")

    def beep(self, frequency: float = 440, duration: float = 0.2,
             volume: float = 0.5, waveform: str = "sine"):
        """Play a short tone asynchronously, allowing overlapping beeps."""
        if not self._available:
            return

        def play_tone():
            try:
                np = self._np
                t = np.linspace(0, duration, int(self.sample_rate * duration), False)

                if waveform == "sine":
                    tone = np.sin(frequency * 2 * np.pi * t)
                elif waveform == "square":
                    tone = np.sign(np.sin(frequency * 2 * np.pi * t))
                elif waveform == "saw":
                    tone = 2 * (t * frequency - np.floor(0.5 + t * frequency))
                else:
                    raise ValueError(f"Unsupported waveform: {waveform}")

                tone = volume * tone

                # Use OutputStream to allow overlapping tones
                with self._sd.OutputStream(samplerate=self.sample_rate, channels=1) as stream:
                    stream.write(tone.astype(np.float32))
            except Exception as e:
                print(f"[AudioFeedback] beep error: {e}")

        # Run the tone playback in a separate thread
        threading.Thread(target=play_tone, daemon=True).start()

    def success(self):
        """Play a two-tone success sound."""
        def play_success():
            self.beep(600, 0.15, 0.02)
            time.sleep(0.2)
            self.beep(900, 0.15, 0.04)
        threading.Thread(target=play_success, daemon=True).start()

    def error(self):
        """Play a low error tone."""
        self.beep(200, 0.5, 0.1)

    def alert(self, repeats: int = 3):
        """Play a repeated alert beep."""
        def play_alert():
            for _ in range(repeats):
                self.beep(1000, 0.15, 0.03)
                time.sleep(0.25)
        threading.Thread(target=play_alert, daemon=True).start()

    def bootup(self):
        """Play a startup chime."""
        def play_bootup():
            self.beep(440, 0.3, 0.02)
            time.sleep(0.5)
            self.beep(660, 0.3, 0.04)
        threading.Thread(target=play_bootup, daemon=True).start()

    def shutdown(self):
        """Play a shutdown chime."""
        def play_shutdown():
            self.beep(660, 0.3, 0.02)
            time.sleep(0.5)
            self.beep(440, 0.3, 0.04)
        threading.Thread(target=play_shutdown, daemon=True).start()

    def button_press(self):
        """Play a beep for button press feedback."""
        threading.Thread(target=lambda: self.beep(880, 0.1, 0.02), daemon=True).start()

    def button_release(self):
        """Play a beep for button release feedback."""
        threading.Thread(target=lambda: self.beep(750, 0.1, 0.02), daemon=True).start()