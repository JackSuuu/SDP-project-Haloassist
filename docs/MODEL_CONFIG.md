# Model and Hardware Configuration Guide

## Quick Start

### Choose Your Model

The system now supports multiple YOLO models for different hardware capabilities:

```bash
# Pi3 (tested) - Fast, lightweight
python src/main.py --model nano --no-display

# Pi4 - Balanced
python src/main.py --model small --no-display

# Pi5 (future) - Best accuracy, 8-motor support
python src/main.py --model medium --no-display

# Mac/Testing - Full YOLO-World features
python src/main.py --model world-small
```

### Platform Profiles

Use pre-configured profiles for optimal performance:

```bash
# Pi3 profile (nano model, 160px, 2 motors)
python src/main.py --profile pi3 --no-display

# Pi5 profile (medium model, 640px, 8 motors)
python src/main.py --profile pi5 --no-display

# Mac profile (for development)
python src/main.py --profile mac
```

## Configuration System

All hardware and model settings are centralized in [`config/hardware_config.py`](config/hardware_config.py).

### Available Models

| Model Name | File | Speed | Accuracy | Best For |
|------------|------|-------|----------|----------|
| `nano` | yolov8n.pt | ⚡⚡⚡ | ⭐⭐ | Pi3 |
| `small` | yolov8s.pt | ⚡⚡ | ⭐⭐⭐ | Pi4 |
| `medium` | yolov8m.pt | ⚡ | ⭐⭐⭐⭐ | Pi5 |
| `world-small` | yolov8s-world.pt | ⚡⚡ | ⭐⭐⭐ | Mac/Custom classes |
| `world-medium` | yolov8m-world.pt | ⚡ | ⭐⭐⭐⭐ | Pi5/Custom classes |

### Motor Configurations

#### 2-Motor Array (Current - Pi3/Pi4)
```
        Front
          ↑
    Left ← → Right
```

**GPIO Pins:**
- Left motor: GPIO 22
- Right motor: GPIO 26

**Directions:**
- Left third of frame: Left motor vibrates
- Right third: Right motor vibrates
- Center third: Both motors vibrate

#### 8-Motor Array (Future - Pi5)
```
          Front
        Front-Right
    Right      Left
Back-Right    Front-Left
          Back-Left
```

**GPIO Pins:**
- Front: GPIO 17
- Front-right: GPIO 18
- Right: GPIO 22
- Back-right: GPIO 23
- Back: GPIO 24
- Back-left: GPIO 25
- Left: GPIO 26
- Front-left: GPIO 27

**Directions:** 360° directional guidance based on object angle

## Upgrading to Pi5 + 8 Motors

### Step 1: Update Hardware Configuration

Edit [`config/hardware_config.py`](config/hardware_config.py):

```python
# Change the active motor configuration
MOTOR_PINS = MOTOR_PINS_8  # Was: MOTOR_PINS_2

# Change the default model
DEFAULT_MODEL = 'medium'  # Was: 'world-small'

# Adjust YOLO settings for Pi5
YOLO_CONFIG = {
    'conf_threshold': 0.25,
    'imgsz': 640,  # Was: 160 for Pi3
    'verbose': False,
}

# Adjust camera settings for Pi5
CAMERA_CONFIG = {
    'width': 1280,  # Was: 640
    'height': 720,  # Was: 480
    'fps': 30,
}
```

### Step 2: Wire 8 Motors

Connect motors to the GPIO pins as specified in `MOTOR_PINS_8`.

### Step 3: Run with Pi5 Profile

```bash
python src/main.py --profile pi5 --no-display
```

That's it! The system automatically adapts to 8-motor configuration.

## Custom Configuration

### Using Custom Model File

```bash
# Use your own YOLO model file
python src/main.py --model /path/to/custom_model.pt
```

### Modifying Detection Classes

Edit [`config/hardware_config.py`](config/hardware_config.py):

```python
PRIORITY_OBJECTS = [
    'person', 'chair', 'table',  # Add/remove objects
    'bottle', 'cup', 'phone',
    # Add your custom objects for YOLO-World
]
```

### Adjusting Motor Pins

Edit [`config/hardware_config.py`](config/hardware_config.py):

```python
# Custom 2-motor setup
MOTOR_PINS_2 = {
    'left': 17,   # Change pins as needed
    'right': 18,
}

# Custom 8-motor setup
MOTOR_PINS_8 = {
    'front': 5,
    'front_right': 6,
    # ... etc
}
```

### Tuning Haptic Feedback

Edit [`config/hardware_config.py`](config/hardware_config.py):

```python
HAPTIC_CONFIG = {
    'default_strength': 0.7,    # Increase motor intensity (0.0-1.0)
    'default_duration': 0.3,    # Longer vibration (seconds)
    'detection_interval': 0.1,  # More frequent updates
}
```

## Platform Comparison

| Feature | Pi3 | Pi4 | Pi5 |
|---------|-----|-----|-----|
| Model | yolov8n | yolov8s | yolov8m |
| Image Size | 160px | 320px | 640px |
| FPS (est.) | 10-15 | 20-25 | 30+ |
| Motors | 2 | 2 | 8 |
| Camera | 640x480 | 640x480 | 1280x720 |
| Detection Quality | ⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐⭐ |

## Examples

### Mac Development
```bash
# Use YOLO-World for testing with display
python src/main.py --model world-small
```

### Pi3 Production (Current)
```bash
# Tested configuration with nano model
python src/main.py --profile pi3 --no-display
```

### Pi5 Production (Future)
```bash
# Full 8-motor array with best model
python src/main.py --profile pi5 --no-display --enable-speech
```

### Custom Setup
```bash
# Custom model with speech
python src/main.py --model /path/to/model.pt --enable-speech
```

## Code Structure

```
perception/
├── config/
│   ├── hardware_config.py     # ⭐ Main configuration file
│   └── settings.py
├── src/
│   ├── hardware/
│   │   ├── haptic_controller.py   # Supports 2-8 motors automatically
│   │   ├── button_interface.py
│   │   └── speech_interface.py
│   ├── perception/
│   │   ├── detector.py            # Supports all YOLO models
│   │   └── camera.py
│   └── main.py                    # Model selection + profiles
└── requirements.txt
```

## Extending the System

### Adding a New Motor Array Size

1. Define pin mapping in `hardware_config.py`:
```python
MOTOR_PINS_16 = {
    'n': 17, 'nne': 18, 'ne': 22, 'ene': 23,
    'e': 24, 'ese': 25, 'se': 26, 'sse': 27,
    # ... continue pattern
}
```

2. Update `guide_to_target()` in `haptic_controller.py` to handle new configuration.

### Adding a New Model

1. Add to `YOLO_MODELS` in `hardware_config.py`:
```python
YOLO_MODELS = {
    # ... existing models
    'large': 'yolov8l.pt',
    'world-large': 'yolov8l-world.pt',
}
```

2. Use it:
```bash
python src/main.py --model large
```

### Creating a New Platform Profile

Add to `get_profile()` in `hardware_config.py`:

```python
profiles = {
    # ... existing profiles
    'jetson': {
        'model': 'medium',
        'imgsz': 640,
        'camera_width': 1920,
        'camera_height': 1080,
        'motor_pins': MOTOR_PINS_8,
    },
}
```

Use it:
```bash
python src/main.py --profile jetson
```

## Troubleshooting

### Model file not found
- Ensure model file is in the perception directory or provide full path
- Download models: `yolo export model=yolov8n.pt format=pt`

### Wrong number of motors detected
- Check `MOTOR_PINS` in `hardware_config.py`
- Verify GPIO wiring matches configuration

### Performance issues
- Use smaller `imgsz` (160, 320 instead of 640)
- Use faster model ('nano' instead of 'medium')
- Apply appropriate platform profile

## Summary

✅ **Easy model switching**: Just use `--model` flag  
✅ **Platform profiles**: Pre-configured for Pi3/Pi4/Pi5  
✅ **Extensible**: Add motors/models/platforms in config file  
✅ **No code changes needed**: All settings in `hardware_config.py`  
✅ **Future-proof**: Ready for Pi5 and 8-motor upgrade
