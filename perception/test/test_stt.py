import sounddevice as sd
import queue
import time
import vosk
import json

# Configuration
SAMPLERATE = 16000
DURATION = 3  # seconds
BLOCKSIZE = 8000
MODEL_PATH = "c:\\Documents\\Uni\\YR3\\SDP\\SDP-project-Haloassist\\perception\\models\\vosk-model-small-en-us-0.15"

# Queue to store audio data
q = queue.Queue()

def callback(indata, frames, time, status):
    if status:
        print("Status:", status)
    q.put(bytes(indata))

def test_stt():
    """Test Vosk speech-to-text for 3 seconds."""
    print("Testing Vosk speech-to-text for 3 seconds...")

    try:
        model = vosk.Model(MODEL_PATH)
        rec = vosk.KaldiRecognizer(model, SAMPLERATE)

        with sd.RawInputStream(
            samplerate=SAMPLERATE,
            blocksize=BLOCKSIZE,
            dtype="int16",
            channels=1,
            callback=callback,
        ):
            start_time = time.time()
            print("Listening...")
            while time.time() - start_time < DURATION:
                data = q.get()
                if rec.AcceptWaveform(data):
                    result = json.loads(rec.Result())
                    print("Partial result:", result.get("text", ""))

            print("Final result:", json.loads(rec.FinalResult()).get("text", ""))

        print("Vosk speech-to-text test completed successfully.")
    except Exception as e:
        print(f"Error during Vosk speech-to-text test: {e}")

if __name__ == "__main__":
    test_stt()