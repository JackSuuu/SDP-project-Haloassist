# Quick Start Guide

## Installation

### 1. Create Virtual Environment

```bash
python3 -m venv venv

source venv/bin/activate
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

## Running on Mac (Development/Testing)

**Mac Local Demo:** Tests camera + YOLO detection (without speech workflow)

```bash
source venv/bin/activate  # Mac/Linux

python demo/demo_local.py
```

- Continuously detects objects
- Guides to closest object
- Haptic feedback simulated in console
- Press **'q'** to quit

## Running on Raspberry Pi

**Full Workflow:** Button → Speech → Detection → Haptic Guidance

1. **Connect hardware:**
   - Camera module to CSI port
   - Button to GPIO 5 (and GND)
   - Left motor to GPIO 22
   - Right motor to GPIO 26

2. **Run the demo:**
```bash
python demo/demo.py
```

**Workflow:**
1. Press button → System listens for 3 seconds
2. Say object name (e.g., "bottle", "cup", "phone")
3. Camera detects only that object
4. Motors vibrate to indicate direction (left/right/both)

**Alternative - using main.py directly:**
```bash
cd perception
python src/main.py --profile pi3 --no-display --enable-speech
```

## Command Line Options

```bash
python src/main.py --help
```

- `--model`: Path to YOLO-World model (default: yolov8s-world.pt)
- `--no-display`: Disable visual display (for production on RPi)
- `--motors`: Number of haptic motors (default: 8)

## Testing

Run unit tests:
```bash
pytest test/
```

## How It Works

**Workflow Pipeline:**

1. **Button Press** → User presses button to activate
2. **Speech-to-Text (STT)** → User says target object name (e.g., "bottle", "cup", "phone")
3. **YOLO Detection** → Camera detects ONLY that specific object
4. **Haptic Guidance** → Motors vibrate based on object direction:
   - Object on left → Left motor vibrates
   - Object on right → Right motor vibrates  
   - Object centered → Both motors vibrate
   - No object found → System keeps searching

**Technical Flow:**
1. **Camera** captures live video feed
2. **YOLO-World** detects the specified target object (open-vocabulary)
3. **Directional guidance** based on object position in frame
4. **Haptic feedback** provides directional cues:
   - 2 motors (left/right) for Pi3
   - 8 motors (circular array) for Pi5
   - Console simulation on Mac
