#import gpio
from gpiozero import Button

import time

button = Button(27)

while True:
    if button.is_pressed:
        print("Good")
    else:
        print("Bad")
    time.sleep(0.5)
