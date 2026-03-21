"""
Main application entry point.
Integrates target-object detection, haptic guidance, speech input, and feedback services.
"""
from typing import Optional
import argparse
import datetime
import sys
import time
from pathlib import Path

import cv2

# Ensure local modules are importable when running this file directly.
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "config"))
sys.path.insert(0, str(project_root.parent / "visualization"))
sys.path.insert(0, str(project_root.parent))

from perception.detector import detect_target_object
from perception_config import (
    COCO_CLASSES,
    CONFIDENCE_DECAY_PER_MISS,
    CONFIDENCE_SUCCESS_MARGIN,
    CONFIDENCE_THRESHOLD,
    MIN_CONFIDENCE_THRESHOLD,
    YOLOE_CONFIDENCE_DISCOUNT,
    YOLO_MODELS,
)
from run_config import RUN_CONFIG
from llm.extractor import get_extracted_object, load_extractor_model

KEY_ESCAPE = 27


class PerceptionSystem:
    def __init__(self):
        self.model_paths = YOLO_MODELS
        self.active_model_key = "yoloe-26-seg"
        self.active_model_path = self.model_paths[self.active_model_key]

        if RUN_CONFIG["enable_haptic"]:
            from hardware.haptic_controller import HapticController
        if RUN_CONFIG["enable_button"]:
            from hardware.button_interface import ButtonInterface
        if RUN_CONFIG["enable_camera"]:
            from hardware.camera_interface import CameraInterface
        if RUN_CONFIG["enable_speech"]:
            from services.stt_interface import STTInterface
        if RUN_CONFIG["enable_tts"]:
            from services.tts_interface import TTSInterface
        if RUN_CONFIG["enable_audio"]:
            from services.audio_feedback import AudioFeedback
        if RUN_CONFIG["enable_visualizer"]:
            from visualization.haptic_client import HapticVisualizer

        self.haptic = HapticController() if RUN_CONFIG["enable_haptic"] else None
        self.button = ButtonInterface() if RUN_CONFIG["enable_button"] else None
        self.stt = STTInterface() if RUN_CONFIG["enable_speech"] else None
        self.tts = TTSInterface() if RUN_CONFIG["enable_tts"] else None
        self.audio = AudioFeedback() if RUN_CONFIG["enable_audio"] else None
        self.camera = CameraInterface(width=1280, height=720) if RUN_CONFIG["enable_camera"] else None
        self.visualizer = HapticVisualizer() if RUN_CONFIG["enable_visualizer"] else None

        self.show_display = RUN_CONFIG["show_display"]
        self.target_object: Optional[str] = None
        self.is_idle = True
        self.detected_objects = []
        self.matched_target_obj = None
        self.current_conf_threshold = CONFIDENCE_THRESHOLD

        if self.visualizer:
            self.visualizer.searching(self.target_object)

        load_extractor_model()

        print("Perception System initialized")
        print(f"  YOLO model:     auto-select ({self.active_model_key})")
        print(f"  Base conf:      {CONFIDENCE_THRESHOLD:.2f}")
        print(f"  Haptic:         {'enabled' if self.haptic else 'DISABLED'}")
        print(f"  Button:         {'enabled' if self.button else 'DISABLED'}")
        print(f"  Speech (STT):   {'enabled' if self.stt and self.stt.is_available() else 'DISABLED'}")
        print(f"  TTS:            {'enabled' if self.tts and self.tts.is_available() else 'DISABLED'}")
        print(f"  Audio feedback: {'enabled' if self.audio else 'DISABLED'}")
        print(f"  Visualizer:     {'enabled' if self.visualizer else 'DISABLED'}")
        print(f"  Display:        {'enabled' if self.show_display else 'DISABLED'}")

    def _target_in_coco(self, target_object: str) -> bool:
        return target_object.lower() in COCO_CLASSES

    def _select_model_for_target(self):
        if not self.target_object:
            self.active_model_key = "yoloe-26-seg"
        else:
            self.active_model_key = "yolo26n" if self._target_in_coco(self.target_object) else "yoloe-26-seg"
        self.active_model_path = self.model_paths[self.active_model_key]

    def _get_model_adjusted_threshold(self) -> float:
        threshold = self.current_conf_threshold
        if self.active_model_key == "yoloe-26-seg":
            threshold -= YOLOE_CONFIDENCE_DISCOUNT
        return max(MIN_CONFIDENCE_THRESHOLD, threshold)

    def _on_detection_miss(self):
        self.current_conf_threshold = max(
            MIN_CONFIDENCE_THRESHOLD,
            self.current_conf_threshold - CONFIDENCE_DECAY_PER_MISS,
        )

    def _on_detection_success(self, detected_confidence: float):
        self.current_conf_threshold = max(
            MIN_CONFIDENCE_THRESHOLD,
            detected_confidence - CONFIDENCE_SUCCESS_MARGIN,
        )

    def _listen_and_set_target(self):
        if not (self.stt and self.stt.is_available()):
            return

        if self.audio:
            self.audio.button_press()

        text = self.stt.listen_while_pressed(self.button.is_pressed)
        if not text or not text.strip():
            print("No speech recognised. Keeping current target.")
            if self.tts:
                self.tts.speak("I did not hear anything.")
            if self.audio:
                self.audio.error()
            return

        extraction = get_extracted_object(text)
        valid = (
            extraction.status == "success"
            and extraction.object_of_interest.strip().lower() not in ("n/a", "large yellow pickaxe")
        )

        if valid:
            self.target_object = extraction.object_of_interest.strip().lower()
        else:
            print("LLM extraction failed; using raw speech text as fallback target.")
            self.target_object = text.strip().lower()

        self._select_model_for_target()
        self.current_conf_threshold = CONFIDENCE_THRESHOLD
        print(f"Target changed to: '{self.target_object}'")
        print(f"Using model: {self.active_model_key}")

        if self.visualizer:
            self.visualizer.searching(self.target_object)
        if self.tts:
            self.tts.speak("Looking for " + self.target_object)
        if self.audio:
            self.audio.success()

        self.is_idle = False

    def _handle_button(self):
        if not (self.button and self.button.is_pressed()):
            return

        if self.is_idle:
            print("\nButton pressed. Listening while held...")
            self._listen_and_set_target()
        else:
            self.target_object = None
            self._select_model_for_target()
            self.is_idle = True
            self.detected_objects = []
            self.matched_target_obj = None
            self.current_conf_threshold = CONFIDENCE_THRESHOLD
            print("Search stopped.")
            if self.tts:
                self.tts.speak("Search stopped")
            if self.visualizer:
                self.visualizer.stop()
            if self.audio:
                self.audio.button_release()

    def _run_detection(self, frame):
        if not self.target_object:
            self.detected_objects = []
            self.matched_target_obj = None
            return

        self._select_model_for_target()
        detection = detect_target_object(
            frame=frame,
            min_conf=self._get_model_adjusted_threshold(),
            target_obj=self.target_object,
            model_path=self.active_model_path,
        )

        if detection is None:
            self.detected_objects = []
            self.matched_target_obj = None
            self._on_detection_miss()
            return

        self._on_detection_success(detection.confidence)
        x1, y1, x2, y2 = [int(v) for v in detection.bbox]
        cx, cy = [int(v) for v in detection.center]
        self.matched_target_obj = {
            "class": self.target_object,
            "bbox": [x1, y1, x2, y2],
            "center": (cx, cy),
            "confidence": detection.confidence,
        }
        self.detected_objects = [self.matched_target_obj]

    def _update_visualizer(self, matched_target: Optional[dict], frame):
        if not self.visualizer:
            return

        if matched_target:
            offset = (matched_target["center"][0] - frame.shape[1] / 2) / (frame.shape[1] / 2)
            position = "left" if offset < -0.33 else ("right" if offset > 0.33 else "center")
            self.visualizer.update_motors(
                left=offset < 0,
                right=offset > 0,
                intensity_left=abs(offset) if offset < 0 else 0.0,
                intensity_right=abs(offset) if offset > 0 else 0.0,
                target_object=self.target_object,
                position=position,
            )
        else:
            self.visualizer.searching(self.target_object)

    def _log_status(self, matched_target):
        current_time = datetime.datetime.now()
        if not hasattr(self, "_last_log_time"):
            self._last_log_time = current_time
        if (current_time - self._last_log_time).total_seconds() < 1:
            return

        self._last_log_time = current_time
        timestamp = current_time.strftime("%Y-%m-%d %H:%M:%S")
        if matched_target:
            print(
                f"[{timestamp}] Found: {matched_target['class']} at {matched_target['center']} "
                f"(conf: {matched_target['confidence']:.2f}, min: {self._get_model_adjusted_threshold():.2f})"
            )
        elif self.target_object:
            print(
                f"[{timestamp}] Searching for '{self.target_object}' "
                f"(min: {self._get_model_adjusted_threshold():.2f})..."
            )
        else:
            print(f"[{timestamp}] Idle (no target set)")

    def _update_visual_display(self, frame, detections: list, matched_target, frame_count: int, fps_start: float) -> bool:
        if not self.show_display or frame is None:
            return True

        display = frame.copy()
        for det in detections:
            x1, y1, x2, y2 = det["bbox"]
            is_target = det == matched_target
            color = (0, 255, 0) if is_target else (255, 0, 0)
            thickness = 3 if is_target else 1

            cv2.rectangle(display, (x1, y1), (x2, y2), color, thickness)
            cv2.putText(
                display,
                f"{det['class']} {det['confidence']:.2f}",
                (x1, y1 - 10),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.5,
                color,
                2,
            )

            if is_target:
                cx, cy = det["center"]
                cv2.circle(display, (cx, cy), 8, (0, 0, 255), -1)
                cv2.putText(display, "TARGET", (cx - 30, cy - 15), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 2)

        if RUN_CONFIG["fps_display"]:
            fps = frame_count / max(1e-6, (time.time() - fps_start))
            cv2.putText(display, f"FPS: {fps:.1f}", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)

        cv2.imshow("Perception System", display)
        return cv2.waitKey(1) & 0xFF != KEY_ESCAPE

    def _cleanup(self):
        print("Cleaning up...")
        if self.audio:
            self.audio.shutdown()
        if self.camera:
            self.camera.stop()
        if self.haptic:
            self.haptic.cleanup()
        if self.button:
            self.button.cleanup()
        if self.tts:
            self.tts.cleanup()
        if self.visualizer:
            self.visualizer.stop()
        if self.show_display:
            cv2.destroyAllWindows()
        print("System stopped.")

    def run(self):
        print("\nStarting perception system...")
        if self.camera and not self.camera.start():
            print("Failed to start camera. Continuing without camera.")
            self.camera = None

        if self.audio:
            self.audio.bootup()

        frame_count = 0
        fps_start = time.time()

        try:
            while True:
                self._handle_button()
                camera_frame = self.camera.read_frame() if self.camera else None

                if self.camera and camera_frame is None:
                    print("Warning: failed to read frame from camera")
                    continue

                self._run_detection(camera_frame)
                if self.haptic:
                    self.haptic.calc_motor_strengths(
                        self.matched_target_obj["center"] if self.matched_target_obj else None,
                        (camera_frame.shape[1] // 2, camera_frame.shape[0] // 2),
                        camera_frame.shape[1],
                    )
                    self.haptic.update_motors()

                self._update_visualizer(self.matched_target_obj, camera_frame)

                frame_count += 1
                self._log_status(self.matched_target_obj)
                if not self._update_visual_display(camera_frame, self.detected_objects, 
                                                   self.matched_target_obj, frame_count, fps_start):
                    break

        except KeyboardInterrupt:
            print("\nKeyboard interrupt received. Stopping...")
        finally:
            self._cleanup()
            time.sleep(1)

def main():
    parser = argparse.ArgumentParser(description="HaloAssist Perception System")
    parser.add_argument("--disable-haptics", action="store_true", help="Disable haptic feedback")
    parser.add_argument("--disable-speech", action="store_true", help="Disable speech input")
    parser.add_argument("--disable-tts", action="store_true", help="Disable text-to-speech output")
    parser.add_argument("--disable-audio", action="store_true", help="Disable audio feedback")
    parser.add_argument("--disable-visualizer", action="store_true", help="Disable visualizer")
    args = parser.parse_args()

    if args.disable_haptics:
        RUN_CONFIG["enable_haptic"] = False
    if args.disable_speech:
        RUN_CONFIG["enable_speech"] = False
    if args.disable_tts:
        RUN_CONFIG["enable_tts"] = False
    if args.disable_audio:
        RUN_CONFIG["enable_audio"] = False
    if args.disable_visualizer:
        RUN_CONFIG["enable_visualizer"] = False

    PerceptionSystem().run()


if __name__ == "__main__":
    main()
