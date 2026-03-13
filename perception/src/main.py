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

config_dir = Path(__file__).parent.parent / 'config'
sys.path.insert(0, str(config_dir))

viz_dir = Path(__file__).parent.parent.parent / 'visualization'
sys.path.insert(0, str(viz_dir))

from perception.detector import ObjectDetector
from perception_config import YOLO_MODELS, DEFAULT_MODEL, apply_profile
from run_config import RUN_CONFIG
from llm.extractor import get_extracted_object, load_extractor_model

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
if RUN_CONFIG['enable_visualizer']:
    from haptic_client import HapticVisualizer

KEY_ESCAPE = 27


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

        self.detector   = ObjectDetector(model_path=model_path)
        self.haptic     = HapticController()  if RUN_CONFIG['enable_haptic']     else None
        self.button     = ButtonInterface()   if RUN_CONFIG['enable_button']     else None
        self.stt        = STTInterface()      if RUN_CONFIG['enable_speech']     else None
        self.tts        = TTSInterface()      if RUN_CONFIG['enable_tts']        else None
        self.audio      = AudioFeedback()     if RUN_CONFIG['enable_audio']      else None
        self.camera     = CameraInterface(width=1280, height=720) if RUN_CONFIG['enable_camera'] else None
        self.visualizer = HapticVisualizer()  if RUN_CONFIG['enable_visualizer'] else None

        self.show_display  = RUN_CONFIG['show_display']
        self.target_object: Optional[str] = "cup"
        self.is_yolo_world = 'world' in str(model_path).lower() or 'yoloe' in str(model_path).lower()
        self.is_idle       = True

        if self.haptic:
            self.haptic.set_target(self.target_object)
        if self.visualizer:
            self.visualizer.searching(self.target_object)

        load_extractor_model()

        print("Perception System initialized")
        print(f"  YOLO model:     {model_path}")
        print(f"  Haptic:         {'enabled' if self.haptic else 'DISABLED'}")
        print(f"  Button:         {'enabled' if self.button else 'DISABLED'}")
        print(f"  Speech (STT):   {'enabled' if self.stt and self.stt.is_available() else 'DISABLED'}")
        print(f"  TTS:            {'enabled' if self.tts and self.tts.is_available() else 'DISABLED'}")
        print(f"  Audio feedback: {'enabled' if self.audio else 'DISABLED'}")
        print(f"  Visualizer:     {'enabled' if self.visualizer else 'DISABLED'}")
        print(f"  Display:        {'enabled' if self.show_display else 'DISABLED'}")

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _listen_and_set_target(self):
        """Record speech, extract object via LLM, update target."""
        if not (self.stt and self.stt.is_available()):
            return

        text = self.stt.listen_while_pressed(self.button.is_pressed)
        if not text or not text.strip():
            print("❌ No speech recognised. Keeping current target.")
            if self.audio:
                self.audio.error()
            return

        extraction = get_extracted_object(text)
        valid = (
            extraction.status == "success"
            and extraction.object_of_interest.strip().lower() not in ("n/a", "large yellow pickaxe")
        )

        if not valid:
            print("❌ LLM failed to extract a valid object.")
            if self.tts:
                self.tts.speak("I did not understand.")
            return

        self.target_object = extraction.object_of_interest.lower()
        print(f"✅ Target changed to: '{self.target_object}'")

        if self.haptic:
            self.haptic.set_target(self.target_object)
        if self.visualizer:
            self.visualizer.searching(self.target_object)

        if self.is_yolo_world:
            try:
                self.detector.model.set_classes([self.target_object])
            except Exception as e:
                print(f"⚠️  Could not update YOLO classes: {e}")

        if self.tts:
            self.tts.speak("Looking for " + self.target_object)

        self.is_idle = False

    def _handle_button(self):
        """Handle button press: start listening or cancel active search."""
        if not (self.button and self.button.is_pressed()):
            return

        if self.is_idle:
            print("\n🔘 Button pressed! Listening while held...")
            self._listen_and_set_target()
        else:
            self.target_object = None
            self.is_idle = True
            print("⏸️  Search stopped.")
            if self.tts:
                self.tts.speak("Search stopped")
            if self.visualizer:
                self.visualizer.stop()

    def _run_detection(self, frame) -> tuple:
        """Run YOLO detection, update haptic guidance, and update visualizer.

        Returns:
            (detections, target) where target is the matching detection or None.
        """
        if not self.target_object:
            return [], None

        detections = self.detector.detect(frame)
        target = next(
            (d for d in detections if self.target_object in d['class'].lower()),
            None
        )

        if target is not None:
            offset = (target['center'][0] - frame.shape[1] / 2) / (frame.shape[1] / 2)
            offset = max(-1.0, min(1.0, offset))

            if self.haptic:
                self.haptic.guide_to_target(
                    target['center'],
                    (frame.shape[1] // 2, frame.shape[0] // 2),
                    frame.shape[1]
                )
            if self.visualizer:
                position = 'left' if offset < -0.33 else ('right' if offset > 0.33 else 'center')
                self.visualizer.update_motors(
                    left=offset < 0,
                    right=offset > 0,
                    intensity_left=abs(offset) if offset < 0 else 0.0,
                    intensity_right=abs(offset) if offset > 0 else 0.0,
                    target_object=self.target_object,
                    position=position
                )
        else:
            if self.haptic:
                self.haptic.notify_searching()
            if self.visualizer:
                self.visualizer.searching(self.target_object)

        return detections, target

    def _log_status(self, target, frame_count: int):
        """Log detection status to console every 30 frames (debug only)."""
        if frame_count % 30 != 0:
            return
        if target:
            print(f"🎯 Found: {target['class']} at {target['center']} "
                  f"(conf: {target['confidence']:.2f})")
        elif self.target_object:
            print(f"🔍 Searching for '{self.target_object}'...")
        else:
            print("⏸️  No target set...")

    def _update_display(self, frame, detections: list, target, frame_count: int, fps_start: float) -> bool:
        """Draw detections and FPS overlay, handle quit key.

        Returns:
            True to continue, False to quit.
        """
        if not self.show_display:
            return True

        display = frame.copy()
        for det in detections:
            x1, y1, x2, y2 = det['bbox']
            is_target = det == target
            color     = (0, 255, 0) if is_target else (255, 0, 0)
            thickness = 3 if is_target else 1

            cv2.rectangle(display, (x1, y1), (x2, y2), color, thickness)
            cv2.putText(display, f"{det['class']} {det['confidence']:.2f}",
                        (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)

            if is_target:
                cx, cy = det['center']
                cv2.circle(display, (cx, cy), 8, (0, 0, 255), -1)
                cv2.putText(display, "TARGET", (cx - 30, cy - 15),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 2)

        if RUN_CONFIG['fps_display']:
            fps = frame_count / (time.time() - fps_start)
            cv2.putText(display, f"FPS: {fps:.1f}", (10, 30),
                        cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)

        cv2.imshow('Perception System', display)
        return cv2.waitKey(1) & 0xFF != KEY_ESCAPE

    def _cleanup(self):
        """Release all hardware and display resources."""
        print("Cleaning up...")
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
        print("System stopped")

    # ------------------------------------------------------------------
    # Main loop
    # ------------------------------------------------------------------

    def run(self):
        """Start the camera and enter the main processing loop."""
        print("\nStarting perception system...")

        if self.camera:
            if not self.camera.start():
                print("❌ Failed to start camera")
                return
            print("✅ Camera started")

        if self.audio:
            self.audio.alert()

        frame_count = 0
        fps_start   = time.time()
        detections  = []
        target      = None

        try:
            while True:
                if not self.camera:
                    break

                frame = self.camera.read_frame()
                if frame is None:
                    print("⚠️  Warning: None frame from camera")
                    continue

                frame_count += 1

                self._handle_button()
                detections, target = self._run_detection(frame)

                if self.haptic:
                    self.haptic.update_motors()

                self._log_status(target, frame_count)

                if not self._update_display(frame, detections, target, frame_count, fps_start):
                    break

        except KeyboardInterrupt:
            print("\nStopping...")
        finally:
            self._cleanup()


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
