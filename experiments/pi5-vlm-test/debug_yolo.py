#!/usr/bin/env python3
"""
Debug YOLO detections - see what objects are actually detected
"""

from ultralytics import YOLO
from PIL import Image
import sys

def debug_detections(image_path: str):
    print("="*70)
    print("YOLO DETECTION DEBUGGER")
    print("="*70)
    print()
    
    # Load model
    print("Loading YOLOv8n...")
    model = YOLO('yolov8n.pt')
    
    # Load image
    image = Image.open(image_path).convert("RGB")
    print(f"Image size: {image.width}x{image.height}")
    print()
    
    # Run detection with very low confidence
    print("Running detection with confidence threshold 0.1...")
    results = model(image, conf=0.1, verbose=False)
    
    print()
    print("="*70)
    print("ALL DETECTED OBJECTS")
    print("="*70)
    print()
    
    detected_count = 0
    
    for result in results:
        boxes = result.boxes
        
        if len(boxes) == 0:
            print("❌ No objects detected at all!")
            print()
            print("Possible reasons:")
            print("  1. Image might be too dark/blurry")
            print("  2. Objects not in COCO dataset")
            print("  3. Objects too small or unusual angle")
            return
        
        print(f"Found {len(boxes)} objects:\n")
        
        for i, box in enumerate(boxes):
            cls_id = int(box.cls[0])
            conf = float(box.conf[0])
            class_name = model.names[cls_id]
            xyxy = box.xyxy[0].cpu().numpy()
            x1, y1, x2, y2 = xyxy
            
            detected_count += 1
            
            # Calculate center and size
            center_x = (x1 + x2) / 2
            center_y = (y1 + y2) / 2
            width = x2 - x1
            height = y2 - y1
            
            # Determine position
            img_width = image.width
            left_third = img_width / 3
            right_third = 2 * img_width / 3
            
            if center_x < left_third:
                position = "Left"
            elif center_x > right_third:
                position = "Right"
            else:
                position = "Middle"
            
            print(f"{i+1}. {class_name.upper()} (class_id: {cls_id})")
            print(f"   Confidence: {conf:.3f}")
            print(f"   Position: {position}")
            print(f"   Bounding box: [{x1:.0f}, {y1:.0f}, {x2:.0f}, {y2:.0f}]")
            print(f"   Size: {width:.0f}x{height:.0f} pixels")
            print()
    
    print("="*70)
    print("DOOR-SPECIFIC CHECK")
    print("="*70)
    print()
    print(f"COCO 'door' class ID: 62")
    print()
    
    door_found = False
    for result in results:
        for box in result.boxes:
            if int(box.cls[0]) == 62:
                door_found = True
                conf = float(box.conf[0])
                print(f"✓ Door detected with confidence {conf:.3f}")
                
                if conf < 0.3:
                    print(f"  ⚠ Confidence {conf:.3f} is below default threshold (0.3)")
                    print(f"  Try: python test_yolo_detection.py {image_path} --conf 0.1")
    
    if not door_found:
        print("❌ No 'door' (class 62) detected")
        print()
        print("The detected objects above might include your door, but YOLO")
        print("classified it differently. Common alternatives:")
        print("  - It might be detected as part of a larger scene")
        print("  - COCO 'door' is trained on specific door types")
        print("  - Indoor doors might not match COCO training data")
        print()
        print("SOLUTION: Use a door-specific trained model or fine-tune YOLO")
        print("          on your specific door images")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python debug_yolo.py <image_path>")
        sys.exit(1)
    
    debug_detections(sys.argv[1])
