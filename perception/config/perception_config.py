"""
Perception Configuration
Minimal model and detection settings for target-object mode.
"""
from pathlib import Path


MODELS_DIR = Path(__file__).resolve().parent.parent / 'models'

YOLO_MODELS = {
    'yolo26n': str(MODELS_DIR / 'yolo26n.pt'),
    'yoloe-26-seg': str(MODELS_DIR / 'yoloe-26n-seg.pt'),
}

CONFIDENCE_THRESHOLD = 0.5
MIN_CONFIDENCE_THRESHOLD = 0.01
CONFIDENCE_DECAY_PER_MISS = 0.03
CONFIDENCE_SUCCESS_MARGIN = 0.07
YOLOE_CONFIDENCE_DISCOUNT = 0.08

# COCO 80-class taxonomy used by closed-vocabulary YOLO models.
COCO_CLASSES = {
    'person', 'bicycle', 'car', 'motorcycle', 'airplane', 'bus', 'train', 'truck', 'boat',
    'traffic light', 'fire hydrant', 'stop sign', 'parking meter', 'bench', 'bird', 'cat',
    'dog', 'horse', 'sheep', 'cow', 'elephant', 'bear', 'zebra', 'giraffe', 'backpack',
    'umbrella', 'handbag', 'tie', 'suitcase', 'frisbee', 'skis', 'snowboard', 'sports ball',
    'kite', 'baseball bat', 'baseball glove', 'skateboard', 'surfboard', 'tennis racket',
    'bottle', 'wine glass', 'cup', 'fork', 'knife', 'spoon', 'bowl', 'banana', 'apple',
    'sandwich', 'orange', 'broccoli', 'carrot', 'hot dog', 'pizza', 'donut', 'cake', 'chair',
    'couch', 'potted plant', 'bed', 'dining table', 'toilet', 'tv', 'laptop', 'mouse',
    'remote', 'keyboard', 'cell phone', 'microwave', 'oven', 'toaster', 'sink',
    'refrigerator', 'book', 'clock', 'vase', 'scissors', 'teddy bear', 'hair drier',
    'toothbrush',
}
