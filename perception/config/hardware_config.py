"""
Hardware Configuration
Centralized configuration for hardware components and model selection
Easy to modify for different hardware setups (Pi3/Pi5, motor arrays, etc.)
"""

# ============================================
# YOLO Model Configuration
# ============================================
YOLO_MODELS = {
    'yolo26n': 'yolo26n.pt',        # YOLO 26 nano (default)
    'nano': 'yolov8n.pt',           # Fastest, lowest accuracy (Pi3)
    'small': 'yolov8s.pt',          # Balanced (Pi4)
    'medium': 'yolov8m.pt',         # Better accuracy (Pi5)
    'world-small': 'yolov8s-world.pt',   # YOLO-World small
    'world-medium': 'yolov8m-world.pt',  # YOLO-World medium
}

# Default model selection based on platform
DEFAULT_MODEL = 'yolo26n'  # Using yolo26n.pt as default

# YOLO inference settings
YOLO_CONFIG = {
    'conf_threshold': 0.25,     # Confidence threshold
    'imgsz': 640,              # Input image size (160 for Pi3, 640 for Pi5)
    'verbose': False,           # Suppress YOLO output
}

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

# Current setup (2 motors - left/right)
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

# Active motor configuration (change for different setups)
MOTOR_PINS = MOTOR_PINS_2  # Switch to MOTOR_PINS_8 for 8-motor array

# Haptic feedback settings
HAPTIC_CONFIG = {
    'default_strength': 0.5,    # Default motor strength (0.0 - 1.0)
    'default_duration': 0.25,   # Default vibration duration (seconds)
    'detection_interval': 0.25, # Minimum time between haptic updates
}

# ============================================
# Button Configuration
# ============================================
BUTTON_CONFIG = {
    'pin': 5,                   # GPIO pin for button (BCM mode)
    'pull_up': True,            # Use pull-up resistor
    'active_low': True,         # Button active when LOW
    'debounce_time': 0.01,      # Debounce delay (seconds)
}

# ============================================
# Speech-to-Text Configuration
# ============================================
STT_CONFIG = {
    'model_path': '/home/pi/vosk-model/vosk-model-small-en-us-0.15',
    'sample_rate': 16000,
    'duration': 3,              # Recording duration (seconds)
    'block_size': 8000,
}

# ============================================
# Detection Configuration
# ============================================
# Priority objects for detection (YOLO-World custom classes)
PRIORITY_OBJECTS = [
    # Furniture & Structure
    'chair', 'couch', 'bed', 'dining table', 'door', 'stairs', 'shelf',
    
    # Kitchen
    'refrigerator', 'microwave', 'oven', 'sink', 'bottle', 'cup', 'bowl',
    
    # Food
    'apple', 'banana', 'orange', 'broccoli', 'carrot',
    
    # Utensils
    'knife', 'spoon', 'fork', 'plate', 'glass',
    
    # Common objects
    'person', 'can', 'box', 'bag', 'laptop', 'phone', 'book',
]

# ============================================
# System Configuration
# ============================================
SYSTEM_CONFIG = {
    'show_display': True,       # Show visual output (False for headless Pi)
    'enable_speech': False,     # Enable speech input
    'enable_button': True,      # Enable button input
    'fps_display': True,        # Show FPS on display
    'detect_interval': 0.05,    # Main loop delay (seconds)
}

# ============================================
# Platform-Specific Profiles
# ============================================
def get_profile(platform='pi3'):
    """
    Get optimized configuration profile for specific platform
    
    Args:
        platform: 'pi3', 'pi4', 'pi5', 'mac', or 'custom'
    
    Returns:
        dict: Configuration overrides for the platform
    """
    profiles = {
        'pi3': {
            'model': 'nano',
            'imgsz': 160,
            'camera_width': 640,
            'camera_height': 480,
            'motor_pins': MOTOR_PINS_2,
        },
        'pi4': {
            'model': 'small',
            'imgsz': 320,
            'camera_width': 640,
            'camera_height': 480,
            'motor_pins': MOTOR_PINS_2,
        },
        'pi5': {
            'model': 'medium',
            'imgsz': 640,
            'camera_width': 1280,
            'camera_height': 720,
            'motor_pins': MOTOR_PINS_8,  # Support for 8-motor array
        },
        'mac': {
            'model': 'world-small',
            'imgsz': 640,
            'camera_width': 640,
            'camera_height': 480,
            'motor_pins': MOTOR_PINS_2,
        },
    }
    
    return profiles.get(platform, profiles['mac'])


def apply_profile(platform='pi3'):
    """
    Apply platform-specific configuration profile
    
    Args:
        platform: Platform identifier ('pi3', 'pi4', 'pi5', 'mac')
    """
    global DEFAULT_MODEL, MOTOR_PINS
    
    profile = get_profile(platform)
    
    DEFAULT_MODEL = profile['model']
    YOLO_CONFIG['imgsz'] = profile['imgsz']
    CAMERA_CONFIG['width'] = profile['camera_width']
    CAMERA_CONFIG['height'] = profile['camera_height']
    MOTOR_PINS = profile['motor_pins']
    
    print(f"Applied {platform.upper()} configuration profile")
    print(f"  Model: {YOLO_MODELS[DEFAULT_MODEL]}")
    print(f"  Image size: {YOLO_CONFIG['imgsz']}")
    print(f"  Camera: {CAMERA_CONFIG['width']}x{CAMERA_CONFIG['height']}")
    print(f"  Motors: {len(MOTOR_PINS)}")
