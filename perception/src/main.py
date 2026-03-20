"""
Main application entry point
Integrates detection, guidance, and haptic feedback with hardware components.
Supports flexible configuration for different platforms (Pi3/Pi4/Pi5).

Latency improvements (from 1-integration branch):
  - Non-blocking haptic pulses (no time.sleep in motor code)
  - Button-held STT (record only while held, no fixed 3 s wait)
  - Piper neural TTS feedback via TTSInterface class
  - detect_interval throttles YOLO so the camera loop stays fast

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
import os
import datetime  # Add this import at the top of the file if not already present

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

from perception.detector import ObjectDetector
from perception_config import YOLO_MODELS, DEFAULT_MODEL, apply_profile
from run_config import RUN_CONFIG
from llm.extractor import get_extracted_object, load_extractor_model

KEY_ESCAPE = 27

class PerceptionSystem:
    def __init__(self, model: Optional[str] = None):
        """
        Initialize perception system.
        Components are created only if their flag is set in run_config.py.

        Args:
            model: Model name from perception_config ('nano', 'small', etc.) or direct path to model file.
        """
        # Determine model_path based on input
        if model and os.path.isfile(model):
            model_path = model  # Direct path provided
        elif model and model in YOLO_MODELS:
            model_path = YOLO_MODELS[model]  # Model name provided
        else:
            print(f"ℹ️ No valid model provided. Defaulting to 'yoloe-26n-seg.pt'")
            model_path = str(Path(__file__).parent.parent / 'models' / 'yoloe-26n-seg.pt')

        # Initialize ObjectDetector
        self.detector = ObjectDetector(model_path=model_path)

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
        self.haptic     = HapticController() if RUN_CONFIG['enable_haptic'] else None
        self.button     = ButtonInterface()   if RUN_CONFIG['enable_button']     else None
        self.stt        = STTInterface()      if RUN_CONFIG['enable_speech']     else None
        self.tts        = TTSInterface()      if RUN_CONFIG['enable_tts']        else None
        self.audio      = AudioFeedback()     if RUN_CONFIG['enable_audio']      else None
        self.camera     = CameraInterface(width=1280, height=720) if RUN_CONFIG['enable_camera'] else None
        self.visualizer = HapticVisualizer()  if RUN_CONFIG['enable_visualizer'] else None

        # Initialize variables
        self.show_display     = RUN_CONFIG['show_display']
        self.target_object: Optional[str] = None
        self.is_yolo_world = 'world' in model_path.lower()
        self.is_idle          = True
        self._last_detect_time = 0.0  # tracks when YOLO last ran

        if self.visualizer:
            self.visualizer.searching(self.target_object)

        # Initialize LLM
        load_extractor_model()

        print("Perception System initialized")
        print(f"  YOLO model:     {model_path}")
        print(f"  Detect interval:{RUN_CONFIG['detect_interval']} s")
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

    def _get_matching_target_object(self, detected_objects: list) -> Optional[dict]:
        """Match the detected objects to the target object."""
        if not self.target_object:  # Ensure target_object is not None
            return None
        return next((d for d in detected_objects if self.target_object in d['class'].lower()), None)

    def _update_visualizer(self, matched_target: dict, offset: float):
        """Update the visualizer based on the matched target and offset."""
        if self.visualizer:
            if matched_target:
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
                self.visualizer.searching(self.target_object)

    def _calc_haptic_strengths(self, matched_target: dict, frame):
        if matched_target and self.haptic:
            self.haptic.calc_motor_strengths(
                matched_target['center'], (frame.shape[1] // 2, frame.shape[0] // 2), frame.shape[1]
                )

    def _update_visualizer(self, matched_target: dict, frame):
        """Delegate visualizer updates."""
        offset = (matched_target['center'][0] - frame.shape[1] / 2) / (frame.shape[1] / 2) if matched_target else 0
        if self.visualizer:
            if matched_target:
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
                self.visualizer.searching(self.target_object)

    def _log_status(self, matched_target, frame_count: int):
        """Log detection status to console every 30 frames (debug only)."""
        current_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")  # Get current time

        if matched_target:
            print(f"[{current_time}] 🎯 Found: {matched_target['class']} at {matched_target['center']} "
                  f"(conf: {matched_target['confidence']:.2f})")
        elif self.target_object:
            print(f"[{current_time}] 🔍 Searching for target object: '{self.target_object}'...")
        else:
            print(f"[{current_time}] ⏸️  No target set...")

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
            self.audio.alert() # Play startup sound

        frame_count = 0
        fps_start   = time.time()
        detected_objects  = []
        matched_target_obj = None 

        try:
            while True:
                # Check button state and listen for new target if pressed
                self._handle_button()

                # Read frame from camera
                if self.camera:
                    camera_frame = self.camera.read_frame()
                    if camera_frame is None:
                        print("⚠️  Warning: None frame from camera")
                        continue
                else:
                    camera_frame = None  # No camera, proceed without frame

                if camera_frame is not None:
                    current_time = time.time()
                    # Throttle YOLO detection to run only at intervals defined in RUN_CONFIG
                    if current_time - self._last_detect_time >= RUN_CONFIG['detect_interval']: 
                        self._last_detect_time = current_time

                        detected_objects = self.detector.get_detected_objects(camera_frame)
                        matched_target_obj = self._get_matching_target_object(detected_objects)
                        self._calc_haptic_strengths(matched_target_obj, camera_frame)
                        self._update_visualizer(matched_target_obj, camera_frame)

                if self.haptic:
                    self.haptic.update_motors() # Update haptic motors (non-blocking)

                frame_count += 1
                self._log_status(matched_target_obj, frame_count) # Update log_status call

                if not self._update_visual_display(camera_frame, detected_objects, matched_target_obj, frame_count, fps_start): # Update display call
                    break # Exit loop if ESC key is pressed

        except KeyboardInterrupt:
            print("\nKeyboardInterrupt received. Stopping...")
        finally:
            self._cleanup()


def main():
    """
    Parse command-line arguments and configure the perception system.

    This function sets up the system by:
    - Parsing arguments for model selection and feature toggles.
    - Applying platform-specific configuration profiles.
    - Initializing and running the `PerceptionSystem`.

    Args:
        --model <str>: Model name (nano/small/medium/world-small) or path to model file.
        --profile <str>: Apply platform-specific configuration profile (pi3/pi4/pi5/mac).
        --disable-haptics: Disable haptic feedback.
        --disable-speech: Disable speech input.
        --disable-tts: Disable text-to-speech output.
        --disable-audio: Disable audio feedback.
        --disable-visualizer: Disable visualizer.

    Returns:
        None
    """
    parser = argparse.ArgumentParser(description='HaloAssist Perception System')
    parser.add_argument('--model', type=str, help='Model name (nano/small/medium/world-small) or path to model file')
    parser.add_argument('--profile', type=str, choices=['pi3', 'pi4', 'pi5', 'mac'], help='Apply platform-specific configuration profile')
    parser.add_argument('--disable-haptics', action='store_true', help='Disable haptic feedback')
    parser.add_argument('--disable-speech', action='store_true', help='Disable speech input')
    parser.add_argument('--disable-tts', action='store_true', help='Disable text-to-speech output')
    parser.add_argument('--disable-audio', action='store_true', help='Disable audio feedback')
    parser.add_argument('--disable-visualizer', action='store_true', help='Disable visualizer')

    args = parser.parse_args()    # Parse arguments

    # Apply platform profile if specified
    if args.profile:
        apply_profile(args.profile)
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

    system = PerceptionSystem(model=args.model)
    system.run()


if __name__ == '__main__': # Run main() if this script is executed directly
    main()