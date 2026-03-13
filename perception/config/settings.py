# Configuration for Perception System
import hardware_config

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
DEFAULT_MODEL = 'yolo26n'

# YOLO inference settings
YOLO_CONFIG = {
    'conf_threshold': 0.25,
    'imgsz': 640,
    'verbose': False,
}

# Detection settings
CONFIDENCE_THRESHOLD = 0.5
MODEL_PATH = "yolov8s-world.pt"

# ============================================
# Text-to-Speech (Piper) Configuration
# ============================================
TTS_CONFIG = {
    'model_path': '/home/ubuntu/piper-voices/en_US-lessac-medium/en_US-lessac-medium.onnx',
    'output_sample_rate': 22050,
}

# ============================================
# Speech-to-Text Configuration
# ============================================
STT_CONFIG = {
    'model_path': '/home/ubuntu/vosk-model/vosk-model-small-en-us-0.15',
    'sample_rate': 16000,
    'duration': 3,
    'block_size': 8000,
}

# ============================================
# Detection Configuration
# ============================================
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
    'show_display': True,
    'enable_speech': False,
    'enable_button': True,
    'fps_display': True,
    'detect_interval': 0.05,
}

# ============================================
# Platform-Specific Profiles
# ============================================
def get_profile(platform='pi3'):
    """
    Get optimized configuration profile for a specific platform.

    Args:
        platform: 'pi3', 'pi4', 'pi5', or 'mac'

    Returns:
        dict: Configuration overrides for the platform
    """
    profiles = {
        'pi3': {
            'model': 'nano',
            'imgsz': 160,
            'camera_width': 640,
            'camera_height': 480,
        },
        'pi4': {
            'model': 'small',
            'imgsz': 320,
            'camera_width': 640,
            'camera_height': 480,
        },
        'pi5': {
            'model': 'medium',
            'imgsz': 640,
            'camera_width': 1280,
            'camera_height': 720,
        },
        'mac': {
            'model': 'world-small',
            'imgsz': 640,
            'camera_width': 640,
            'camera_height': 480,
        },
    }

    return profiles.get(platform, profiles['mac'])


def apply_profile(platform='pi3'):
    """
    Apply platform-specific configuration profile.

    Args:
        platform: Platform identifier ('pi3', 'pi4', 'pi5', 'mac')
    """
    global DEFAULT_MODEL

    profile = get_profile(platform)

    DEFAULT_MODEL = profile['model']
    YOLO_CONFIG['imgsz'] = profile['imgsz']
    hardware_config.CAMERA_CONFIG['width'] = profile['camera_width']
    hardware_config.CAMERA_CONFIG['height'] = profile['camera_height']

    print(f"Applied {platform.upper()} configuration profile")
    print(f"  Model: {YOLO_MODELS[DEFAULT_MODEL]}")
    print(f"  Image size: {YOLO_CONFIG['imgsz']}")
    print(f"  Camera: {hardware_config.CAMERA_CONFIG['width']}x{hardware_config.CAMERA_CONFIG['height']}")
