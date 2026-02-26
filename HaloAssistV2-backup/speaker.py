# speaker.py

import numpy as np
import sounddevice as sd
import soundfile as sf
import subprocess
import tempfile
import os
import threading

class Speaker:
    def __init__(self,
                 sample_rate=44100,
                 tts_model="/home/ubuntu/piper-voices/en_US-lessac-medium/en_US-lessac-medium.onnx"):
        self.sample_rate = sample_rate
        self.tts_model = tts_model
        self._start_piper()


    # ---------- BEEP ----------
    def beep(self, frequency=440, duration=0.2, volume=0.5, waveform="sine"):
        t = np.linspace(0, duration, int(self.sample_rate * duration), False)

        if waveform == "sine":
            tone = np.sin(frequency * 2 * np.pi * t)
        elif waveform == "square":
            tone = np.sign(np.sin(frequency * 2 * np.pi * t))
        elif waveform == "saw":
            tone = 2 * (t * frequency - np.floor(0.5 + t * frequency))
        else:
            raise ValueError("Unsupported waveform")

        audio = volume * tone
        sd.play(audio, self.sample_rate)
        sd.wait()

    # ---------- PATTERNS ----------
    def success(self):
        self.beep(600, 0.1, 0.3)
        self.beep(900, 0.1, 0.4)

    def error(self):
        self.beep(200, 0.3, 0.6)  # 2.0 would clip badly

    def alert(self, repeats=3):
        for _ in range(repeats):
            self.beep(1000, 0.05, 0.4)

    # ---------- NEURAL TEXT TO SPEECH ----------
    def speak(self, text):
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

        sd.play(data, 22050)
        sd.wait()

    def _start_piper(self):
        self.piper = subprocess.Popen(
            [
                "piper",
                "--model", self.tts_model,
                "--output_raw"
            ],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            bufsize=0
        )
