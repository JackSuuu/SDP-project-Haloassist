"""
Unit tests for object detector
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

import pytest
import numpy as np
from detector import ObjectDetector


def test_detector_initialization():
    """Test detector can be initialized"""
    detector = ObjectDetector(model_path='yolov8s-world.pt')
    assert detector is not None
    assert detector.conf_threshold == 0.5


def test_priority_objects():
    """Test priority objects are defined"""
    detector = ObjectDetector()
    assert len(detector.priority_objects) > 0
    assert 'person' in detector.priority_objects
    assert 'bottle' in detector.priority_objects


def test_get_closest_object_empty():
    """Test get_closest_object with no detections"""
    detector = ObjectDetector()
    result = detector.get_closest_object([], (480, 640))
    assert result is None


def test_get_closest_object_single():
    """Test get_closest_object with single detection"""
    detector = ObjectDetector()
    
    detections = [{
        'bbox': [100, 100, 200, 200],
        'center': (150, 150),
        'class': 'bottle',
        'confidence': 0.9,
        'priority': True
    }]
    
    result = detector.get_closest_object(detections, (480, 640))
    assert result is not None
    assert result['class'] == 'bottle'


def test_get_closest_object_priority():
    """Test priority objects are preferred"""
    detector = ObjectDetector()
    
    detections = [
        {
            'bbox': [100, 100, 200, 200],
            'center': (150, 150),
            'class': 'bottle',
            'confidence': 0.9,
            'priority': True
        },
        {
            'bbox': [300, 300, 400, 400],
            'center': (350, 350),
            'class': 'unknown',
            'confidence': 0.95,
            'priority': False
        }
    ]
    
    result = detector.get_closest_object(detections, (480, 640))
    assert result['priority'] == True


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
