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
import datetime

# Ensure the project root is in sys.path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Ensure the config directory is in sys.path
config_dir = project_root / 'config'
sys.path.insert(0, str(config_dir))

# Ensure the visualization directory is in sys.path
viz_dir = project_root.parent / 'visualization'
sys.path.insert(0, str(viz_dir))

# Ensure the llm directory is in sys.path
llm_dir = project_root.parent
sys.path.insert(0, str(llm_dir))

from perception.detector import detect_target_object
from perception_config import (
    YOLO_MODELS,
    CONFIDENCE_THRESHOLD,
    MIN_CONFIDENCE_THRESHOLD,
    CONFIDENCE_DECAY_PER_MISS,
    CONFIDENCE_SUCCESS_MARGIN,
    YOLOE_CONFIDENCE_DISCOUNT,
    COCO_CLASSES,
)
from run_config import RUN_CONFIG
from hardware_config import CAMERA_CONFIG, PICAMERA_CONFIG, HAPTIC_CONFIG
from hardware.haptic_controller import compute_motor_intensities, DEFAULT_MAX_INTENSITY
from llm.extractor import get_extracted_object, load_extractor_model

KEY_ESCAPE = 27
DEFAULT_OPEN_VOCAB_MODEL_KEY = 'yoloe-26n-seg'
LEGACY_OPEN_VOCAB_MODEL_KEY = 'yoloe-26-seg'
COCO_MODEL_KEY = 'yolo26n'

class PerceptionSystem:
    def __init__(self):
        """
        Initialize perception system.
        Components are created only if their flag is set in run_config.py.
        """
        self.model_paths = YOLO_MODELS
        self.open_vocab_model_key = self._resolve_open_vocab_model_key()
        # Default to open-vocab model before a target is set.
        self.active_model_key = self.open_vocab_model_key
        self.active_model_path = self.model_paths[self.active_model_key]

        # Add conditional imports here
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
            from visualization.haptic_client import HapticVisualizer

        # Initialize components
        self.haptic     = HapticController(haptic_config=HAPTIC_CONFIG) if RUN_CONFIG['enable_haptic'] else None
        self.button     = ButtonInterface()   if RUN_CONFIG['enable_button']     else None
        self.stt        = STTInterface()      if RUN_CONFIG['enable_speech']     else None
        self.tts        = TTSInterface()      if RUN_CONFIG['enable_tts']        else None
        self.audio      = AudioFeedback()     if RUN_CONFIG['enable_audio']      else None
        self.camera     = CameraInterface(
            camera_id=CAMERA_CONFIG['device_id'],
            width=CAMERA_CONFIG['width'],
            height=CAMERA_CONFIG['height'],
            picamera_config=PICAMERA_CONFIG,
        ) if RUN_CONFIG['enable_camera'] else None
        self.visualizer = HapticVisualizer()  if RUN_CONFIG['enable_visualizer'] else None

        # Initialize variables
        self.show_display     = RUN_CONFIG['show_display']
        self.target_object: Optional[str] = None
        self.is_idle          = True
        self.detected_objects = []
        self.matched_target_obj = None
        self.current_conf_threshold = CONFIDENCE_THRESHOLD
        self.no_detection_count = 0  # Counter for cycles with no detections
        configured_max_intensity = HAPTIC_CONFIG.get(
            'max_intensity',
            HAPTIC_CONFIG.get('default_strength', DEFAULT_MAX_INTENSITY),
        )
        self.visual_max_intensity = max(
            0.01,
            min(1.0, float(configured_max_intensity)),
        )

        if self.visualizer:
            self.visualizer.searching(self.target_object)

        # Initialize LLM
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

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _target_in_coco(self, target_object: str) -> bool:
        return target_object.lower() in COCO_CLASSES

    def _resolve_open_vocab_model_key(self) -> str:
        """Resolve the configured YOLOE key, supporting legacy naming."""
        if DEFAULT_OPEN_VOCAB_MODEL_KEY in self.model_paths:
            return DEFAULT_OPEN_VOCAB_MODEL_KEY
        if LEGACY_OPEN_VOCAB_MODEL_KEY in self.model_paths:
            return LEGACY_OPEN_VOCAB_MODEL_KEY
        raise KeyError(
            f"Open-vocab model key not found. Expected '{DEFAULT_OPEN_VOCAB_MODEL_KEY}' or "
            f"'{LEGACY_OPEN_VOCAB_MODEL_KEY}' in YOLO_MODELS."
        )

    def _select_model_for_target(self):
        if not self.target_object:
            self.active_model_key = self.open_vocab_model_key
        else:
            self.active_model_key = (
                COCO_MODEL_KEY if self._target_in_coco(self.target_object) else self.open_vocab_model_key
            )

        self.active_model_path = self.model_paths[self.active_model_key]

    def _get_model_adjusted_threshold(self) -> float:
        threshold = self.current_conf_threshold
        if self.active_model_key == self.open_vocab_model_key:
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
        """Record speech, extract object via LLM, update target."""
        if not (self.stt and self.stt.is_available()):
            return

        self.audio.button_press()  # Play button press sound
        text = self.stt.listen_while_pressed(self.button.is_pressed)

        if not text or not text.strip():
            print("❌ No speech recognised. Keeping current target.")
            if self.tts:
                self.tts.speak("I did not hear anything.")
            if self.audio:
                self.audio.error()
            return

        extraction = get_extracted_object(text)
        valid = (
            extraction.status == True
            and extraction.object.strip().lower() not in ("n/a", "large yellow pickaxe")
        )

        if not valid:
            print("❌ LLM failed to extract a valid object.")
            if self.tts:
                self.tts.speak("I did not understand.")
            if self.audio:
                self.audio.error()
            return

        self.target_object = extraction.object.lower()
        self._select_model_for_target()
        self.current_conf_threshold = CONFIDENCE_THRESHOLD
        print(f"✅ Target changed to: '{self.target_object}'")
        print(f"🧠 Using model: {self.active_model_key}")

        if self.visualizer:
            self.visualizer.searching(self.target_object)

        if self.tts:
            self.tts.speak("Looking for " + self.target_object)


        if self.audio:
            self.audio.success()

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
            self._select_model_for_target()
            self.is_idle = True
            self.detected_objects = []
            self.matched_target_obj = None
            self.current_conf_threshold = CONFIDENCE_THRESHOLD
            print("⏸️  Search stopped.")
            if self.tts:
                self.tts.speak("Search stopped")
            if self.visualizer:
                self.visualizer.stop()

    def _run_detection(self, frame):
        """Run target-only detection using the selected model."""
        if not self.target_object:
            self.detected_objects = []
            self.matched_target_obj = None
            self.no_detection_count += 1  # Increment no detection count
            if self.no_detection_count >= 3 and self.haptic:
                self.haptic.stop()  # Stop haptics after 3 cycles with no detections
            return

        self._select_model_for_target()
        model_adjusted_conf = self._get_model_adjusted_threshold()

        detection = detect_target_object(
            frame=frame,
            min_conf=model_adjusted_conf,
            target_obj=self.target_object,
            model_path=self.active_model_path,
        )

        if detection is None:
            self.detected_objects = []
            self.matched_target_obj = None
            self._on_detection_miss()
            self.no_detection_count += 1  # Increment no detection count
            if self.no_detection_count >= 60 and self.haptic:
                self.haptic.stop()  # Stop haptics after 3 cycles with no detections
            return

        self.no_detection_count = 0  # Reset counter on successful detection
        self._on_detection_success(detection.confidence)
        x1, y1, x2, y2 = [int(v) for v in detection.bbox]
        cx, cy = [int(v) for v in detection.center]
        self.matched_target_obj = {
            'class': self.target_object,
            'bbox': [x1, y1, x2, y2],
            'center': (cx, cy),
            'confidence': detection.confidence,
        }
        self.detected_objects = [self.matched_target_obj]

    def _apply_motor_outputs(self, matched_target: dict, frame):
        """Update motors and visualizer from one shared output path."""
        left_intensity = 0.0
        right_intensity = 0.0

        if matched_target:
            if self.haptic:
                self.haptic.calc_motor_strengths(
                    matched_target['center'],
                    (frame.shape[1] // 2, frame.shape[0] // 2),
                    frame.shape[1],
                )
                self.haptic.update_motors()
                left_intensity, right_intensity = self.haptic.get_current_intensities()
            else:
                left_intensity, right_intensity = compute_motor_intensities(
                    matched_target['center'],
                    frame.shape[1],
                    max_intensity=self.visual_max_intensity,
                )
        elif self.haptic:
            # Keep visualizer synchronized with actual hardware state while search decays.
            self.haptic.update_motors()
            left_intensity, right_intensity = self.haptic.get_current_intensities()

        if not self.visualizer:
            return

        if self.target_object and left_intensity == 0.0 and right_intensity == 0.0:
            self.visualizer.searching(self.target_object)
            return

        max_intensity = max(left_intensity, right_intensity)
        if max_intensity <= 0.0:
            position = None
        else:
            # Treat near-equal intensity as centered to avoid jitter around mid-frame.
            intensity_delta = abs(left_intensity - right_intensity)
            if intensity_delta <= 0.2 * max_intensity:
                position = 'center'
            elif left_intensity > right_intensity:
                position = 'left'
            else:
                position = 'right'

        activity_floor = 0.01 * max_intensity if max_intensity > 0.0 else 0.0
        left_on = left_intensity > activity_floor
        right_on = right_intensity > activity_floor

        self.visualizer.update_motors(
            left=left_on,
            right=right_on,
            intensity_left=left_intensity,
            intensity_right=right_intensity,
            target_object=self.target_object,
            position=position,
        )

    def _log_status(self, matched_target, frame_count: int):
        """Log detection status to console every second (debug only)."""
        current_time = datetime.datetime.now()
        if not hasattr(self, '_last_log_time'):
            self._last_log_time = current_time

        # Log only if at least 1 second has passed since the last log
        if (current_time - self._last_log_time).total_seconds() >= 1:
            self._last_log_time = current_time
            timestamp = current_time.strftime("%Y-%m-%d %H:%M:%S")

            if matched_target:
                print(f"[{timestamp}] 🎯 Found: {matched_target['class']} at {matched_target['center']} "
                      f"(conf: {matched_target['confidence']:.2f}, min: {self._get_model_adjusted_threshold():.2f})")
            elif self.target_object:
                if not self.camera:
                    print(f"[{timestamp}] 🔍 Searching paused (no camera): '{self.target_object}' "
                          f"(min: {self._get_model_adjusted_threshold():.2f}, decay paused - no frames)")
                else:
                    print(f"[{timestamp}] 🔍 Searching for target object: '{self.target_object}' "
                          f"(min: {self._get_model_adjusted_threshold():.2f})...")
            else:
                print(f"[{timestamp}] ⏸️  No target set...")

    def _update_visual_display(self, frame, detections: list, matched_target, frame_count: int, fps_start: float) -> bool:
        """
        Render visual output for debugging and user feedback.

        This method is responsible for:
        - Drawing bounding boxes and labels for detected objects.
        - Displaying FPS (if enabled in RUN_CONFIG).
        - Handling user input for quitting the application.

        Returns:
            True to continue the main loop, False to quit.
        """
        if not self.show_display or frame is None:
            return True

        display = frame.copy()
        for det in detections:
            x1, y1, x2, y2 = det['bbox']
            is_target = det == matched_target
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


    # ------------------------------------------------------------------
    # Main loop
    # ------------------------------------------------------------------
    def run(self):
        """
        Start and manage the perception system's main loop.

        This method is responsible for:
        - Initializing and starting the camera (if available).
        - Playing the startup sound.
        - Running the main loop for detection, feedback, and display updates.
        - Handling keyboard interrupts and cleaning up resources upon exit.

        Returns:
            None
        """

        print("\nStarting perception system...")

        if self.camera:
            if not self.camera.start():
                print("❌ Failed to start camera. Continuing without camera.")
                self.camera = None
        else:
            print("⚠️  No camera detected. Running without camera.")

        if self.audio:
            self.audio.bootup() # Play startup sound

        frame_count = 0
        fps_start   = time.time()

        try:
            while True:
                # Check button state and listen for new target if pressed
                self._handle_button()

                # Read frame from camera (if available) and run detection
                camera_frame = self.camera.read_frame() if self.camera else None

                # Don't run detection if we don't have a frame (camera failure), but continue the loop to keep the system responsive
                if self.camera and camera_frame is None:
                    print("⚠️  Warning: Failed to read frame from camera")
                    continue

                if camera_frame is not None:
                    self._run_detection(camera_frame)
                    self._apply_motor_outputs(self.matched_target_obj, camera_frame)

                frame_count += 1
                self._log_status(self.matched_target_obj, frame_count)

                if not self._update_visual_display(
                    camera_frame,
                    self.detected_objects,
                    self.matched_target_obj,
                    frame_count,
                    fps_start,
                ):
                    break

        except KeyboardInterrupt: # Exit on Ctrl+C
            print("\nKeyboardInterrupt received. Stopping...")
        finally:
            self._cleanup()
            time.sleep(1) # Ensure all resources are released before exiting


def main():
    """
    Parse command-line arguments and configure the perception system.

    This function sets up the system by:
    - Parsing feature-toggle arguments.
    - Initializing and running the `PerceptionSystem`.

    Args:
        --disable-haptics: Disable haptic feedback.
        --disable-speech: Disable speech input.
        --disable-tts: Disable text-to-speech output.
        --disable-audio: Disable audio feedback.
        --disable-visualizer: Disable visualizer.
    """
    parser = argparse.ArgumentParser(description='HaloAssist Perception System')
    parser.add_argument('--disable-haptics', action='store_true', help='Disable haptic feedback')
    parser.add_argument('--disable-speech', action='store_true', help='Disable speech input')
    parser.add_argument('--disable-tts', action='store_true', help='Disable text-to-speech output')
    parser.add_argument('--disable-audio', action='store_true', help='Disable audio feedback')
    parser.add_argument('--disable-visualizer', action='store_true', help='Disable visualizer')
    args = parser.parse_args()    # Parse arguments

    # Override RUN_CONFIG based on arguments
    if args.disable_haptics:
        RUN_CONFIG['enable_haptic'] = False
    if args.disable_speech:
        RUN_CONFIG['enable_speech'] = False
    if args.disable_tts:
        RUN_CONFIG['enable_tts'] = False
    if args.disable_audio:
        RUN_CONFIG['enable_audio'] = False
    if args.disable_visualizer:
        RUN_CONFIG['enable_visualizer'] = False

    system = PerceptionSystem()
    system.run()


if __name__ == '__main__': # Run main() if this script is executed directly
    main()
