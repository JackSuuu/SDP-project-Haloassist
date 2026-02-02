"""
Camera Interface Module
Handles camera capture for Mac (testing) and Raspberry Pi
"""
import cv2
import numpy as np
from typing import Optional


class CameraInterface:
    def __init__(self, camera_id: int = 0, width: int = 640, height: int = 480):
        """
        Initialize camera interface
        
        Args:
            camera_id: Camera device ID (0 for default/Mac camera)
            width: Frame width
            height: Frame height
        """
        self.camera_id = camera_id
        self.width = width
        self.height = height
        self.cap = None
        
    def start(self) -> bool:
        """
        Start camera capture
        
        Returns:
            True if successful, False otherwise
        """
        self.cap = cv2.VideoCapture(self.camera_id)
        
        if not self.cap.isOpened():
            print(f"Error: Could not open camera {self.camera_id}")
            return False
        
        # Set resolution
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.width)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.height)
        
        # Verify settings
        actual_width = int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        actual_height = int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        print(f"Camera started: {actual_width}x{actual_height}")
        
        return True
    
    def read_frame(self) -> Optional[np.ndarray]:
        """
        Read a frame from camera
        
        Returns:
            Frame as numpy array (BGR) or None if failed
        """
        if self.cap is None or not self.cap.isOpened():
            return None
        
        ret, frame = self.cap.read()
        
        if not ret:
            print("Error: Failed to read frame")
            return None
        
        return frame
    
    def stop(self):
        """Stop camera capture and release resources"""
        if self.cap is not None:
            self.cap.release()
            self.cap = None
            print("Camera stopped")
