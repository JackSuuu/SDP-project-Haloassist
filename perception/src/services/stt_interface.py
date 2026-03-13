"""
STT Interface
Speech-to-text via Vosk. Owns all recording and recognition logic internally.
Supports fixed-duration and button-held recording modes.
"""
import sys
import json
import queue
from pathlib import Path
from typing import Optional, Callable

config_dir = Path(__file__).parent.parent.parent / 'config'
sys.path.insert(0, str(config_dir))

from services_config import STT_CONFIG


class STTInterface:
    """Speech-to-text interface using Vosk."""

    def __init__(self):
        self.model_path = STT_CONFIG['model_path']
        self.sample_rate = STT_CONFIG['sample_rate']
        self.block_size = STT_CONFIG['block_size']
        self.model = None
        self._sd = None
        self._vosk = None
        self._is_available = self._initialize()

    def _initialize(self) -> bool:
        """Load Vosk model and import sounddevice once."""
        try:
            import vosk
            import sounddevice as sd
            self._vosk = vosk
            self._sd = sd
            self.model = vosk.Model(self.model_path)
            print(f"STTInterface initialized (model: {self.model_path})")
            return True
        except ImportError as e:
            print(f"Warning: Missing dependency ({e}). Speech recognition disabled.")
            return False
        except Exception as e:
            print(f"Warning: Failed to initialize STT: {e}")
            return False

    def is_available(self) -> bool:
        return self._is_available

    def listen(self, duration: int = None) -> Optional[str]:
        """
        Record for a fixed duration and return recognised text.

        Args:
            duration: seconds to record (defaults to STT_CONFIG['duration'])
        """
        if not self._is_available:
            return None

        duration = duration or STT_CONFIG['duration']
        q = queue.Queue()

        def callback(indata, frames, time, status):
            if status:
                print(status)
            q.put(bytes(indata))

        try:
            with self._sd.RawInputStream(samplerate=self.sample_rate, blocksize=self.block_size,
                                         dtype='int16', channels=1, callback=callback):
                rec = self._vosk.KaldiRecognizer(self.model, self.sample_rate)
                print("Recording...")
                for _ in range(int(self.sample_rate / self.block_size * duration)):
                    rec.AcceptWaveform(q.get())
                print("Done recording")
                text = json.loads(rec.FinalResult()).get("text", "")
                print(f"You said: {text}")
                return text if text else None
        except Exception as e:
            print(f"[STT] listen error: {e}")
            return None

    def listen_while_pressed(self, button_check_fn: Callable[[], bool]) -> Optional[str]:
        """
        Record as long as button_check_fn() returns True.
        Recording length matches exactly how long the user holds the button.

        Args:
            button_check_fn: Callable returning True while button is held
        """
        if not self._is_available:
            return None

        q = queue.Queue()

        def callback(indata, frames, time, status):
            if status:
                print(status)
            q.put(bytes(indata))

        try:
            with self._sd.RawInputStream(samplerate=self.sample_rate, blocksize=self.block_size,
                                         dtype='int16', channels=1, callback=callback):
                rec = self._vosk.KaldiRecognizer(self.model, self.sample_rate)
                print("Recording...")
                while button_check_fn():
                    rec.AcceptWaveform(q.get())
                print("Stopped recording")
                text = json.loads(rec.FinalResult()).get("text", "")
                print(f"You said: {text}")
                return text if text else None
        except Exception as e:
            print(f"[STT] listen_while_pressed error: {e}")
            return None
