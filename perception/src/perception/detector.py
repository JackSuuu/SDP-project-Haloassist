"""
Object Detector Module
Uses YOLO-World for real-time object detection in home/supermarket scenarios
Supports configurable models for different hardware (Pi3/Pi4/Pi5)
"""
import cv2
import numpy as np
from ultralytics import YOLOWorld, YOLO
from typing import List, Tuple, Dict
import sys
from pathlib import Path

# Add config directory to path
config_dir = Path(__file__).parent.parent.parent / 'config'
sys.path.insert(0, str(config_dir))

from hardware_config import YOLO_CONFIG, PRIORITY_OBJECTS


class ObjectDetector:
    def __init__(self, model_path: str = 'yolov8s-world.pt', 
                 conf_threshold: float = None,
                 imgsz: int = None,
                 custom_classes: List[str] = None):
        """
        Initialize YOLO object detector (supports YOLO-World and standard YOLO)
        
        Args:
            model_path: Path to YOLO model weights
            conf_threshold: Confidence threshold (uses config default if None)
            imgsz: Input image size (uses config default if None)
            custom_classes: Custom object classes for YOLO-World (uses config default if None)
        """
        # Use configuration defaults if not specified
        self.conf_threshold = conf_threshold or YOLO_CONFIG['conf_threshold']
        self.imgsz = imgsz or YOLO_CONFIG['imgsz']
        self.priority_objects = custom_classes or PRIORITY_OBJECTS
        
        # Determine model type (YOLO-World vs standard YOLO)
        self.is_yolo_world = 'world' in model_path.lower()
        
        # Initialize model
        if self.is_yolo_world:
            self.model = YOLOWorld(model_path)
            # Set custom classes for YOLO-World
            self.model.set_classes(self.priority_objects)
            print(f"YOLO-World model loaded: {model_path}")
            print(f"Custom classes: {len(self.priority_objects)} objects")
        else:
            self.model = YOLO(model_path)
            print(f"Standard YOLO model loaded: {model_path}")
        
        print(f"Detection config: conf={self.conf_threshold}, imgsz={self.imgsz}")
    
    def detect(self, frame: np.ndarray) -> List[Dict]:
        """
        Detect objects in frame
        
        Args:
            frame: Input image frame (BGR format)
            
        Returns:
            List of detected objects with bbox, class, confidence
        """
        results = self.model(frame, conf=self.conf_threshold, imgsz=self.imgsz, verbose=False)[0]
        
        detections = []
        for box in results.boxes:
            x1, y1, x2, y2 = box.xyxy[0].cpu().numpy()
            conf = float(box.conf[0])
            cls_id = int(box.cls[0])
            cls_name = results.names[cls_id]
            
            # Calculate center point
            center_x = int((x1 + x2) / 2)
            center_y = int((y1 + y2) / 2)
            
            detection = {
                'bbox': [int(x1), int(y1), int(x2), int(y2)],
                'center': (center_x, center_y),
                'class': cls_name,
                'confidence': conf,
                'priority': cls_name.lower() in [obj.lower() for obj in self.priority_objects]
            }
            detections.append(detection)
        
        return detections
    
    def get_closest_object(self, detections: List[Dict], frame_shape: Tuple[int, int]) -> Dict:
        """
        Get the closest/most relevant object for hand guidance
        
        Args:
            detections: List of detected objects
            frame_shape: (height, width) of frame
            
        Returns:
            Most relevant detection or None
        """
        if not detections:
            return None
        
        frame_center = (frame_shape[1] // 2, frame_shape[0] // 2)
        
        # Prioritize objects by: priority flag, then proximity to center, then size
        priority_detections = [d for d in detections if d['priority']]
        candidates = priority_detections if priority_detections else detections
        
        # Calculate score based on distance from center and size
        for det in candidates:
            cx, cy = det['center']
            dist = np.sqrt((cx - frame_center[0])**2 + (cy - frame_center[1])**2)
            
            bbox_area = (det['bbox'][2] - det['bbox'][0]) * (det['bbox'][3] - det['bbox'][1])
            frame_area = frame_shape[0] * frame_shape[1]
            size_ratio = bbox_area / frame_area
            
            # Lower score is better (closer to center and larger)
            det['score'] = dist * (1 - size_ratio * 0.5)
        
        return min(candidates, key=lambda x: x['score'])
