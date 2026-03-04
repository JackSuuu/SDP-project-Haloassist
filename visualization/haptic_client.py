#!/usr/bin/env python3
"""
Client module to send haptic updates to the visualizer
Import this in your perception system to send motor updates
"""
import requests
from typing import Optional
import threading


class HapticVisualizer:
    """Client for sending motor updates to the web visualizer"""
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.enabled = True
        self._last_state = None
    
    def _send_async(self, endpoint: str, data: dict):
        """Send request in background thread to avoid blocking"""
        def send():
            try:
                requests.post(
                    f"{self.base_url}{endpoint}",
                    json=data,
                    timeout=0.5
                )
            except Exception:
                pass  # Don't block on visualizer errors
        
        if self.enabled:
            thread = threading.Thread(target=send, daemon=True)
            thread.start()
    
    def update_motors(
        self,
        left: bool,
        right: bool,
        intensity_left: float = 1.0,
        intensity_right: float = 1.0,
        target_object: Optional[str] = None,
        position: Optional[str] = None
    ):
        """
        Update motor state on the visualizer
        
        Args:
            left: Left motor active
            right: Right motor active
            intensity_left: Left motor intensity (0.0 - 1.0)
            intensity_right: Right motor intensity (0.0 - 1.0)
            target_object: Name of detected object
            position: Position of object ("left", "right", "center")
        """
        state = {
            "left": left,
            "right": right,
            "intensity_left": intensity_left if left else 0.0,
            "intensity_right": intensity_right if right else 0.0,
            "target_object": target_object,
            "position": position
        }
        
        # Only send if state changed
        if state != self._last_state:
            self._last_state = state.copy()
            self._send_async("/api/motor/update", state)
    
    def detection(
        self,
        target_object: str,
        position: str,
        confidence: float = 0.8
    ):
        """
        Send detection update - automatically triggers appropriate motors
        
        Args:
            target_object: Name of detected object
            position: "left", "right", or "center"
            confidence: Detection confidence (0.0 - 1.0)
        """
        self._send_async("/api/detection", {
            "target_object": target_object,
            "position": position,
            "confidence": confidence
        })
    
    def left_motor(self, active: bool, intensity: float = 1.0):
        """Control left motor only"""
        if active:
            self.update_motors(True, False, intensity, 0.0, position="left")
        else:
            self.stop()
    
    def right_motor(self, active: bool, intensity: float = 1.0):
        """Control right motor only"""
        if active:
            self.update_motors(False, True, 0.0, intensity, position="right")
        else:
            self.stop()
    
    def both_motors(self, active: bool, intensity: float = 1.0):
        """Control both motors (center position)"""
        if active:
            self.update_motors(True, True, intensity, intensity, position="center")
        else:
            self.stop()
    
    def stop(self):
        """Stop all motors"""
        self._last_state = None
        self._send_async("/api/motor/stop", {})
    
    def searching(self, target_object: str):
        """
        Signal that the system is searching for an object (no detection yet).
        Shows 'SEARCHING' on the head with scanning eyes.
        """
        self._send_async("/api/motor/update", {
            "left": False,
            "right": False,
            "intensity_left": 0.0,
            "intensity_right": 0.0,
            "target_object": target_object,
            "position": None
        })


# Global instance for easy access
_visualizer = None

def get_visualizer(base_url: str = "http://localhost:8000") -> HapticVisualizer:
    """Get or create the global visualizer instance"""
    global _visualizer
    if _visualizer is None:
        _visualizer = HapticVisualizer(base_url)
    return _visualizer


# Convenience functions
def send_detection(target: str, position: str, confidence: float = 0.8):
    """Quick function to send a detection update"""
    get_visualizer().detection(target, position, confidence)

def send_motor_update(left: bool, right: bool, target: str = None, position: str = None):
    """Quick function to update motor state"""
    get_visualizer().update_motors(left, right, target_object=target, position=position)

def stop_motors():
    """Quick function to stop all motors"""
    get_visualizer().stop()


if __name__ == "__main__":
    # Demo usage
    import time
    
    print("Haptic Visualizer Client Demo")
    print("Make sure the server is running: python server.py")
    print()
    
    viz = get_visualizer()
    
    print("Testing left motor...")
    viz.detection("demo_object", "left", 0.9)
    time.sleep(2)
    
    print("Testing right motor...")
    viz.detection("demo_object", "right", 0.85)
    time.sleep(2)
    
    print("Testing both motors (center)...")
    viz.detection("demo_object", "center", 0.95)
    time.sleep(2)
    
    print("Stopping all motors...")
    viz.stop()
    
    print("Demo complete!")
