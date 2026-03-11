#!/home/ubuntu/HaloAssistV2/.venv/bin/python

from ultralytics import YOLO
import cv2
import time
from gpiozero import PWMOutputDevice

# ==================== SETTINGS ====================
PULSE_INTERVAL = 0.5     # seconds between pulses
PULSE_DURATION = 0.05    # seconds motor stays ON (0.03–0.06 recommended)
# ==================================================

# -------------------- MOTOR SETUP --------------------
motor_left = PWMOutputDevice(22)
motor_right = PWMOutputDevice(26)

last_pulse_time = 0
pulse_end_time = 0

# -------------------- LOAD MODEL --------------------
model = YOLO("yoloe-26n-seg.pt")
model.set_classes(["cone", "bottle"])

# -------------------- USB CAMERA --------------------
cap = cv2.VideoCapture(0)  # change to 1 if needed
cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
cap.set(cv2.CAP_PROP_FPS, 30)

if not cap.isOpened():
    raise RuntimeError("Could not open USB camera")

print("Running YOLO detection. Press ESC to exit.")

# -------------------- MAIN LOOP --------------------
while True:
    ret, frame = cap.read()
    if not ret:
        break

    results = model(frame, imgsz=160, conf=0.1)
    r = results[0]

    left_strength = 0.0
    right_strength = 0.0

    # ---------------- FIND BEST DETECTION ----------------
    if r.boxes is not None and len(r.boxes) > 0:
        highest_conf = None
        for box, conf in zip(r.boxes.xyxy, r.boxes.conf):
            conf = float(conf)
            if highest_conf is None or conf > highest_conf[1]:
                highest_conf = (box, conf)

        box = highest_conf[0]
        x1, y1, x2, y2 = box
        x_center = (x1 + x2) / 2
        frame_width = frame.shape[1]

        # Normalize to [-1, 1]
        offset = (x_center - frame_width / 2) / (frame_width / 2)
        offset = max(-1, min(1, offset))

        # Proportional strength
        left_strength = max(0, -offset)
        right_strength = max(0, offset)

        center_strength = 1 - abs(offset)
        left_strength += 0.6 * center_strength
        right_strength += 0.6 * center_strength

        left_strength = min(1.0, left_strength)
        right_strength = min(1.0, right_strength)

    # ---------------- PULSE TIMER ----------------
    current_time = time.time()

    # Start new pulse if detection present
    if (left_strength > 0 or right_strength > 0) and \
       current_time - last_pulse_time >= PULSE_INTERVAL:
        pulse_end_time = current_time + PULSE_DURATION
        last_pulse_time = current_time

    # Motor ON only during pulse window
    if current_time < pulse_end_time:
        motor_left.value = left_strength
        motor_right.value = right_strength
    else:
        motor_left.value = 0.0
        motor_right.value = 0.0

    # ---------------- DISPLAY ----------------
    annotated = r.plot()
    cv2.imshow("YOLO Detection", annotated)

    if cv2.waitKey(1) == 27:
        break

# ---------------- CLEANUP ----------------
cap.release()
motor_left.off()
motor_right.off()
cv2.destroyAllWindows()
