# Perception Framework for Blind Assistance

An object detection framework designed to assist blind individuals in navigating home and supermarket environments using **YOLO-World** open-vocabulary detection and haptic feedback.

## Features
- **Speech-to-Text object selection** - User specifies target object via voice
- Real-time object detection using **YOLO-World** (open-vocabulary)
- **Directional haptic guidance** - Vibration indicates where object is located
- Custom object classes for home/supermarket scenarios

---

- Vibration motor array feedback (2 motors for Pi3, 8 motors for Pi5)
- Optimized for Raspberry Pi 5 / Linux
- Mac camera support for development/testing

## Workflow

1. 🔘 **Button Press** - User presses button to start
2. 🎤 **Speech Input** - User says object name ("bottle", "cup", "phone", etc.)
3. 📹 **Detection** - Camera searches for that specific object using YOLO
4. 📳 **Haptic Guidance** - Motors vibrate to indicate direction:
   - **Left**: Object on left side
   - **Right**: Object on right side
   - **Both**: Object centered
5. 🔄 **Continuous** - System keeps detecting and guiding until object found

## Project Structure
```
perception/
├── src/           # Source code
├── test/          # Test files
├── config/        # Configuration files
├── models/        # YOLO model weights
└── requirements.txt
```

## Hardware Requirements
- Raspberry Pi 5 (or Mac for development/testing)
- Camera module
- 6-8 vibration motors
- Motor driver board

## Setup
```bash
# 创建虚拟环境
python3 -m venv venv
source venv/bin/activate  # Mac/Linux
# venv\Scripts\activate  # Windows

# 安装依赖
pip install -r requirements.txt
```

## Quick Start

**Mac (Testing):**
```bash
python demo.py
```

**Raspberry Pi (Production):**
```bash
python src/main.py --no-display
```

See [QUICKSTART.md](QUICKSTART.md) for detailed instructions.

## System Architecture

```
                    ┌─────────────┐
                    │   Button    │ ──> User presses button
                    └─────────────┘
                           │
                           ↓
                    ┌─────────────┐
                    │  Speech-to- │ ──> User says "bottle"
                    │    Text     │
                    └─────────────┘
                           │
                           ↓
┌─────────────┐    ┌─────────────────────┐
│   Camera    │──> │  YOLO-World Model   │ ──> Detects "bottle" only
└─────────────┘    │ (Target: bottle)    │
                   └─────────────────────┘
                           │
                           ↓
                   ┌─────────────────┐
                   │ Object Located? │
                   └─────────────────┘
                     │            │
                    Yes          No
                     │            │
                     ↓            ↓
              ┌──────────┐   Keep searching
              │ Position │
              │ Analysis │
              └──────────┘
                     │
                     ↓
         ┌──────────────────────┐
         │ Haptic Controller    │
         │ - Left motor (L)     │
         │ - Right motor (R)    │
         └──────────────────────┘
                     │
                     ↓
         [Directional Guidance]
         L: Left object
         R: Right object
         L+R: Center object
```

## Core Modules

- **detector.py**: YOLO-World based object detection with custom classes
- **haptic.py**: Vibration motor control for directional guidance  
- **camera.py**: Cross-platform camera interface (Mac/RPi)
- **main.py**: Main integration and control loop

## Why YOLO-World?

- **Open-vocabulary detection**: Detect custom object categories without retraining
- **Flexible**: Easily add new object classes for different scenarios
- **Accurate**: Better performance for specific home/supermarket items
- **Efficient**: Real-time performance on Raspberry Pi 5
