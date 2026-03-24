"""
Hardware Configuration
GPIO pins, motor mappings, and physical device settings
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

# Raspberry Pi camera settings
PICAMERA_CONFIG = {
    'width': 1000,              # PiCamera frame width
    'height': 1000,             # PiCamera frame height
    'format': 'BGR888',         # Color format
}

# ============================================
# Haptic Feedback Configuration
# ============================================
# GPIO pin mapping for motors (BCM mode)
# Can be easily extended from 2 motors to 6-8 motors

# Current setup (2 motors via I2C MUX + DRV2605 haptic drivers)
# TCA9548A multiplexer channel mapping
MOTOR_MUX_CHANNELS = {
    'left': 1,
    'right': 2,
}

# Legacy GPIO pin mapping (unused with MUX setup)
MOTOR_PINS_2 = {
    'left': 22,
    'right': 26,
}

# Future setup (8 motors - circular array)
MOTOR_PINS_8 = {
    'front': 17,
    'front_right': 18,
    'right': 22,
    'back_right': 23,
    'back': 24,
    'back_left': 25,
    'left': 26,
    'front_left': 27,
}

# Active motor configuration
MOTOR_PINS = MOTOR_PINS_2  # Legacy fallback
MOTOR_MUX = MOTOR_MUX_CHANNELS  # Active: I2C MUX + DRV2605

# Haptic feedback settings
HAPTIC_CONFIG = {
    'default_strength': 0.5,    # Default motor strength (0.0 - 1.0)
    'default_duration': 0.25,   # Default vibration duration (seconds) – legacy
    'detection_interval': 0.25, # Minimum time between haptic updates
    'pulse_interval': 0.5,     # Non-blocking: min seconds between pulses
    'pulse_duration': 0.05,    # Non-blocking: duration of each pulse (seconds)
}

# ============================================
# Button Configuration
# ============================================
BUTTON_CONFIG = {
    'pin': 27,                   # GPIO pin for button (BCM mode)
    'pull_up': True,            # Use pull-up resistor
    'active_low': True,         # Button active when LOW
    'debounce_time': 0.01,      # Debounce delay (seconds)
}
