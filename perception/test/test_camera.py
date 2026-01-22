"""
Unit tests for camera interface
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

import pytest
from camera import CameraInterface


def test_camera_initialization():
    """Test camera can be initialized"""
    camera = CameraInterface(camera_id=0)
    assert camera is not None
    assert camera.camera_id == 0
    assert camera.width == 640
    assert camera.height == 480


def test_camera_custom_resolution():
    """Test camera with custom resolution"""
    camera = CameraInterface(camera_id=0, width=1280, height=720)
    assert camera.width == 1280
    assert camera.height == 720


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
