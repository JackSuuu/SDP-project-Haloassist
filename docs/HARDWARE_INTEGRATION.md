# Hardware Integration Guide

## Overview

The perception system has been refactored to cleanly integrate with the hardware modules from the `hardware/` directory. All hardware-specific functionality is now properly abstracted through clean interfaces.

## Architecture

```
perception/src/
├── hardware/              # Hardware interface modules (NEW)
│   ├── __init__.py       # Exports ButtonInterface, SpeechInterface, HapticController
│   ├── button_interface.py
│   ├── speech_interface.py
│   └── haptic_controller.py
├── perception/
│   ├── camera.py         # Camera interface (Mac + Pi support)
│   ├── detector.py       # YOLO-World object detection
│   └── __init__.py
└── main.py              # Main application

hardware/                 # Original Pi hardware modules
├── button.py            # GPIO button control (used as reference)
├── stt.py              # Vosk speech-to-text (imported by speech_interface)
└── yolo_haptic.py      # Motor control logic (used as reference)
```

## Hardware Modules

### 1. ButtonInterface (`hardware/button_interface.py`)
- Handles GPIO button input
- Auto-detects Raspberry Pi
- Falls back to disabled mode on non-Pi systems
- **GPIO Pin:** 5 (BCM mode, active LOW)

### 2. SpeechInterface (`hardware/speech_interface.py`)
- Wraps Vosk speech-to-text functionality
- Uses `hardware/stt.py` module
- Returns recognized text from voice input
- **Model path:** `/home/pi/vosk-model/vosk-model-small-en-us-0.15`

### 3. HapticController (`hardware/haptic_controller.py`)
- Controls 2 vibration motors (left/right)
- Provides directional guidance based on object position
- Uses PWM for motor intensity control
- **GPIO Pins:** 22 (left), 26 (right)

### 4. CameraInterface (`perception/camera.py`)
- Supports both Mac (OpenCV) and Pi (picamera2)
- Auto-detects platform and uses appropriate camera backend
- Graceful fallback to OpenCV if picamera2 unavailable

## Usage

### Basic Usage (Mac - Testing)
```bash
cd perception
python src/main.py
```

### Raspberry Pi (Production)
```bash
cd perception
python src/main.py --no-display --enable-speech
```

### Command-line Options
- `--model MODEL_PATH`: Path to YOLO-World model (default: yolov8s-world.pt)
- `--no-display`: Disable visual display (for headless Pi)
- `--enable-speech`: Enable speech input via button press

## Hardware Setup on Raspberry Pi

### GPIO Pin Configuration
| Component | GPIO Pin (BCM) | Description |
|-----------|----------------|-------------|
| Button | 5 | Input, pull-up, active LOW |
| Left Motor | 22 | PWM output |
| Right Motor | 26 | PWM output |

### Wiring Diagram
```
Button:     GPIO 5 ----[Button]---- GND

Motors:     GPIO 22 ----[Driver]----[Left Motor]
            GPIO 26 ----[Driver]----[Right Motor]
```

## Dependencies

### Core Dependencies (requirements.txt)
```
ultralytics
opencv-python
numpy
```

### Raspberry Pi Only
```
RPi.GPIO          # For button input
gpiozero          # For motor control
picamera2         # For camera
sounddevice       # For audio capture
vosk              # For speech recognition
```

## Platform Detection

All hardware modules include automatic platform detection:

```python
def _check_raspberry_pi(self) -> bool:
    """Check if running on Raspberry Pi"""
    try:
        with open('/proc/device-tree/model', 'r') as f:
            model = f.read()
            return 'raspberry pi' in model.lower()
    except:
        return False
```

- **On Raspberry Pi:** Full hardware functionality enabled
- **On Mac/Other:** Simulated/disabled mode for testing

## Code Quality Features

### Clean Abstractions
- All hardware access is through well-defined interfaces
- No direct GPIO/hardware calls in main application code
- Easy to mock for testing

### Error Handling
- Graceful degradation when hardware unavailable
- Clear error messages and warnings
- No crashes on missing hardware

### Cross-Platform Support
- Single codebase works on Mac (development) and Pi (production)
- Automatic platform detection
- Appropriate backend selection

## Integration Flow

```
main.py
  ├─> ObjectDetector (YOLO-World)
  │     └─> detect objects
  │
  ├─> CameraInterface
  │     ├─> [Mac] OpenCV
  │     └─> [Pi] picamera2
  │
  ├─> HapticController
  │     └─> guide_to_target() ──> vibration motors
  │
  ├─> ButtonInterface
  │     └─> is_pressed() ──> GPIO button
  │
  └─> SpeechInterface
        └─> listen() ──> hardware/stt.py ──> Vosk
```

## Future Enhancements

1. **Dynamic Class Selection**: Use speech input to change detection classes on-the-fly
2. **Multi-motor Arrays**: Expand from 2 to 6-8 motors for finer directional guidance
3. **Audio Feedback**: Add TTS for object announcements
4. **Configuration File**: Move GPIO pins and settings to config file

## Troubleshooting

### Button not responding
- Check GPIO wiring (pin 5 to button, button to GND)
- Verify pull-up resistor configuration
- Check `/proc/device-tree/model` for Pi detection

### Motors not vibrating
- Verify GPIO pins 22 and 26 are connected
- Check motor driver power supply
- Test with manual GPIO control

### Camera not working
- **Pi:** Install picamera2: `sudo apt install python3-picamera2`
- **Mac:** Ensure camera permissions granted
- Check camera device index (default: 0)

### Speech recognition issues
- Verify Vosk model at `/home/pi/vosk-model/vosk-model-small-en-us-0.15`
- Check microphone connection
- Test with button press

## Testing Without Hardware

The system gracefully handles missing hardware:

```bash
# On Mac - everything simulated
python src/main.py

# Output shows:
# - Haptic feedback: simulated
# - Button input: disabled  
# - Speech input: disabled
```

## Contributing

When adding new hardware modules:
1. Create interface in `perception/src/hardware/`
2. Include platform detection
3. Implement graceful fallback
4. Add to `hardware/__init__.py`
5. Update this documentation
