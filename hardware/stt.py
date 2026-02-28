import sounddevice as sd
import vosk
import json
import queue

MODEL_PATH = "/home/ubuntu/vosk-model/vosk-model-small-en-us-0.15"
SAMPLERATE = 16000
BLOCKSIZE = 8000

q = queue.Queue()
model = vosk.Model(MODEL_PATH)
print("Initialising STT")

def callback(indata, frames, time, status):
	if status:
		print(status)
	q.put(bytes(indata))


def listen(duration):
	"""Fixed-duration recording (legacy)."""
	q.queue.clear()
	with sd.RawInputStream(samplerate=SAMPLERATE, blocksize=BLOCKSIZE, dtype='int16', channels=1, callback=callback):
		rec = vosk.KaldiRecognizer(model, SAMPLERATE)
		print("Recording")
		for _ in range(int(SAMPLERATE / BLOCKSIZE * duration)):
			data = q.get()
			if rec.AcceptWaveform(data):
				pass
		print("Done recording")
		result = rec.FinalResult()
		text = json.loads(result).get("text", "")
		print("You said: ", text)
		return text


def listen_while_button_pressed(button_check_function):
	"""
	Record as long as button_check_function() returns True.
	This removes the fixed-duration latency entirely.
	"""
	q.queue.clear()

	with sd.RawInputStream(
		samplerate=SAMPLERATE,
		blocksize=BLOCKSIZE,
		dtype="int16",
		channels=1,
		callback=callback,
	):
		rec = vosk.KaldiRecognizer(model, SAMPLERATE)
		print("Recording...")

		while button_check_function():
			data = q.get()
			rec.AcceptWaveform(data)

		print("Stopped recording")

		result = rec.FinalResult()
		text = json.loads(result).get("text", "")
		print("You said:", text)
		return text