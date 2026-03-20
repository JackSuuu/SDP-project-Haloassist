"""
Perception Configuration
YOLO model paths, inference settings, detection objects, and platform profiles.
"""
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
    'yoloe-nano': '../models/yoloe-26n-seg.pt',  # YOLOE Nano
    'yoloe-small': '../models/yoloe-26s-seg.pt',  # YOLOE Small
}

DEFAULT_MODEL = 'yoloe-nano'  # Default model key

# Dynamically fetch the model path
MODEL_PATH = YOLO_MODELS[DEFAULT_MODEL]

YOLO_CONFIG = {
    'conf_threshold': 0.25,
    'imgsz': 640,
    'verbose': False,
}

CONFIDENCE_THRESHOLD = 0.5

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
        'windows': {
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
