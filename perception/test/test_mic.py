import sounddevice as sd
import queue
import wave

# Configuration
SAMPLERATE = 16000
DURATION = 5  # seconds
BLOCKSIZE = 8000

# Queue to store audio data
q = queue.Queue()

def list_audio_devices():
    """List all available audio input devices."""
    print("Available audio devices:")
    devices = sd.query_devices()
    for idx, device in enumerate(devices):
        print(f"{idx}: {device['name']} (Input Channels: {device['max_input_channels']})")

def callback(indata, frames, time, status):
    if status:
        print("Status:", status)
    q.put(bytes(indata))

def save_audio_to_file():
    """Save the recorded audio to a file for verification."""
    filename = "test_mic_output.wav"
    with wave.open(filename, "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)  # 16-bit audio
        wf.setframerate(SAMPLERATE)

        # Write all data from the queue to the file
        while not q.empty():
            wf.writeframes(q.get())

    print(f"Audio saved to {filename}. You can play it back to verify.")

def test_microphone(device_index=None):
    """Test microphone input for 5 seconds."""
    print("Testing microphone input for 5 seconds...")

    try:
        with sd.RawInputStream(
            samplerate=SAMPLERATE,
            blocksize=BLOCKSIZE,
            dtype="int16",
            channels=1,
            callback=callback,
            device=device_index
        ):
            print("Listening...")
            sd.sleep(DURATION * 1000)

        print("Microphone test completed successfully.")
        save_audio_to_file()
    except Exception as e:
        print(f"Error during microphone test: {e}")

if __name__ == "__main__":
    list_audio_devices()
    try:
        device_index = int(input("Enter the device index to use for the microphone: "))
    except ValueError:
        print("Invalid input. Using default device.")
        device_index = None

    test_microphone(device_index=device_index)