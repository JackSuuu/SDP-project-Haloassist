# Quick Start Guide

## Installation

### 1. Create Virtual Environment (推荐)

**创建虚拟环境：**
```bash
python3 -m venv venv
```

**激活虚拟环境：**

在 Mac/Linux 上：
```bash
source venv/bin/activate
```

在 Windows 上：
```bash
venv\Scripts\activate
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

**注意：** 首次运行时会自动下载 YOLO-World 模型 (~40MB)

## Running on Mac (Development/Testing)

**确保虚拟环境已激活：**
```bash
source venv/bin/activate  # Mac/Linux
# 或 venv\Scripts\activate  # Windows
```

**运行演示：**
```bash
python demo.py
```

**或直接运行：**
```bash
python src/main.py
```

按 **'q'** 退出。

## Running on Raspberry Pi

1. **Connect hardware:**
   - Camera module to CSI port
   - Vibration motors to GPIO pins (see config/settings.py)

2. **Run:**
```bash
python src/main.py --motors 8
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

1. **Camera** captures live video feed
2. **YOLO-World** detects objects in each frame (open-vocabulary detection)
3. **Priority system** selects most relevant object (closest + prioritized classes)
4. **Haptic feedback** guides user's hand towards target:
   - 8 motors arranged in circle provide directional cues
   - Vibration intensity/duration indicates distance
   - Console output shows direction arrows in simulation mode

## Why YOLO-World?

YOLO-World 是一个开放词汇（open-vocabulary）检测模型：
- 可以检测自定义类别，无需重新训练
- 更适合家庭/超市场景的多样化物品
- 支持中文类别名称
- 性能优于传统 YOLO 在特定场景的表现

## Hardware Setup (Raspberry Pi)

### GPIO Pin Configuration
Default pins (BCM numbering):
- Motor 0 (→): GPIO 17
- Motor 1 (↗): GPIO 18
- Motor 2 (↑): GPIO 27
- Motor 3 (↖): GPIO 22
- Motor 4 (←): GPIO 23
- Motor 5 (↙): GPIO 24
- Motor 6 (↓): GPIO 25
- Motor 7 (↘): GPIO 4

Modify in `config/settings.py` as needed.

## Troubleshooting

**Camera not found:**
- Check camera permissions (Mac: System Preferences > Security & Privacy > Camera)
- Try different camera ID: `--camera-id 1`

**YOLO-World model download fails:**
- Check internet connection
- Download manually: `yolo predict model=yolov8s-world.pt source='path/to/image.jpg'`
- Or download from [Ultralytics](https://github.com/ultralytics/ultralytics)

**GPIO errors on RPi:**
- Ensure `RPi.GPIO` is installed: `pip install RPi.GPIO`
- Run with sudo if needed: `sudo python src/main.py`
