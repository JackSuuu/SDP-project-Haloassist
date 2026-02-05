"""
Camera Interface Module
Handles camera capture for Mac (testing) and Raspberry Pi (picamera2)
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
        self.picam2 = None
        self._is_pi = self._check_raspberry_pi()
        self._use_picamera = False
    
    def _check_raspberry_pi(self) -> bool:
        """Check if running on Raspberry Pi"""
        try:
            with open('/proc/device-tree/model', 'r') as f:
                model = f.read()
                return 'raspberry pi' in model.lower()
        except:
            return False
        
    def start(self) -> bool:
        """
        Start camera capture (uses picamera2 on Pi, OpenCV on Mac)
        
        Returns:
            True if successful, False otherwise
        """
        # Try picamera2 first if on Raspberry Pi
        if self._is_pi:
            try:
                from picamera2 import Picamera2
                self.picam2 = Picamera2()
                config = self.picam2.create_preview_configuration(
                    main={"size": (self.width, self.height)}
                )
                self.picam2.configure(config)
                self.picam2.start()
                self._use_picamera = True
                print(f"PiCamera2 started: {self.width}x{self.height}")
                return True
            except ImportError:
                print("picamera2 not available, falling back to OpenCV")
        # Use picamera2 if available
        if self._use_picamera and self.picam2 is not None:
            try:
                frame = self.picam2.capture_array()
                # Convert BGRA to BGR if needed
                if frame.shape[2] == 4:
                    frame = cv2.cvtColor(frame, cv2.COLOR_BGRA2BGR)
                return frame
            except Exception as e:
                print(f"Error reading from picamera2: {e}")
                return None
        
        # Use OpenCV fallback
            except Exception as e:
                print(f"Failed to initialize picamera2: {e}, falling back to OpenCV")
        
        # Fallback to OpenCV (for Mac or if picamera2 fails)
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
        print(f"OpenCV camera started: {actual_width}x{actual_height}")
        
        return True
    
    def read_frame(self) -> Optional[np.ndarray]:
        """
        Read a frame from camera
        
        Returns:
            Frame as numpy array (BGR) or None if failed
        """
        if self._use_picamera and self.picam2 is not None:
            try:
                self.picam2.stop()
                self.picam2.close()
                self.picam2 = None
                print("PiCamera2 stopped")
            except Exception as e:
                print(f"Error stopping picamera2: {e}")
        
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
