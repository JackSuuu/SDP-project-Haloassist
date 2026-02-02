"""
Main application entry point
Integrates detection, guidance, and haptic feedback
"""
import cv2
import time
import argparse
from perception.detector import ObjectDetector
from feedback.haptic_legacy import HapticFeedback
from perception.camera import CameraInterface


class PerceptionSystem:
    def __init__(self, model_path: str = 'yolov8s-world.pt', 
                 show_display: bool = True,
                 num_motors: int = 8):
        """
        Initialize perception system
        
        Args:
            model_path: Path to YOLO-World model
            show_display: Whether to show visual display (for testing)
            num_motors: Number of haptic motors
        """
        self.detector = ObjectDetector(model_path=model_path)
        self.haptic = HapticFeedback(num_motors=num_motors)
        self.camera = CameraInterface()
        self.show_display = show_display
        
        print("Perception System initialized")
        print(f"- YOLO model: {model_path}")
        print(f"- Haptic motors: {num_motors}")
        print(f"- Display mode: {show_display}")
    
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
                
                # Detect objects
                detections = self.detector.detect(frame)
                
                # Get target object for guidance
                target = self.detector.get_closest_object(detections, frame.shape[:2])
                
                # Provide haptic feedback
                if target is not None:
                    frame_center = (frame.shape[1] // 2, frame.shape[0] // 2)
                    
                    # Calculate distance score (0=far, 1=close)
                    cx, cy = target['center']
                    dist = ((cx - frame_center[0])**2 + (cy - frame_center[1])**2)**0.5
                    max_dist = (frame.shape[1]**2 + frame.shape[0]**2)**0.5 / 2
                    distance_score = 1.0 - min(dist / max_dist, 1.0)
                    
                    self.haptic.guide_to_target(target['center'], frame_center, distance_score)
                    
                    print(f"Target: {target['class']} at {target['center']} "
                          f"(conf: {target['confidence']:.2f}, dist: {distance_score:.2f})")
                
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
            self.camera.stop()
            self.haptic.cleanup()
            if self.show_display:
                cv2.destroyAllWindows()
            print("System stopped")


def main():
    parser = argparse.ArgumentParser(description='Perception System for Blind Assistance')
    parser.add_argument('--model', type=str, default='yolov8s-world.pt',
                       help='Path to YOLO-World model (default: yolov8s-world.pt)')
    parser.add_argument('--no-display', action='store_true',
                       help='Disable visual display')
    parser.add_argument('--motors', type=int, default=8,
                       help='Number of haptic motors (default: 8)')
    
    args = parser.parse_args()
    
    system = PerceptionSystem(
        model_path=args.model,
        show_display=not args.no_display,
        num_motors=args.motors
    )
    
    system.run()


if __name__ == '__main__':
    main()
