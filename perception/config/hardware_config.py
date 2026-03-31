"""
Hardware Configuration
GPIO pins, motor mappings, and physical device settings.
"""

# ============================================
# Camera Configuration
# ============================================
CAMERA_CONFIG = {
    'width': 640,               # Frame width (1280 for Pi5)
    'height': 480,              # Frame height (720 for Pi5)
    'fps': 30,                  # Target FPS
    'device_id': 0,             # Camera device ID for OpenCV
}

# Raspberry Pi camera settings (picamera2)
PICAMERA_CONFIG = {
    'width': 1000,
    'height': 1000,
    'format': 'BGR888',
}

# ============================================
# Haptic Feedback Configuration
# ============================================
# Active setup: Grove Shield, direct GPIO PWM (BCM mode)
#   Pi GPIO 22  -->  Grove Shield  -->  left motor
#   Pi GPIO 26  -->  Grove Shield  -->  right motor
MOTOR_PINS = {
    'left':  22,
    'right': 26,
}

# Haptic feedback settings
HAPTIC_CONFIG = {
    'default_strength':    0.5,   # Default motor strength (0.0 – 1.0)
    'default_duration':    0.25,  # Vibration duration (seconds) — legacy reference
    'detection_interval':  0.25,  # Minimum time between haptic updates
    'pulse_interval':      0.5,   # Non-blocking: min seconds between pulses
    'pulse_duration':      0.05,  # Non-blocking: duration of each pulse (seconds)
}

# ============================================
# Button Configuration
# ============================================
BUTTON_CONFIG = {
    'pin':           13,    # BCM GPIO pin for push button (Grove Shield, physical pin 33)
    'pull_up':       True,  # Pin is externally pulled HIGH; button drives it LOW when pressed
    'active_low':    True,  # Button active when LOW
    'debounce_time': 0.01,  # Debounce delay (seconds)
}
