# yolo_haptic.py
from picamera2 import Picamera2
import cv2
from ultralytics import YOLO
import time
from gpiozero import PWMOutputDevice

# --- Hardware Initialization ---
motor_left = PWMOutputDevice(22)
motor_right = PWMOutputDevice(26)

def trigger_vibration(left_strength=0.0, right_strength=0.0, duration=0.25):
    """
    Vibrate the left and right motors independently.
    :param left_strength: Duty cycle for left motor (0.0 to 1.0)
    :param right_strength: Duty cycle for right motor (0.0 to 1.0)
    :param duration: Duration of vibration in seconds
    """
    motor_left.value = left_strength
    motor_right.value = right_strength
    print(f"Vibrating L:{int(left_strength*100)}% R:{int(right_strength*100)}% for {duration}s")
    time.sleep(duration)
    motor_left.off()
    motor_right.off()

# --- YOLOv8 Model ---
model = YOLO("yolov8n.pt")

# --- Camera Setup ---
picam2 = Picamera2()
config = picam2.create_preview_configuration(main={"size": (1000, 1000)})
picam2.configure(config)
picam2.start()

print("Running YOLO. Press 'q' to stop.")

DETECT_INTERVAL = 0.25
last_detect_time = 0.0

fps_timer = time.time()
fps_count = 0

while True:
	now = time.time()
	if now - last_detect_time < DETECT_INTERVAL:
		continue
	last_detect_time = now

	frame = picam2.capture_array()
	frame = cv2.cvtColor(frame, cv2.COLOR_BGRA2BGR)

	# Run YOLOv8 detection
	results = model(frame, imgsz=160, conf=0.25, stream=True)

	# Display annotated frame
	for r in results:
		annotated_frame = r.plot()
		cv2.imshow("YOLOv8 Detection", annotated_frame)

	if cv2.waitKey(1) & 0xFF == ord('q'):
		break

	# Find object with highest confidence
	highest_conf = None
	for r in results:
		if len(r.boxes) == 0:
			continue
	for box, conf in zip(r.boxes.xyxy, r.boxes.conf):
		if highest_conf is None or conf > highest_conf[1]:
			highest_conf = (box, conf)

	# If we detected something
	if highest_conf:
		box = highest_conf[0]  # [x1, y1, x2, y2]
		x1, y1, x2, y2 = box
		x_center = (x1 + x2) / 2

		# Determine left/middle/right based on frame width
		frame_width = frame.shape[1]
		if x_center < frame_width / 3:
			trigger_vibration(left_strength=0.5, right_strength=0.0)
		elif x_center > 2 * frame_width / 3:
			trigger_vibration(left_strength=0.0, right_strength=0.5)
		else:
			trigger_vibration(left_strength=0.5, right_strength=0.5)

cv2.destroyAllWindows()
picam2.close()
motor_left.off()
motor_right.off()
print("Program terminated safely.")