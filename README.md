<div align="center">

# 🌟 HaloAssist

### AI-Powered Navigation Assistant for the Visually Impaired

[![Python](https://img.shields.io/badge/Python-3.8%2B-blue.svg)](https://www.python.org/)
[![YOLO](https://img.shields.io/badge/YOLO-World-00FFFF.svg)](https://github.com/ultralytics/ultralytics)
[![Raspberry Pi](https://img.shields.io/badge/Raspberry_Pi-5-C51A4A.svg)](https://www.raspberrypi.org/)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

**[Features](#-features)** • 
**[Quick Start](#-quick-start)** • 
**[Demo](#-demo)** • 
**[Architecture](#-system-architecture)** • 
**[Hardware](#-hardware-setup)** • 
**[Documentation](#-documentation)**

---

</div>

## 🎯 Overview

**HaloAssist** is an intelligent assistive technology system that helps visually impaired individuals navigate indoor environments through voice commands and haptic feedback. By combining state-of-the-art computer vision (YOLO-World) with intuitive haptic guidance, users can locate everyday objects hands-free.

### 💡 How It Works

1. **Press** → User presses a button to activate the system
2. **Speak** → User says the object they're looking for (e.g., "water bottle")
3. **Detect** → Real-time object detection using YOLO-World AI model
4. **Guide** → Directional vibration motors guide user toward the object

---

## ✨ Features

- 🗣️ **Voice-Activated Search** - Hands-free object search via speech-to-text
- 🤖 **Advanced AI Detection** - YOLO-World open-vocabulary object detection
- 📳 **Haptic Feedback** - Directional vibration guidance (2-8 motor array)
- 🎯 **Custom Object Classes** - Optimized for home and supermarket environments
- 🚀 **Multi-Platform Support** - Runs on Raspberry Pi (production) and Mac (development)
- ⚡ **Real-Time Performance** - Optimized inference for embedded systems
- 🔧 **Modular Architecture** - Clean separation of perception, hardware, and visualization

---

## 🚀 Quick Start

### Prerequisites

- Python 3.8+
- Camera (USB webcam or Raspberry Pi Camera Module)
- [Optional] Raspberry Pi 5 with GPIO peripherals

### Installation

```bash
# Clone the repository
git clone https://github.com/JackSuuu/SDP-project-Haloassist.git
cd SDP-project-Haloassist

# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
cd perception
pip install -r requirements.txt
```

## Run System

```bash
cd perception/src
python main.py
```

### Run Demo

**Mac/Linux Development:**
```bash
python demo/demo_local.py
```

**Raspberry Pi (Full System):**
```bash
python demo/demo.py
```

**Image-Based Testing:**
```bash
python demo/demo_image_detector.py test_images/your_image.jpg
```

Press **`q`** to quit any demo.

---

## 🎬 Demo

### Voice Command Detection
```
User: "Find my phone"
System: 🔍 Searching for phone...
        📳 Vibrating left → Object detected at 45° left
        📳 Vibrating center → Object centered, within reach!
```

### Supported Objects
- **Home:** chair, couch, bed, door, stairs, phone, laptop, book
- **Kitchen:** refrigerator, microwave, bottle, cup, bowl, knife, fork
- **Food:** apple, banana, orange, broccoli, carrot

See [PRIORITY_OBJECTS](perception/config/hardware_config.py#L108) for the full list.

---

## 🏗️ System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                      HaloAssist System                       │
└─────────────────────────────────────────────────────────────┘

    ┌──────────────┐      ┌──────────────┐      ┌──────────────┐
    │   Hardware   │      │  Perception  │      │Visualization │
    │              │      │              │      │              │
    │ • Button     │─────▶│ • Camera     │─────▶│ • Web UI     │
    │ • Speech     │      │ • YOLO Model │      │ • Debug View │
    │ • Haptics    │◀─────│ • Detector   │      │ • Metrics    │
    └──────────────┘      └──────────────┘      └──────────────┘
```

### Project Structure

```
.
├── perception/          # Core detection system
│   ├── src/            # Source code
│   │   ├── hardware/   # Button, speech, haptic interfaces
│   │   └── perception/ # Camera and detection modules
│   ├── config/         # Hardware & model configuration
│   └── test/           # Unit tests
│
├── hardware/           # Low-level GPIO drivers
│   ├── button.py       # GPIO button control
│   ├── stt.py         # Vosk speech-to-text
│   └── yolo_haptic.py # Motor control
│
├── visualization/      # Web-based monitoring
│   ├── server.py       # Flask backend
│   └── static/         # Frontend UI
│
├── demo/              # Demo scripts
│   ├── demo.py        # Full system demo (Pi)
│   ├── demo_local.py  # Mac development demo
│   └── demo_image_detector.py  # Image testing
│
├── experiments/       # Performance benchmarks
│   └── pi5-vlm-test/ # Latency tests & results
│
└── docs/             # Documentation
    ├── QUICKSTART.md
    ├── HARDWARE_INTEGRATION.md
    └── MODEL_CONFIG.md
```

---

## 🔧 Hardware Setup

### Raspberry Pi Configuration

| Component | GPIO Pin | Description |
|-----------|----------|-------------|
| Button    | GPIO 5   | Activation button (pull-up, active LOW) |
| Left Motor| GPIO 22  | Left haptic feedback |
| Right Motor| GPIO 26 | Right haptic feedback |
| Camera    | CSI Port | Pi Camera Module 3 |

### Supported Platforms

| Platform | Model | Image Size | FPS | Motors |
|----------|-------|------------|-----|--------|
| Raspberry Pi 3 | YOLO Nano | 160×160 | ~10 | 2 |
| Raspberry Pi 4 | YOLO Small | 320×320 | ~15 | 2 |
| Raspberry Pi 5 | YOLO Medium | 640×640 | ~30 | 2-8 |
| Mac/Linux Dev | YOLO World | 640×640 | 60+ | Simulated |

See [hardware_config.py](perception/config/hardware_config.py) for platform-specific profiles.

---

## 📚 Documentation

- **[Quick Start Guide](docs/QUICKSTART.md)** - Installation and first run
- **[Hardware Integration](docs/HARDWARE_INTEGRATION.md)** - GPIO setup and wiring
- **[Model Configuration](docs/MODEL_CONFIG.md)** - YOLO models and tuning
- **[Quick Reference](docs/QUICKREF.md)** - API and command reference

---

## 🧪 Testing

Run unit tests:
```bash
cd perception

# Test camera interface
python test/test_camera.py

# Test object detection
python test/test_detector.py

# Test haptic feedback
python test/test_haptic.py

# Test image-based detection
python test/test_image_detector.py
```

---

## ⚙️ Configuration

### Easy Platform Switching

```python
# In perception/config/hardware_config.py
apply_profile('pi5')  # Options: 'pi3', 'pi4', 'pi5', 'mac'
```

### Custom Object Detection

```python
# Add your own objects to detect
PRIORITY_OBJECTS = [
    'custom_object_1',
    'custom_object_2',
    # ... your objects here
]
```

### Adjust Haptic Feedback

```python
HAPTIC_CONFIG = {
    'default_strength': 0.5,    # Motor intensity (0.0 - 1.0)
    'default_duration': 0.25,   # Vibration duration (seconds)
    'detection_interval': 0.25, # Update frequency
}
```

---

## 🎓 Research & Benchmarks

Performance benchmarks and latency tests available in [`experiments/pi5-vlm-test/`](experiments/pi5-vlm-test/):
- YOLO detection latency measurements
- Model comparison (Nano vs Small vs Medium)
- Raspberry Pi 5 performance analysis

---

## 🤝 Contributing

Contributions are welcome! Areas for improvement:

- [ ] Expand object detection categories
- [ ] Multi-language speech support
- [ ] 8-motor haptic array implementation
- [ ] Mobile app companion
- [ ] Battery optimization for portable use

---

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## 👥 Team

**Senior Design Project (SDP)** - Spring 2026

---

## 🙏 Acknowledgments

- [Ultralytics YOLO](https://github.com/ultralytics/ultralytics) - Object detection framework
- [Vosk](https://alphacephei.com/vosk/) - Offline speech recognition
- [Raspberry Pi Foundation](https://www.raspberrypi.org/) - Hardware platform

---

<div align="center">

**Built with ❤️ for accessibility**

[⬆ Back to Top](#-haloassist)

</div>
