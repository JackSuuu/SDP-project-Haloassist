"""
Main application entry point
Integrates detection, guidance, and haptic feedback with hardware components.
Supports flexible configuration for different platforms (Pi3/Pi4/Pi5).

Latency improvements (from 1-integration branch):
  - Non-blocking haptic pulses (no time.sleep in motor code)
  - Button-held STT (record only while held, no fixed 3 s wait)
  - Piper neural TTS feedback via TTSInterface class

Run modes (set flags in perception/config/run_config.py):
  - Full system:    all flags True
  - YOLO only:      enable_haptic=False, enable_speech=False, enable_tts=False, enable_button=False
  - No haptic:      enable_haptic=False
  - Headless:       show_display=False
"""
from typing import Optional
import cv2
import time
import argparse
import sys
from pathlib import Path

# Add config directory to path
config_dir = Path(__file__).parent.parent / 'config'
sys.path.insert(0, str(config_dir))

from perception.detector import ObjectDetector
from perception_config import YOLO_MODELS, DEFAULT_MODEL, apply_profile
from run_config import RUN_CONFIG
from llm.extractor import get_extracted_object, ObjectExtraction, load_extractor_model

if RUN_CONFIG['enable_haptic']:
    from hardware.haptic_controller import HapticController
if RUN_CONFIG['enable_button']:
    from hardware.button_interface import ButtonInterface
if RUN_CONFIG['enable_camera']:
    from hardware.camera_interface import CameraInterface
if RUN_CONFIG['enable_speech']:
    from services.stt_interface import STTInterface
if RUN_CONFIG['enable_tts']:
    from services.tts_interface import TTSInterface
if RUN_CONFIG['enable_audio']:
    from services.audio_feedback import AudioFeedback


class PerceptionSystem:
    def __init__(self, model_name: Optional[str] = None,
                 model_path: Optional[str] = None):
        """
        Initialize perception system.
        Components are created only if their flag is set in run_config.py.

        Args:
            model_name: Model name from perception_config ('nano', 'small', etc.)
            model_path: Direct path to model file (overrides model_name)
        """
        if model_path is None:
            model_name = model_name or DEFAULT_MODEL
            model_path = YOLO_MODELS.get(model_name, YOLO_MODELS[DEFAULT_MODEL])

        self.detector = ObjectDetector(model_path=model_path)
        self.haptic  = HapticController()  if RUN_CONFIG['enable_haptic']  else None
        self.button  = ButtonInterface()   if RUN_CONFIG['enable_button']  else None
        self.stt     = STTInterface()      if RUN_CONFIG['enable_speech']  else None
        self.tts     = TTSInterface()      if RUN_CONFIG['enable_tts']     else None
        self.audio   = AudioFeedback()     if RUN_CONFIG['enable_audio']   else None
        self.camera  = CameraInterface(width=1280, height=720) if RUN_CONFIG['enable_camera'] else None

        self.show_display = RUN_CONFIG['show_display']
        self.target_object = "cup"
        self.is_yolo_world = 'world' in str(model_path).lower() or 'yoloe' in str(model_path).lower()
        self.currentlyIdle = True

        if self.haptic:
            self.haptic.set_target(self.target_object)

        load_extractor_model()

        print("Perception System initialized")
        print(f"  YOLO model:     {model_path}")
        print(f"  Haptic:         {'enabled' if self.haptic else 'DISABLED'}")
        print(f"  Button:         {'enabled' if self.button else 'DISABLED'}")
        print(f"  Speech (STT):   {'enabled' if self.stt and self.stt.is_available() else 'DISABLED'}")
        print(f"  TTS:            {'enabled' if self.tts and self.tts.is_available() else 'DISABLED'}")
        print(f"  Audio feedback: {'enabled' if self.audio else 'DISABLED'}")
        print(f"  Display:        {'enabled' if self.show_display else 'DISABLED'}")

    def draw_detections(self, frame, detections, target_detection):
        """Draw detection boxes and guidance on frame."""
        for det in detections:
            x1, y1, x2, y2 = det['bbox']
            color = (0, 255, 0) if det == target_detection else (255, 0, 0)
            thickness = 3 if det == target_detection else 1

            cv2.rectangle(frame, (x1, y1), (x2, y2), color, thickness)

            label = f"{det['class']} {det['confidence']:.2f}"
            cv2.putText(frame, label, (x1, y1 - 10),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)

            if det == target_detection:
                cx, cy = det['center']
                cv2.circle(frame, (cx, cy), 8, (0, 0, 255), -1)
                cv2.putText(frame, "TARGET", (cx - 30, cy - 15),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 2)

        return frame

    def run(self):
        """Main processing loop."""
        print("\nStarting perception system...")
        print("Press 'q' to quit\n")

        if self.camera:
            print("Initializing camera...")
            if not self.camera.start():
                print("❌ Failed to start camera")
                return
            print("✅ Camera started")

        if self.audio:
            self.audio.alert()

        try:
            frame_count = 0
            fps_start = time.time()
            detections = []
            target = None

            while True:
                # --- Frame acquisition ---
                if self.camera:
                    frame = self.camera.read_frame()
                    if frame is None:
                        print("⚠️  Warning: None frame from camera")
                        continue
                else:
                    break

                frame_count += 1

                # --- Button / STT ---
                if self.button and self.button.is_pressed():
                    if self.currentlyIdle:
                        print("\n🔘 Button pressed! Listening while held...")
                        if self.stt and self.stt.is_available():
                            text = self.stt.listen_while_pressed(self.button.is_pressed)
                            if text and text.strip():
                                object_extraction = get_extracted_object(text)
                                if (object_extraction.status == "success"
                                        and object_extraction.object_of_interest.strip().lower() != "n/a"
                                        and object_extraction.object_of_interest.strip() != "large yellow pickaxe"):
                                    self.target_object = object_extraction.object_of_interest.lower()
                                    print(f"✅ Target changed to: '{self.target_object}'")
                                    if self.haptic:
                                        self.haptic.set_target(self.target_object)
                                    if self.is_yolo_world:
                                        try:
                                            self.detector.model.set_classes([self.target_object])
                                        except Exception as e:
                                            print(f"⚠️  Could not update YOLO classes: {e}")
                                    self.currentlyIdle = False
                                    if self.tts:
                                        self.tts.speak("Looking for " + self.target_object)
                                else:
                                    if self.tts:
                                        self.tts.speak("I did not understand.")
                                    print("❌ LLM failed to extract a valid object.")
                            else:
                                print("❌ No speech recognised. Keeping current target.")
                                if self.audio:
                                    self.audio.error()
                    else:
                        self.target_object = None
                        self.currentlyIdle = True
                        print("⏸️  Search stopped.")
                        if self.tts:
                            self.tts.speak("Search stopped")

                # --- Detection ---
                if self.target_object:
                    detections = self.detector.detect(frame)
                    target = None
                    for det in detections:
                        if self.target_object in det['class'].lower():
                            target = det
                            break

                    if target is not None:
                        if self.haptic:
                            self.haptic.guide_to_target(
                                target['center'],
                                (frame.shape[1] // 2, frame.shape[0] // 2),
                                frame.shape[1]
                            )
                        if frame_count % 30 == 0:
                            print(f"🎯 Found: {target['class']} at {target['center']} "
                                  f"(conf: {target['confidence']:.2f})")
                    else:
                        if frame_count % 30 == 0:
                            print(f"🔍 Searching for '{self.target_object}'...")
                            if self.haptic:
                                self.haptic.notify_searching()
                else:
                    if frame_count % 60 == 0:
                        print("⏸️  No target set...")

                # --- Haptic update ---
                if self.haptic:
                    self.haptic.update_motors()

                # --- Display ---
                if self.show_display:
                    display_frame = self.draw_detections(frame.copy(), detections, target)
                    if RUN_CONFIG['fps_display'] and frame_count % 30 == 0:
                        fps = frame_count / (time.time() - fps_start)
                        cv2.putText(display_frame, f"FPS: {fps:.1f}", (10, 30),
                                    cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
                    cv2.imshow('Perception System', display_frame)
                    if cv2.waitKey(1) & 0xFF == ord('q'):
                        break

        except KeyboardInterrupt:
            print("\nStopping...")

        finally:
            print("Cleaning up...")
            if self.camera:
                self.camera.stop()
            if self.haptic:
                self.haptic.cleanup()
            if self.button:
                self.button.cleanup()
            if self.tts:
                self.tts.cleanup()
            if self.show_display:
                cv2.destroyAllWindows()
            print("System stopped")


def main():
    parser = argparse.ArgumentParser(description='HaloAssist Perception System')
    parser.add_argument('--model', type=str,
                        help='Model name (nano/small/medium/world-small) or path to model file')
    parser.add_argument('--profile', type=str, choices=['pi3', 'pi4', 'pi5', 'mac'],
                        help='Apply platform-specific configuration profile')
    args = parser.parse_args()

    if args.profile:
        apply_profile(args.profile)

    model_name = None
    model_path = None
    if args.model:
        if args.model in YOLO_MODELS:
            model_name = args.model
        else:
            model_path = args.model

    system = PerceptionSystem(model_name=model_name, model_path=model_path)
    system.run()


if __name__ == '__main__':
    main()
