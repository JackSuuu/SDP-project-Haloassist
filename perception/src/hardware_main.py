"""
Hardware-Integrated Perception System
Implements the hardware pipeline:
Button Press -> TTS -> Camera Detection -> Motor Control -> Button Press -> End
"""
import cv2
import time
from perception.camera import CameraInterface
from perception.detector import ObjectDetector
from hardware import ButtonInterface, TTSInterface, VibrationalMotorController
from feedback.haptic_two_motor import TwoMotorHapticFeedback


class HardwareIntegratedSystem:
    """
    Complete hardware-integrated perception system for Raspberry Pi 3
    with 2 vibrational motors for left/right directional guidance
    """
    
    def __init__(self, model_path: str = 'yolov8s-world.pt',
                 button_pin: int = 5,
                 left_motor_pin: int = 17,
                 right_motor_pin: int = 18,
                 camera_id: int = 0,
                 simulation_mode: bool = None):
        """
        Initialize hardware-integrated perception system
        
        Args:
            model_path: Path to YOLO-World model
            button_pin: GPIO pin for control button
            left_motor_pin: GPIO pin for left motor
            right_motor_pin: GPIO pin for right motor
            camera_id: Camera device ID
            simulation_mode: Force simulation mode (None = auto-detect)
        """
        print("Initializing Hardware-Integrated Perception System...")
        
        # Initialize components
        self.detector = ObjectDetector(model_path=model_path)
        self.camera = CameraInterface(camera_id=camera_id)
        self.button = ButtonInterface(button_pin=button_pin, simulation_mode=simulation_mode)
        self.tts = TTSInterface(simulation_mode=simulation_mode)
        self.haptic = TwoMotorHapticFeedback(
            left_motor_pin=left_motor_pin,
            right_motor_pin=right_motor_pin,
            simulation_mode=simulation_mode
        )
        
        self.is_running = False
        
        print("✓ Object Detector initialized")
        print("✓ Camera interface initialized")
        print("✓ Button interface initialized")
        print("✓ TTS interface initialized")
        print("✓ Haptic feedback initialized (2-motor system)")
        print(f"  - Left motor: GPIO {left_motor_pin}")
        print(f"  - Right motor: GPIO {right_motor_pin}")
        print(f"  - Button: GPIO {button_pin}")
    
    def detection_cycle(self):
        """
        Single detection cycle: activate camera -> detect -> provide feedback
        
        Returns:
            True if cycle completed successfully, False if error
        """
        # Start camera
        if not self.camera.start():
            self.tts.speak("Camera failed to start")
            return False
        
        self.tts.speak("Detection active")
        print("\n=== Detection Cycle Started ===")
        
        try:
            detection_start = time.time()
            frame_count = 0
            last_feedback_time = time.time()
            
            while self.is_running:
                # Read frame
                frame = self.camera.read_frame()
                if frame is None:
                    break
                
                frame_count += 1
                
                # Detect objects
                detections = self.detector.detect(frame)
                
                # Get target object for guidance
                target = self.detector.get_closest_object(detections, frame.shape[:2])
                
                # Provide haptic feedback at regular intervals (every 0.3s)
                current_time = time.time()
                if target is not None and (current_time - last_feedback_time) >= 0.3:
                    # Calculate distance score
                    frame_center = (frame.shape[1] // 2, frame.shape[0] // 2)
                    cx, cy = target['center']
                    dist = ((cx - frame_center[0])**2 + (cy - frame_center[1])**2)**0.5
                    max_dist = (frame.shape[1]**2 + frame.shape[0]**2)**0.5 / 2
                    distance_score = 1.0 - min(dist / max_dist, 1.0)
                    
                    # Provide guidance
                    feedback = self.haptic.provide_guidance(
                        target['center'],
                        frame.shape[:2],
                        distance_score
                    )
                    
                    print(f"Target: {target['class']} | "
                          f"Position: {target['center']} | "
                          f"Confidence: {target['confidence']:.2f} | "
                          f"Distance: {distance_score:.2f} | "
                          f"Motor Output: LEFT: {feedback['LEFT']}, RIGHT: {feedback['RIGHT']}")
                    
                    last_feedback_time = current_time
                else:
                    # No target detected, stop motors
                    if current_time - last_feedback_time >= 0.5:
                        self.haptic.stop_motors()
                        print("No target detected - motors stopped")
                        last_feedback_time = current_time
                
                # Check for button press to stop
                if self.button.button_press():
                    print("\n=== Button Pressed - Stopping Detection ===")
                    break
                
                # Small delay
                time.sleep(0.05)
            
            # Stop motors
            self.haptic.stop_motors()
            
            # Calculate statistics
            duration = time.time() - detection_start
            fps = frame_count / duration if duration > 0 else 0
            
            print(f"\n=== Detection Cycle Complete ===")
            print(f"Duration: {duration:.1f}s | Frames: {frame_count} | FPS: {fps:.1f}")
            
            return True
            
        except Exception as e:
            print(f"Error during detection cycle: {e}")
            self.tts.speak("Detection error occurred")
            return False
        
        finally:
            # Always stop camera and motors
            self.camera.stop()
            self.haptic.stop_motors()
    
    def run(self):
        """
        Main hardware pipeline loop:
        1. Wait for button press
        2. TTS announcement
        3. Activate camera detection
        4. Provide motor feedback
        5. Wait for button press to stop
        6. Repeat or end
        """
        print("\n" + "="*50)
        print("Hardware-Integrated Perception System")
        print("="*50)
        print("\nPipeline:")
        print("  1. Press button to start")
        print("  2. System announces activation (TTS)")
        print("  3. Camera detection begins")
        print("  4. Vibrational motors provide directional guidance")
        print("     - LEFT motor for left direction")
        print("     - RIGHT motor for right direction")
        print("     - Both motors equal when object centered")
        print("  5. Press button again to stop detection")
        print("  6. Press button once more to exit system")
        print("\nPress Ctrl+C to exit anytime\n")
        
        self.tts.speak("System ready. Press button to start detection.")
        
        try:
            while True:
                # Step 1: Wait for button press to start
                print("\n[WAITING] Press button to start detection...")
                self.button.wait_for_button()
                
                # Step 2: TTS announcement
                print("[BUTTON] Button pressed - starting detection")
                self.tts.speak("Starting detection")
                time.sleep(0.5)  # Brief pause
                
                # Step 3-4: Run detection cycle (camera + motor feedback)
                self.is_running = True
                success = self.detection_cycle()
                self.is_running = False
                
                # Step 5: Detection stopped
                if success:
                    self.tts.speak("Detection stopped")
                
                # Check if user wants to exit (press button within 3 seconds)
                print("\n[WAITING] Press button within 3 seconds to exit, or wait to continue...")
                if self.button.wait_for_button(timeout=3.0):
                    print("[BUTTON] Button pressed - exiting system")
                    self.tts.speak("Shutting down system")
                    break
                else:
                    print("[TIMEOUT] Continuing to next cycle")
                    self.tts.speak("Ready for next detection")
        
        except KeyboardInterrupt:
            print("\n\n[INTERRUPT] Keyboard interrupt received")
            self.tts.speak("System interrupted")
        
        finally:
            # Cleanup all hardware resources
            print("\nCleaning up hardware resources...")
            self.haptic.cleanup()
            self.button.cleanup()
            self.camera.stop()
            print("System shutdown complete")


def main():
    """Main entry point for hardware-integrated system"""
    import argparse
    
    parser = argparse.ArgumentParser(
        description='Hardware-Integrated Perception System for Raspberry Pi 3'
    )
    parser.add_argument('--model', type=str, default='yolov8s-world.pt',
                       help='Path to YOLO-World model (default: yolov8s-world.pt)')
    parser.add_argument('--button-pin', type=int, default=5,
                       help='GPIO pin for control button (default: 5)')
    parser.add_argument('--left-motor', type=int, default=17,
                       help='GPIO pin for left motor (default: 17)')
    parser.add_argument('--right-motor', type=int, default=18,
                       help='GPIO pin for right motor (default: 18)')
    parser.add_argument('--camera', type=int, default=0,
                       help='Camera device ID (default: 0)')
    parser.add_argument('--simulate', action='store_true',
                       help='Force simulation mode (for testing without hardware)')
    
    args = parser.parse_args()
    
    # Create and run system
    system = HardwareIntegratedSystem(
        model_path=args.model,
        button_pin=args.button_pin,
        left_motor_pin=args.left_motor,
        right_motor_pin=args.right_motor,
        camera_id=args.camera,
        simulation_mode=args.simulate
    )
    
    system.run()


if __name__ == '__main__':
    main()
