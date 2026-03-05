# button.py

import RPi.GPIO as GPIO
import time
import stt

BUTTON_PIN = 5

GPIO.setmode(GPIO.BCM)
GPIO.setup(BUTTON_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)

print("Ready. Hold button to speak.")

def button_pressed():
    return GPIO.input(BUTTON_PIN) == 0  # active low

try:
    while True:
        if button_pressed():
            stt.listen_while_button_pressed(button_pressed)
        time.sleep(0.01)

except KeyboardInterrupt:
    GPIO.cleanup()
