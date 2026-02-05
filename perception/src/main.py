"""
Main application entry point
Integrates detection, guidance, and haptic feedback with hardware components
Supports flexible configuration for different platforms (Pi3/Pi4/Pi5)
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
from hardware.haptic_controller import HapticController
from hardware.button_interface import ButtonInterface
from hardware.speech_interface import SpeechInterface
from perception.camera import CameraInterface
from hardware_config import YOLO_MODELS, DEFAULT_MODEL, apply_profile
from hardware_config import YOLO_MODELS, DEFAULT_MODEL, apply_profile


class PerceptionSystem:
    def __init__(self, model_name: Optional[str] = None, 
                 model_path: Optional[str] = None,
                 show_display: bool = True,
                 enable_speech: bool = False):
        """
        Initialize perception system
        
        Args:
            model_name: Model name from config ('nano', 'small', 'medium', 'world-small', etc.)
            model_path: Direct path to model file (overrides model_name)
            show_display: Whether to show visual display (for testing)
            enable_speech: Whether to enable speech input
        """
        # Determine model path
        if model_path is None:
            model_name = model_name or DEFAULT_MODEL
            model_path = YOLO_MODELS.get(model_name, YOLO_MODELS[DEFAULT_MODEL])
        
        self.detector = ObjectDetector(model_path=model_path)
        self.haptic = HapticController()
        self.button = ButtonInterface()
        self.speech = SpeechInterface() if enable_speech else None
        self.camera = CameraInterface()
        self.show_display = show_display
        self.target_object = None  # Track the object user wants to find
        self.is_yolo_world = 'world' in str(model_path).lower()
        
        print("Perception System initialized")
        print(f"- YOLO model: {model_path}")
        print(f"- Motors: {self.haptic.num_motors}-motor array")
        print(f"- Haptic feedback: {'enabled' if self.haptic._is_pi else 'simulated'}")
        print(f"- Button input: {'enabled' if self.button._is_pi else 'disabled'}")
        print(f"- Speech input: {'enabled' if self.speech and self.speech.is_available() else 'disabled'}")
        print(f"- Display mode: {show_display}")
        
        # If speech is enabled, wait for user to specify target
        if enable_speech:
            print("\n⚠️  WORKFLOW: Press button and say the object you want to find")
            print("   Example: 'bottle', 'cup', 'phone', 'person'")
            print("   System will then guide you to that object\n")
        else:
            print("\n💡 Running in continuous detection mode (no speech input)")
            print("   System detects all objects and guides to the closest one\n")
    
    def draw_detections(self, frame, detections, target_detection):
        """Draw detection boxes and guidance on frame"""
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
        """Main processing loop"""
        print("\nStarting perception system...")
        print("Press 'q' to quit\n")
        
        if not self.camera.start():
            print("Failed to start camera")
            return
        
        try:
            frame_count = 0
            fps_start = time.time()
            
            while True:
                frame = self.camera.read_frame()
                if frame is None:
                    break
                
                frame_count += 1
                
                # Check for button press FIRST (to set target object)
                if self.button.is_pressed():
                    print("\n🔘 Button pressed!")
                    if self.speech and self.speech.is_available():
                        print("🎤 Listening for target object...")
                        text = self.speech.listen(duration=3)
                        if text and text.strip():
                            self.target_object = text.strip().lower()
                            print(f"✅ Target set: '{self.target_object}'")
                            
                            # Update YOLO-World detection classes if using YOLO-World
                            if self.is_yolo_world:
                                try:
                                    self.detector.model.set_classes([self.target_object])
                                    print(f"🎯 YOLO-World now detecting: {self.target_object}")
                                except Exception as e:
                                    print(f"⚠️  Could not update YOLO classes: {e}")
                        else:
                            print("❌ No speech recognized. Try again.")
                    time.sleep(0.5)  # Debounce
                
                # Only detect and guide if we have a target object
                if self.target_object:
                    # Detect objects
                    detections = self.detector.detect(frame)
                    
                    # Filter for target object (or get closest match)
                    target = None
                    for det in detections:
                        if self.target_object in det['class'].lower():
                            target = det
                            break
                    
                    # If no exact match, get closest object
                    if target is None and detections:
                        target = self.detector.get_closest_object(detections, frame.shape[:2])
                    
                    # Provide haptic feedback based on target location
                    if target is not None:
                        self.haptic.guide_to_target(
                            target['center'], 
                            (frame.shape[1] // 2, frame.shape[0] // 2),
                            frame.shape[1]
                        )
                        
                        print(f"🎯 Found: {target['class']} at {target['center']} "
                              f"(conf: {target['confidence']:.2f})")
                    else:
                        # Show status that we're looking for the target
                        if frame_count % 30 == 0:  # Print every 30 frames
                            print(f"🔍 Searching for '{self.target_object}'...")
                else:
                    # No target set yet
                    if frame_count % 60 == 0:  # Print every 60 frames
                        if self.speech and self.speech.is_available():
                            print("⏸️  Waiting for button press to set target object...")
                        else:
                            # Mac demo mode - detect everything
                            pass
                    
                    # Still detect everything for display purposes (Mac demo mode)
                    detections = self.detector.detect(frame)
                    target = self.detector.get_closest_object(detections, frame.shape[:2]) if detections else None
                    
                    # Provide haptic feedback for closest object
                    if target is not None:
                        self.haptic.guide_to_target(
                            target['center'], 
                            (frame.shape[1] // 2, frame.shape[0] // 2),
                            frame.shape[1]
                        )
                        if frame_count % 30 == 0:  # Print every 30 frames
                            print(f"🎯 Closest: {target['class']} at {target['center']} "
                                  f"(conf: {target['confidence']:.2f})")
                
                # Display
                if self.show_display:
                    display_frame = self.draw_detections(frame.copy(), detections, target)
                    
                    # Show FPS
                    if frame_count % 30 == 0:
                        fps = frame_count / (time.time() - fps_start)
                        cv2.putText(display_frame, f"FPS: {fps:.1f}", (10, 30),
                                   cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
                    
                    cv2.imshow('Perception System', display_frame)
                    
                    if cv2.waitKey(1) & 0xFF == ord('q'):
                        break
                
                # Small delay to prevent overwhelming the system
                time.sleep(0.05)
        
        except KeyboardInterrupt:
            print("\nStopping...")
        
        finally:
            print("Cleaning up resources...")
            self.camera.stop()
            self.haptic.cleanup()
            self.button.cleanup()  # Clean button last
            if self.show_display:
                cv2.destroyAllWindows()
            print("System stopped")


def main():
    parser = argparse.ArgumentParser(description='Perception System for Blind Assistance')
    parser.add_argument('--model', type=str, 
                       help='Model name (nano/small/medium/world-small/world-medium) or path to model file')
    parser.add_argument('--profile', type=str, choices=['pi3', 'pi4', 'pi5', 'mac'],
                       help='Apply platform-specific configuration profile')
    parser.add_argument('--no-display', action='store_true',
                       help='Disable visual display')
    parser.add_argument('--enable-speech', action='store_true',
                       help='Enable speech input (requires button press)')
    
    args = parser.parse_args()
    
    # Apply platform profile if specified
    if args.profile:
        apply_profile(args.profile)
    
    # Determine if model arg is a name or path
    model_name = None
    model_path = None
    if args.model:
        if args.model in YOLO_MODELS:
            model_name = args.model
        else:
            model_path = args.model
    
    system = PerceptionSystem(
        model_name=model_name,
        model_path=model_path,
        show_display=not args.no_display,
        enable_speech=args.enable_speech
    )
    
    system.run()


if __name__ == '__main__':
    main()
