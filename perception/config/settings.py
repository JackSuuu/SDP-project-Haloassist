# Configuration for Perception System

# Detection settings
CONFIDENCE_THRESHOLD = 0.5
MODEL_PATH = "yolov8s-world.pt"

# Camera settings
CAMERA_ID = 0
FRAME_WIDTH = 640
FRAME_HEIGHT = 480

# Haptic feedback settings
NUM_MOTORS = 8
MOTOR_PINS = [17, 18, 27, 22, 23, 24, 25, 4]
VIBRATION_DURATION = 0.2

# Priority objects for home/supermarket scenarios
PRIORITY_OBJECTS = [
    'person', 'chair', 'couch', 'bed', 'dining table', 'bottle',
    'cup', 'bowl', 'apple', 'banana', 'orange', 'broccoli',
    'carrot', 'refrigerator', 'microwave', 'oven', 'sink',
    'door', 'stairs', 'shelf', 'knife', 'spoon', 'fork', 'phone'
]
