#!/usr/bin/env python3
"""
Real YOLO Door Detection Test
Tests actual inference latency of YOLOv8 for door detection
"""

import time
import torch
from ultralytics import YOLO
from PIL import Image
import numpy as np
import json
from pathlib import Path
from typing import Dict, List


class YOLODoorDetector:
    def __init__(self, model_size: str = "s"):
        """
        Initialize YOLO model
        
        Args:
            model_size: 'n' (nano), 's' (small), 'm' (medium), 'l' (large), 'x' (xlarge)
                       For Pi 5: 'n' or 's' recommended
        """
        print(f"Loading YOLOv8{model_size}...")
        load_start = time.time()
        
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        print(f"Using device: {self.device}")
        
        # Load YOLO model
        self.model = YOLO(f'yolov8{model_size}.pt')
        
        # Door class ID in COCO dataset (62 = door)
        self.door_class_id = 62
        
        load_time = time.time() - load_start
        print(f"Model loaded in {load_time:.2f} seconds")
        print(f"Model size: yolov8{model_size}")
        print()
        
    def detect_door_position(self, image_path: str, conf_threshold: float = 0.3) -> Dict:
        """
        Detect door position using YOLO
        Returns: dict with 'direction', 'inference_time', 'confidence', 'bbox'
        """
        # Load image
        image = Image.open(image_path).convert("RGB")
        img_width = image.width
        
        # Start timing inference
        start_time = time.time()
        
        # Run inference
        results = self.model(image, conf=conf_threshold, verbose=False)
        
        inference_time = time.time() - start_time
        
        # Parse results
        direction = None
        best_door = None
        best_conf = 0
        
        for result in results:
            boxes = result.boxes
            for box in boxes:
                cls_id = int(box.cls[0])
                conf = float(box.conf[0])
                
                # Check if it's a door
                if cls_id == self.door_class_id and conf > best_conf:
                    best_conf = conf
                    xyxy = box.xyxy[0].cpu().numpy()
                    x1, y1, x2, y2 = xyxy
                    
                    # Calculate center of bounding box
                    center_x = (x1 + x2) / 2
                    
                    # Determine position (left, middle, right)
                    # Divide image into thirds
                    left_third = img_width / 3
                    right_third = 2 * img_width / 3
                    
                    if center_x < left_third:
                        direction = "Left"
                    elif center_x > right_third:
                        direction = "Right"
                    else:
                        direction = "Middle"
                    
                    best_door = {
                        "bbox": [float(x1), float(y1), float(x2), float(y2)],
                        "center_x": float(center_x),
                        "confidence": conf
                    }
        
        return {
            "direction": direction,
            "inference_time": inference_time,
            "confidence": best_conf if best_door else 0.0,
            "bbox": best_door["bbox"] if best_door else None,
            "detected": best_door is not None
        }


def run_yolo_latency_tests(image_paths: List[str], model_sizes: List[str] = ["n", "s"], num_runs: int = 10):
    """Run multiple latency tests with different YOLO models"""
    print("="*70)
    print("YOLO REAL-TIME DOOR DETECTION LATENCY TEST")
    print("="*70)
    print()
    
    all_results = {}
    
    for model_size in model_sizes:
        print(f"\n{'='*70}")
        print(f"Testing YOLOv8{model_size}")
        print(f"{'='*70}\n")
        
        detector = YOLODoorDetector(model_size=model_size)
        model_results = []
        
        for image_path in image_paths:
            print(f"\nTesting with image: {Path(image_path).name}")
            print("-"*70)
            
            image_results = []
            
            # Warmup run (models are slower on first inference)
            print("Warmup run...", end=" ", flush=True)
            _ = detector.detect_door_position(image_path)
            print("done")
            
            # Actual test runs
            for run in range(num_runs):
                print(f"Run {run + 1}/{num_runs}...", end=" ", flush=True)
                
                result = detector.detect_door_position(image_path)
                image_results.append(result)
                model_results.append(result)
                
                if result['detected']:
                    print(f"Direction: {result['direction']}, "
                          f"Conf: {result['confidence']:.2f}, "
                          f"Time: {result['inference_time']:.3f}s")
                else:
                    print(f"No door detected, Time: {result['inference_time']:.3f}s")
            
            # Statistics for this image
            times = [r['inference_time'] for r in image_results]
            avg_time = sum(times) / len(times)
            min_time = min(times)
            max_time = max(times)
            
            print(f"\nStatistics for {Path(image_path).name}:")
            print(f"  Average: {avg_time:.3f}s ({1/avg_time:.1f} FPS)")
            print(f"  Min: {min_time:.3f}s ({1/min_time:.1f} FPS)")
            print(f"  Max: {max_time:.3f}s ({1/max_time:.1f} FPS)")
        
        # Overall statistics for this model
        all_times = [r['inference_time'] for r in model_results]
        overall_avg = sum(all_times) / len(all_times)
        overall_min = min(all_times)
        overall_max = max(all_times)
        
        all_results[f"yolov8{model_size}"] = {
            "average": overall_avg,
            "min": overall_min,
            "max": overall_max,
            "fps": 1 / overall_avg
        }
        
        print(f"\n{'='*70}")
        print(f"YOLOv8{model_size} Overall Statistics")
        print(f"{'='*70}")
        print(f"Average latency: {overall_avg:.3f}s ({1/overall_avg:.1f} FPS)")
        print(f"Min latency: {overall_min:.3f}s")
        print(f"Max latency: {overall_max:.3f}s")
        
        # Real-world implications
        walking_speed = 1.4  # m/s
        distance_avg = overall_avg * walking_speed
        
        print(f"\nAt normal walking speed (1.4 m/s):")
        print(f"  Distance traveled: {distance_avg:.2f}m")
        
        if distance_avg < 0.5:
            safety = "✓ SAFE for real-time navigation"
        elif distance_avg < 1.0:
            safety = "⚠ MARGINAL - borderline acceptable"
        else:
            safety = "✗ UNSAFE - too slow"
        
        print(f"  Safety assessment: {safety}")
    
    # Compare all models
    if len(model_sizes) > 1:
        print(f"\n{'='*70}")
        print("MODEL COMPARISON")
        print(f"{'='*70}\n")
        print(f"{'Model':<15} {'Avg Latency':<15} {'FPS':<10} {'Distance @1.4m/s':<20}")
        print("-"*70)
        
        for model, stats in all_results.items():
            distance = stats['average'] * 1.4
            print(f"{model:<15} {stats['average']:.3f}s{'':<8} {stats['fps']:.1f}{'':<6} {distance:.2f}m")
    
    # Save results
    results_file = "yolo_latency_results.json"
    with open(results_file, 'w') as f:
        json.dump(all_results, f, indent=2)
    
    print(f"\nResults saved to {results_file}")
    
    return all_results


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python test_yolo_detection.py <image_path1> [image_path2] ...")
        print("\nExample:")
        print("  python test_yolo_detection.py test_images/door_left.jpg")
        print("\nYou can also test different model sizes:")
        print("  python test_yolo_detection.py test_images/*.jpg")
        sys.exit(1)
    
    image_paths = sys.argv[1:]
    
    # Verify images exist
    for img_path in image_paths:
        if not Path(img_path).exists():
            print(f"Error: Image not found: {img_path}")
            sys.exit(1)
    
    # Test nano and small models (best for Pi 5)
    run_yolo_latency_tests(image_paths, model_sizes=["n", "s"], num_runs=10)
