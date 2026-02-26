# vision.py

from ultralytics import YOLO
import cv2


class VisionSystem:
    def __init__(self, model_path, classes, img_size, conf_threshold):
        self.model = YOLO(model_path)
        self.model.set_classes(classes)

        self.img_size = img_size
        self.conf_threshold = conf_threshold

    def detect(self, frame):
        results = self.model(frame, imgsz=self.img_size, conf=self.conf_threshold)
        return results[0]

    @staticmethod
    def compute_motor_strength(frame, result):
        left_strength = 0.0
        right_strength = 0.0

        if result.boxes is None or len(result.boxes) == 0:
            return left_strength, right_strength

        highest_conf = None
        for box, conf in zip(result.boxes.xyxy, result.boxes.conf):
            conf = float(conf)
            if highest_conf is None or conf > highest_conf[1]:
                highest_conf = (box, conf)

        box = highest_conf[0]
        x1, y1, x2, y2 = box
        x_center = (x1 + x2) / 2
        frame_width = frame.shape[1]

        offset = (x_center - frame_width / 2) / (frame_width / 2)
        offset = max(-1, min(1, offset))

        left_strength = max(0, -offset)
        right_strength = max(0, offset)

        center_strength = 1 - abs(offset)
        left_strength += 0.6 * center_strength
        right_strength += 0.6 * center_strength

        return min(1.0, left_strength), min(1.0, right_strength)
