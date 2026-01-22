# Perception Framework for Blind Assistance

An object detection framework designed to assist blind individuals in navigating home and supermarket environments using **YOLO-World** open-vocabulary detection and haptic feedback.

## Features
- Real-time object detection using **YOLO-World** (open-vocabulary)
- Custom object classes for home/supermarket scenarios
- Hand guidance towards detected objects
- Vibration motor array feedback (6-8 motors)
- Optimized for Raspberry Pi 5 / Linux
- Mac camera support for development/testing

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
│   Camera    │ ──┐
└─────────────┘   │
                  ├──> ┌──────────────┐      ┌─────────────────────┐
┌─────────────┐   │    │ Main System  │ ──>  │  YOLO-World     │
│  Mac / RPi  │ ──┘    │  (main.py)   │      │ Object Detector │
└─────────────┘        └──────────────┘      └─────────────────┘
                              │                       │
                              │                       ↓
                              │              ┌─────────────────┐
                              │              │ Target Selector │
                              │              │ (Priority Logic)│
                              │              └─────────────────┘
                              │                       │
                              ↓                       ↓
                       ┌─────────────────────────────────┐
                       │   Haptic Feedback Controller    │
                       │   (8 Vibration Motors)          │
                       └─────────────────────────────────┘
                                      │
                                      ↓
                              [Directional Guidance]
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
