# Perception Code Structure Fix Notes

## Problem Summary

The original codebase suffered from the following issues:

1. **Redundant Definitions**: `hardware.py` redefined classes that already existed within the `hardware/` directory.
2. **Import Chaos**: Modules were being imported from incorrect paths across multiple files.
3. **Misplaced Files**: `camera`, `detector`, and `haptic` files were located in the `src` root instead of their respective subdirectories.

## Fixes Applied

### 1. File Reorganization

**Moved files to their correct locations:**

* `src/camera.py` → `src/perception/camera.py`
* `src/detector.py` → `src/perception/detector.py`
* `src/haptic.py` → `src/feedback/haptic_legacy.py`
* `src/haptic_two_motor.py` → `src/feedback/haptic_two_motor.py`

### 2. Refactoring `hardware.py`

**Before**: Contained full class definitions (redundant code).

```python
class ButtonInterface:
    def __init__(...):
        # Full implementation

```

**After**: Acts as a clean entry point for imports.

```python
from hardware.button import ButtonInterface
from hardware.tts import TTSInterface
from hardware.motors import VibrationalMotorController

__all__ = ['ButtonInterface', 'TTSInterface', 'VibrationalMotorController']

```

### 3. Updating All Import Statements

#### `hardware_main.py`

```python
# Before
from detector import ObjectDetector
from camera import CameraInterface
from hardware import ButtonInterface, TTSInterface, VibrationalMotorController
from haptic_two_motor import TwoMotorHapticFeedback

# After
from perception.camera import CameraInterface
from perception.detector import ObjectDetector
from hardware import ButtonInterface, TTSInterface, VibrationalMotorController
from feedback.haptic_two_motor import TwoMotorHapticFeedback

```

#### `main.py`

```python
# Before
from detector import ObjectDetector
from haptic import HapticFeedback
from camera import CameraInterface

# After
from perception.detector import ObjectDetector
from feedback.haptic_legacy import HapticFeedback
from perception.camera import CameraInterface

```

#### `feedback/haptic_two_motor.py`

```python
# Before
from hardware import VibrationalMotorController

# After
from hardware.motors import VibrationalMotorController

```

#### Test Files

Updated all test files to use correct module paths:

* `test/test_camera.py`: `from perception.camera import CameraInterface`
* `test/test_detector.py`: `from perception.detector import ObjectDetector`
* `test/test_haptic.py`: `from feedback.haptic_legacy import HapticFeedback`

---

## New Code Structure

```text
perception/
├── src/
│   ├── main.py                    # Main program entry
│   ├── hardware_main.py           # Hardware integration system
│   ├── hardware.py                # Hardware module entry point (Refactored)
│   │
│   ├── perception/                # Perception modules
│   │   ├── __init__.py
│   │   ├── camera.py              # Camera interface
│   │   └── detector.py            # Object detector
│   │
│   ├── feedback/                  # Feedback systems
│   │   ├── __init__.py
│   │   ├── haptic_legacy.py       # Legacy multi-motor haptic feedback
│   │   └── haptic_two_motor.py    # Dual-motor haptic feedback
│   │
│   ├── hardware/                  # Hardware drivers
│   │   ├── __init__.py
│   │   ├── button.py              # Button interface
│   │   ├── tts.py                 # Text-to-Speech interface
│   │   └── motors.py              # Vibration motor controller
│   │
│   └── controllers/               # Controllers
│       ├── __init__.py
│       ├── hardware_integrated.py
│       └── legacy_system.py
│
└── test/                          # Test files
    ├── test_camera.py
    ├── test_detector.py
    ├── test_haptic.py
    └── test_image_detector.py

```

---

## Module Responsibilities

### `perception/` - Perception Module

* **camera.py**: Handles camera input; compatible with Mac and Raspberry Pi.
* **detector.py**: YOLO-World object detection implementation.

### `feedback/` - Feedback Module

* **haptic_legacy.py**: 8-motor array haptic feedback system.
* **haptic_two_motor.py**: Simplified dual-motor left/right guidance system.

### `hardware/` - Hardware Driver Layer

* **button.py**: Button input control.
* **tts.py**: Text-to-Speech output.
* **motors.py**: PWM control for vibration motors.
* Supports **Simulation Mode** (Dev/Test).
* Supports **Hardware Mode** (Raspberry Pi GPIO).



---

## Import Standards

| Component | Standard Import Path |
| --- | --- |
| **Hardware Components** | `from hardware import ButtonInterface, TTSInterface, VibrationalMotorController` |
| **Perception Components** | `from perception.camera import CameraInterface` |
| **Feedback Components** | `from feedback.haptic_two_motor import TwoMotorHapticFeedback` |

---

## Advantages of the Fix

* ✅ **Clear Module Segregation**: Each subfolder has a defined responsibility.
* ✅ **DRY (Don't Repeat Yourself)**: Eliminated duplicate class definitions.
* ✅ **Ease of Maintenance**: Standardized import rules.
* ✅ **Flexibility**: Native support for switching between simulation and hardware modes.
* ✅ **Scalability**: Easy to add new hardware or perception modules.