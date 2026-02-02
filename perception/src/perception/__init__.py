"""
Perception Components Module
Handles camera and object detection
"""
from .camera import CameraInterface
from .detector import ObjectDetector

__all__ = ['CameraInterface', 'ObjectDetector']
