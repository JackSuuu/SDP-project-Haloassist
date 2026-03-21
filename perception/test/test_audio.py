import sys
import time

from pathlib import Path

src_root = Path(__file__).parent.parent
sys.path.insert(0, str(src_root))

from src.services.audio_feedback import AudioFeedback

audio = AudioFeedback()

def test_audio_feedback():
    """Test AudioFeedback functionality."""
    print("Testing AudioFeedback...")

    if not audio._available:
        print("AudioFeedback dependencies not available. Skipping audio tests.")
        return

    try:
        #audio.beep(440, 1, 0.5)  # Long beep
        #audio.beep(880, 0.5, 0.5)  # Short beep starts immediately
        #audio.beep(660, 0.3, 0.5)  # Another short beep starts immediately

        audio.button_press()  # Should play a quick beep
        time.sleep(1)
        audio.button_release()  # Should play a quick beep
        time.sleep(1)

        # beep at different frequency and waveform
        #for freq in [200, 440, 600, 880, 1000, 1400, 1760]:
         #   print(f"Playing beep at {freq} Hz...")
          #  audio.beep(frequency=freq, duration=0.25, volume=1, waveform="sine")

        print("AudioFeedback test completed successfully.")
    except Exception as e:
        print(f"AudioFeedback test failed: {e}")

if __name__ == "__main__":
    test_audio_feedback()