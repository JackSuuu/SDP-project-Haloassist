"""
Object Detector Module
Uses YOLO-World for real-time object detection in home/supermarket scenarios
"""
import cv2
import numpy as np
from ultralytics import YOLOWorld
from typing import List, Tuple, Dict


class ObjectDetector:
    def __init__(self, model_path: str = 'yolov8s-world.pt', conf_threshold: float = 0.5):
        """
        Initialize YOLO-World object detector
        
        Args:
            model_path: Path to YOLO-World model weights
            conf_threshold: Confidence threshold for detections
        """
        self.model = YOLOWorld(model_path)
        self.conf_threshold = conf_threshold
        
        # Common objects in home/supermarket scenarios
        self.priority_objects = [
            'person', 'chair', 'couch', 'bed', 'dining table', 'bottle',
            'cup', 'bowl', 'apple', 'banana', 'orange', 'broccoli',
            'carrot', 'refrigerator', 'microwave', 'oven', 'sink',
            'door', 'stairs', 'shelf', 'knife', 'spoon', 'fork',
            'plate', 'glass', 'can', 'box', 'bag'
        ]
        
        # Set custom classes for YOLO-World
        self.model.set_classes(self.priority_objects)
    
    def detect(self, frame: np.ndarray) -> List[Dict]:
        """
        Detect objects in frame
        
        Args:
            frame: Input image frame (BGR format)
            
        Returns:
            List of detected objects with bbox, class, confidence
        """
        results = self.model(frame, conf=self.conf_threshold, verbose=False)[0]
        
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
