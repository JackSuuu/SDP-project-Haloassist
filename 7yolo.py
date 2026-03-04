import time
import cv2
from ultralytics import YOLO

import busio
import board
from adafruit_tca9548a import TCA9548A
import adafruit_drv2605
from picamera2 import Picamera2

# -------------------- I2C + HAPTIC SETUP --------------------
i2c = busio.I2C(board.SCL, board.SDA)
mux = TCA9548A(i2c)

drv_left = adafruit_drv2605.DRV2605(mux[6])
drv_right = adafruit_drv2605.DRV2605(mux[7])

drv_left.use_ERM()
drv_right.use_ERM()

drv_left.mode = adafruit_drv2605.MODE_INTTRIG
drv_right.mode = adafruit_drv2605.MODE_INTTRIG

# -------------------- TUNING --------------------
DEAD_ZONE = 0.12          # center region where no vibration
MIN_INTERVAL = 0.45       # fastest pulse
MAX_INTERVAL = 0.55        # slowest pulse
PULSE_DURATION = 0.05

last_pulse_time = 0
pulse_end_time = 0
active_side = None  # "left" or "right"

# -------------------- LOAD YOLO --------------------
model = YOLO("yoloe-26n-seg.pt")
model.set_classes(["cone", "bottle"])

# -------------------- PICAMERA2 --------------------
picam2 = Picamera2()
config = picam2.create_preview_configuration(
    main={"size": (640, 480), "format": "RGB888"}
)
picam2.configure(config)
picam2.start()

print("Running YOLO detection. Press ESC to exit.")

# -------------------- MAIN LOOP --------------------
while True:
    frame = picam2.capture_array()
    results = model(frame, imgsz=160, conf=0.2)
    r = results[0]

    side = None
    strength = 0.0

    # ---------------- FIND BEST DETECTION ----------------
    if r.boxes is not None and len(r.boxes) > 0:
        best = max(zip(r.boxes.xyxy, r.boxes.conf), key=lambda x: float(x[1]))
        box = best[0]

        x1, y1, x2, y2 = box
        x_center = (x1 + x2) / 2
        frame_width = frame.shape[1]

        offset = (x_center - frame_width / 2) / (frame_width / 2)
        offset = max(-1, min(1, offset))

        if abs(offset) > DEAD_ZONE:
            strength = abs(offset)

            if offset < 0:
                side = "left"
            else:
                side = "right"

    # ---------------- PULSE LOGIC ----------------
    current_time = time.time()

    if side is not None:
        # Stronger offset = faster pulses
        interval = MAX_INTERVAL - strength * (MAX_INTERVAL - MIN_INTERVAL)

        if current_time - last_pulse_time >= interval:
            pulse_end_time = current_time + PULSE_DURATION
            last_pulse_time = current_time
            active_side = side

    # ---------------- DRIVE MOTORS ----------------
    if current_time < pulse_end_time:
        if active_side == "left":
            drv_right.stop()
            drv_left.sequence[0] = adafruit_drv2605.Effect(47)
            drv_left.play()

        elif active_side == "right":
            drv_left.stop()
            drv_right.sequence[0] = adafruit_drv2605.Effect(47)
            drv_right.play()
    else:
        drv_left.stop()
        drv_right.stop()

    # ---------------- DISPLAY ----------------
    annotated = r.plot()
    cv2.imshow("YOLO Detection", annotated)

    if cv2.waitKey(1) == 27:
        break

# ---------------- CLEANUP ----------------
picam2.stop()
drv_left.stop()
drv_right.stop()
cv2.destroyAllWindows()
