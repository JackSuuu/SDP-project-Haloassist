# Configuration for Perception System

# ============================================
# YOLO Model Configuration
# ============================================
YOLO_MODELS = {
    'yolo26n': '../models/yolo26n.pt',        # YOLO 26 nano (default)
    'nano': '../models/yolov8n.pt',           # Fastest, lowest accuracy (Pi3)
    'small': '../models/yolov8s.pt',          # Balanced (Pi4)
    'medium': '../models/yolov8m.pt',         # Better accuracy (Pi5)
    'world-small': '../models/yolov8s-world.pt',   # YOLO-World small
    'world-medium': '../models/yolov8m-world.pt',  # YOLO-World medium
}

# Default model selection based on platform
DEFAULT_MODEL = 'yolo26n'  # Using yolo26n.pt as default

# YOLO inference settings
YOLO_CONFIG = {
    'conf_threshold': 0.25,     # Confidence threshold
    'imgsz': 640,              # Input image size (160 for Pi3, 640 for Pi5)
    'verbose': False,           # Suppress YOLO output
}

# Detection settings
CONFIDENCE_THRESHOLD = 0.5
MODEL_PATH = "yolov8s-world.pt"

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

# Camera settings
CAMERA_ID = 0
FRAME_WIDTH = 160
FRAME_HEIGHT = 160

# ============================================
# Text-to-Speech (Piper) Configuration
# ============================================
TTS_CONFIG = {
    'model_path': '/home/ubuntu/piper-voices/en_US-lessac-medium/en_US-lessac-medium.onnx',
    'output_sample_rate': 22050,  # Piper raw PCM output rate
}

# ============================================
# Speech-to-Text Configuration
# ============================================
STT_CONFIG = {
    'model_path': '/home/ubuntu/vosk-model/vosk-model-small-en-us-0.15',
    'sample_rate': 16000,
    'duration': 3,              # Recording duration (seconds) – legacy fixed mode
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

# Haptic feedback settings
NUM_MOTORS = 8
MOTOR_PINS = [17, 18, 27, 22, 23, 24, 25, 4]
VIBRATION_DURATION = 0.2
