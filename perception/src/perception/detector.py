import numpy as np
from ultralytics import YOLO
from dataclasses import dataclass
from typing import Optional, Tuple, List

# Cache to store loaded models so we don't reload them on every single frame
_model_cache = {}

# Explicit inference size for YOLO letterbox resize.
INFERENCE_IMGSZ = 640

@dataclass
class DetectionObject:
    """
    Custom object to hold the details of our target detection.
    """
    bbox: List[float]            # [x1, y1, x2, y2] format
    center: Tuple[float, float]  # (cx, cy) format
    confidence: float            # Detection confidence (0.0 to 1.0)


def detect_target_object(
    frame: np.ndarray, 
    min_conf: float, 
    target_obj: str, 
    model_path: str
) -> Optional[DetectionObject]:
    """
    Runs a YOLO model on an image frame and returns the highest confidence 
    detection matching the target object string.

    Args:
        frame (np.ndarray): Image frame in BGR format (Standard OpenCV format).
            The frame is inferred at imgsz=640 for consistent performance/latency.
        min_conf (float): Minimum confidence threshold (e.g., 0.5).
        target_obj (str): The name of the object to look for (e.g., 'person', 'car').
        model_path (str): Path to the YOLO model weights (e.g., 'yolov8n.pt' or 'yolov8s-world.pt').

    Returns:
        DetectionObject: Bbox, center, and confidence of the best match, or None if no match.
    """
    # 1. Load or retrieve the model from cache
    if model_path not in _model_cache:
        _model_cache[model_path] = YOLO(model_path)
    
    model = _model_cache[model_path]

    # Optional handling for Open-Vocab models (like YOLO-World)
    # If the model has a set_classes method, we can dynamically assign the target
    if hasattr(model, 'set_classes'):
        model.set_classes([target_obj])

    # 2. Run inference with explicit confidence threshold.
    # Ultralytics defaults to conf=0.25 if not provided, which can hide low-confidence
    # detections before our own target filtering logic runs.
    inference_conf = max(0.001, min(1.0, float(min_conf)))
    results = model(frame, imgsz=INFERENCE_IMGSZ, conf=inference_conf, verbose=False)
    
    best_box = None
    highest_conf = -1.0
    
    # 3. Parse the results
    for result in results:
        boxes = result.boxes
        names = result.names  # Dictionary mapping class IDs to class names
        
        for box in boxes:
            conf = float(box.conf[0])
            cls_id = int(box.cls[0])
            cls_name = names[cls_id]
            
            # Check if this detection is the target object and meets the threshold
            if cls_name.lower() == target_obj.lower() and conf >= min_conf:
                # Keep track of the highest confidence detection
                if conf > highest_conf:
                    highest_conf = conf
                    best_box = box

    # 4. Return None if no detections met the criteria
    if best_box is None:
        return None
        
    # 5. Extract coordinates and calculate the center point
    # xyxy gives us bounding box coordinates in [x1, y1, x2, y2] format
    x1, y1, x2, y2 = best_box.xyxy[0].tolist()
    
    cx = (x1 + x2) / 2.0
    cy = (y1 + y2) / 2.0
    
    return DetectionObject(
        bbox=[x1, y1, x2, y2],
        center=(cx, cy),
        confidence=highest_conf
    )