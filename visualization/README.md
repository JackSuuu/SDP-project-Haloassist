# Motor Vibration Visualizer

A modern web-based visualization for the haptic feedback system. Shows real-time motor status with a stylized head and two vibrating motors on each side.

## Features

- 🎨 Modern dark theme with neon glow effects
- ⚡ Real-time updates via WebSocket
- 📳 Animated vibration effects when motors are active
- 🎯 Shows target object and position
- 📊 Intensity bars for each motor
- 🧪 Test buttons for manual testing

## Quick Start

```bash
# Install dependencies
pip install -r requirements.txt

# Run the server
python server.py
```

Open http://localhost:8000 in your browser.

## API Endpoints

### Update Motor State
```bash
POST /api/motor/update
Content-Type: application/json

{
    "left": true,
    "right": false,
    "intensity_left": 0.8,
    "intensity_right": 0.0,
    "target_object": "bottle",
    "position": "left"
}
```

### Detection Update (Auto-triggers motors)
```bash
POST /api/detection
Content-Type: application/json

{
    "target_object": "cup",
    "position": "right",
    "confidence": 0.85
}
```

### Quick Motor Controls
```bash
# Toggle left motor
POST /api/motor/left/true
POST /api/motor/left/false

# Toggle right motor
POST /api/motor/right/true
POST /api/motor/right/false

# Toggle both motors (center)
POST /api/motor/both/true
POST /api/motor/both/false

# Stop all motors
POST /api/motor/stop

# Get current state
GET /api/motor/state
```

### WebSocket
Connect to `/ws` for real-time motor state updates.

## Integration with Perception System

Add this to your haptic controller to send updates to the visualization:

```python
import requests

VISUALIZER_URL = "http://localhost:8000"

def send_haptic_update(left: bool, right: bool, target: str, position: str):
    """Send motor update to visualizer"""
    try:
        requests.post(f"{VISUALIZER_URL}/api/motor/update", json={
            "left": left,
            "right": right,
            "target_object": target,
            "position": position
        }, timeout=0.1)
    except:
        pass  # Don't block on visualizer errors
```

## Architecture

```
┌─────────────────────┐       WebSocket       ┌──────────────────┐
│  Perception System  │ ──────────────────────▶│   Web Browser    │
│                     │                        │                  │
│  - Object Detection │       POST /api/...    │  - Real-time UI  │
│  - Haptic Control   │ ──────────────────────▶│  - Animations    │
│  - Speech Input     │                        │  - Motor Status  │
└─────────────────────┘                        └──────────────────┘
                              │
                              ▼
                    ┌──────────────────┐
                    │   FastAPI Server │
                    │                  │
                    │  - REST API      │
                    │  - WebSocket     │
                    │  - State Mgmt    │
                    └──────────────────┘
```
