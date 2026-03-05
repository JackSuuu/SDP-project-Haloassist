#!/home/ubuntu/HaloAssistV2/.venv/bin/python

import cv2
import RPi.GPIO as GPIO
import stt
from config import *
from vision import VisionSystem
from motor import MotorController
from speaker import Speaker


def setup_camera():
    cap = cv2.VideoCapture(CAMERA_INDEX)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, FRAME_WIDTH)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, FRAME_HEIGHT)
    cap.set(cv2.CAP_PROP_FPS, FPS)

    if not cap.isOpened():
        raise RuntimeError("Could not open USB camera")

    return cap

def button_pressed():
        return GPIO.input(BUTTON_PIN) == 0

def main():
    GPIO.setmode(GPIO.BCM)
    GPIO.setup(BUTTON_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)

    vision = VisionSystem(
        MODEL_PATH,
        CLASSES,
        IMG_SIZE,
        CONF_THRESHOLD
    )
    motor = MotorController(
        LEFT_PIN,
        RIGHT_PIN,
        PULSE_INTERVAL,
        PULSE_DURATION
    )

    cap = setup_camera()
    spk = Speaker()
    spk.alert()
    print("Running. Hold button to change classes. ESC to exit.")

    
    try:
        while True:
            ret, frame = cap.read()
            if not ret:
                break

            # --- STT on button hold ---
            if button_pressed():
                text = stt.listen_while_button_pressed(button_pressed)

                if text:
                    # Use spoken words as new detection classes
                    new_classes = [w for w in text.split()]

                    if new_classes:
                        vision.model.set_classes(new_classes)
                        spk.speak("Classes updated: " + ", ".join(new_classes))
                    else:
                        spk.speak("I did not understand.")

            # --- Vision + motor ---
            result = vision.detect(frame)
            left, right = vision.compute_motor_strength(frame, result)

            motor.update(left, right)

            annotated = result.plot()
            cv2.imshow("YOLO Detection", annotated)

            if cv2.waitKey(1) == 27:
                break

    finally:
        cap.release()
        motor.cleanup()
        cv2.destroyAllWindows()
        GPIO.cleanup()

if __name__ == "__main__":
    main()
