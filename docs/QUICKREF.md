# Quick Reference - Perception System

## Current Setup (Pi3)

```bash
cd perception
python src/main.py --profile pi3 --no-display
```

**Model:** yolov8n.pt (tested ✅)  
**Motors:** 2 (left/right on GPIO 22, 26)  
**Camera:** 640x480 via picamera2

## Command Options

### Model Selection
```bash
# Use predefined model
--model nano          # yolov8n.pt (current/Pi3)
--model small         # yolov8s.pt
--model medium        # yolov8m.pt (Pi5)
--model world-small   # yolov8s-world.pt (Mac)

# Use custom model file
--model /path/to/custom.pt
```

### Platform Profiles
```bash
--profile pi3    # Optimized for Pi3 (current)
--profile pi4    # Optimized for Pi4
--profile pi5    # Optimized for Pi5 (future)
--profile mac    # Mac development
```

### Display & Input
```bash
--no-display       # Headless mode (for Pi)
--enable-speech    # Enable voice input via button
```

## Common Usage Patterns

### Mac Development
```bash
python src/main.py
# or
python src/main.py --model world-small
```

### Pi3 Production (Current)
```bash
python src/main.py --profile pi3 --no-display
```

### Pi3 with Speech
```bash
python src/main.py --profile pi3 --no-display --enable-speech
```

### Pi5 Future (8 Motors)
```bash
# After wiring 8 motors and editing config
python src/main.py --profile pi5 --no-display
```

## Configuration Files

### Main Config
[`config/hardware_config.py`](config/hardware_config.py)
- YOLO models
- Motor GPIO pins
- Camera settings
- Detection classes

### Quick Changes

#### Change Model (Pi3)
```python
# config/hardware_config.py
DEFAULT_MODEL = 'nano'  # Current: yolov8n.pt
```

#### Upgrade to 8 Motors
```python
# config/hardware_config.py
MOTOR_PINS = MOTOR_PINS_8  # Change from MOTOR_PINS_2
```

#### Adjust Motor Strength
```python
# config/hardware_config.py
HAPTIC_CONFIG = {
    'default_strength': 0.7,  # 0.0 - 1.0
    'default_duration': 0.3,  # seconds
}
```

## Hardware Setup

### Current (Pi3)
- **Button:** GPIO 5 → GND
- **Left Motor:** GPIO 22 → Driver → Motor
- **Right Motor:** GPIO 26 → Driver → Motor
- **Camera:** Raspberry Pi Camera Module

### Future (Pi5 - 8 Motors)
Additional motors on GPIO: 17, 18, 23, 24, 25, 27

## Testing

### Check if hardware works
```bash
# Button
python -c "from hardware.button_interface import ButtonInterface; b = ButtonInterface(); print('Button:', b._is_pi)"

# Motors
python -c "from hardware.haptic_controller import HapticController; h = HapticController(); h.trigger_vibration({'left': 0.5})"

# Camera
python -c "from perception.camera import CameraInterface; c = CameraInterface(); print('Camera started:', c.start()); c.stop()"
```

## Troubleshooting

### Model not found
```bash
# Download model
cd perception
wget https://github.com/ultralytics/assets/releases/download/v8.1.0/yolov8n.pt
```

### Motors not working
- Check wiring (GPIO 22, 26)
- Verify gpiozero installed: `pip install gpiozero`
- Test with `python -c "from gpiozero import PWMOutputDevice; m = PWMOutputDevice(22); m.value = 0.5; import time; time.sleep(1); m.off()"`

### Camera not working
- Pi: `sudo apt install python3-picamera2`
- Check camera enabled: `vcgencmd get_camera`

### Import errors
```bash
cd perception
pip install -r requirements.txt
```

## File Structure
```
perception/
├── config/hardware_config.py    ⭐ Main config
├── src/
│   ├── main.py                  ⭐ Run this
│   ├── hardware/                # Hardware interfaces
│   └── perception/              # Detection & camera
├── MODEL_CONFIG.md              📖 Detailed guide
└── requirements.txt             📦 Dependencies
```