"""
Camera Interface Module
Handles camera capture for Mac (testing) and Raspberry Pi (picamera2)
"""
import cv2
import numpy as np
from typing import Optional


class CameraInterface:
    def __init__(
        self,
        camera_id: int = 0,
        width: int = 640,
        height: int = 480,
        picamera_config: Optional[dict] = None,
    ):
        """
        Initialize camera interface
        
        Args:
            camera_id: Camera device ID (0 for default/Mac camera)
            width: Frame width
            height: Frame height
            picamera_config: Optional Pi camera controls dictionary
        """
        picamera_config = picamera_config or {}

        self.camera_id = camera_id
        self.width = width
        self.height = height
        self.picamera_format = picamera_config.get('format', 'BGR888')
        self.exposure_time_us = picamera_config.get('exposure_time_us')
        self.analogue_gain = picamera_config.get('analogue_gain')
        self.af_mode = str(picamera_config.get('af_mode', 'continuous')).lower()
        self.lens_position = picamera_config.get('lens_position')
        self.cap = None
        self.picam2 = None
        self._is_pi = self._check_raspberry_pi()
        self._use_picamera = False

    def _build_picamera_controls(self):
        """Build libcamera controls for exposure and focus tuning."""
        controls = {}

        if self.exposure_time_us is not None:
            controls['AeEnable'] = False
            controls['ExposureTime'] = int(self.exposure_time_us)
            if self.analogue_gain is not None:
                controls['AnalogueGain'] = float(self.analogue_gain)

        af_mode_map = {
            'manual': 0,
            'auto': 1,
            'continuous': 2,
        }
        controls['AfMode'] = af_mode_map.get(self.af_mode, 2)

        if self.af_mode == 'manual' and self.lens_position is not None:
            controls['LensPosition'] = float(self.lens_position)

        return controls
    
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
                    main={"size": (self.width, self.height), "format": self.picamera_format}
                )
                self.picam2.configure(config)
                controls = self._build_picamera_controls()
                if controls:
                    try:
                        self.picam2.set_controls(controls)
                        print(f"PiCamera2 controls applied: {controls}")
                    except Exception as control_error:
                        print(f"PiCamera2 controls not fully applied: {control_error}")
                self.picam2.start()
                self._use_picamera = True
                print(f"PiCamera2 started: {self.width}x{self.height}")
                # Add warmup time for camera
                import time
                time.sleep(2)
                return True
            except ImportError:
                print("picamera2 not available, falling back to OpenCV")
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
        # Use picamera2 if available
        if self._use_picamera and self.picam2 is not None:
            try:
                frame = self.picam2.capture_array()
                frame = cv2.rotate(frame, cv2.ROTATE_180)
                # Convert BGRA to BGR if needed
                if frame.ndim == 3 and frame.shape[2] == 4:
                    frame = cv2.cvtColor(frame, cv2.COLOR_RGBA2BGR)
                return frame
            except Exception as e:
                print(f"Error reading from picamera2: {e}")
                return None
        
        # Use OpenCV
        if self.cap is None or not self.cap.isOpened():
            return None
        
        ret, frame = self.cap.read()
        
        if not ret:
            print("Error: Failed to read frame")
            return None
            
        frame = cv2.rotate(frame, cv2.ROTATE_180)
        return frame
    
    def stop(self):
        """Stop camera capture and release resources"""
        if self.picam2 is not None:
            try:
                self.picam2.stop()
            except Exception:
                pass
            self.picam2 = None
            self._use_picamera = False

        if self.cap is not None:
            self.cap.release()
            self.cap = None
        print("Camera stopped")
