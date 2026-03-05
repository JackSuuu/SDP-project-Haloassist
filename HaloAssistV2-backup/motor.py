# motor.py

import time
from gpiozero import PWMOutputDevice


class MotorController:
    def __init__(self, left_pin, right_pin, pulse_interval, pulse_duration):
        self.motor_left = PWMOutputDevice(left_pin)
        self.motor_right = PWMOutputDevice(right_pin)

        self.pulse_interval = pulse_interval
        self.pulse_duration = pulse_duration

        self.last_pulse_time = 0
        self.pulse_end_time = 0

    def update(self, left_strength, right_strength):
        current_time = time.time()

        if (left_strength > 0 or right_strength > 0) and \
           current_time - self.last_pulse_time >= self.pulse_interval:
            self.pulse_end_time = current_time + self.pulse_duration
            self.last_pulse_time = current_time

        if current_time < self.pulse_end_time:
            self.motor_left.value = left_strength
            self.motor_right.value = right_strength
        else:
            self.motor_left.value = 0.0
            self.motor_right.value = 0.0

    def cleanup(self):
        self.motor_left.off()
        self.motor_right.off()
