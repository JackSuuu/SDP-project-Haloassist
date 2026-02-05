import sounddevice as sd
import vosk
import json
import queue

MODEL_PATH = "/home/pi/vosk-model/vosk-model-small-en-us-0.15"

q = queue.Queue()
model = vosk.Model(MODEL_PATH)
samplerate = 16000
print("Initialising STT HERE")

def callback(indata, frames, time, status):
	if status:
		print(status)
	q.put(bytes(indata))


def listen(duration):
	q.queue.clear()
	with sd.RawInputStream(samplerate=samplerate, blocksize=8000, dtype='int16', channels=1, callback=callback):
		rec = vosk.KaldiRecognizer(model, samplerate)
		print("Recording")
		for _ in range(int(samplerate / 8000 * duration)):
			data = q.get()
			if rec.AcceptWaveform(data):
				pass
		print("Done recording")
		result = rec.FinalResult()
		text = json.loads(result).get("text", "")
		print("You said: ", text)
		return text  # Return the recognized text