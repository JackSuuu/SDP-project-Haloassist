import sounddevice as sd
import vosk
import json
import queue
import RPi.GPIO as GPIO
import time
import stt

# ---------- CONFIG ----------
BUTTON_PIN = 5
duration = 3
# ----------------------------

# Setup GPIO
GPIO.setmode(GPIO.BCM)
GPIO.setup(BUTTON_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)

# Setup Vosk

print("Ready. Press the button and speak.")

while True:
	# Wait for button press
	if GPIO.input(BUTTON_PIN) == 0:
		stt.listen(duration)
	time.sleep(0.01)