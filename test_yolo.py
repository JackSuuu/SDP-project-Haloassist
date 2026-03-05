#!/usr/bin/env python3
"""
Universal YOLO Tester (Standard & World)
- Supports both Standard YOLOv8 (COCO) and YOLO-World models.
- Logs detailed timing stats (preprocess, inference, postprocess) per image.
- Consolidates results into a detailed JSON.
"""

import time
import json
from pathlib import Path
from typing import Dict, List, Union
import torch
from ultralytics import YOLO, YOLOE
from PIL import Image
import numpy as np

class YOLOTester:
    def __init__(self, model_path: str = None):
        """
        Initialize YOLO model (Standard or World)
        """
        print("="*60)
        print("Universal YOLO Model Tester")
        print("="*60 + "\n")
        
        # 1. Determine Model Path
        if model_path is None:
            # Default to standard yolov8s.pt
            return -1
            # Un-comment to default to World:
            # model_path = "yolov8s-world.pt"
        
        self.model_path = model_path
        
        # 2. Detect Model Type
        # Heuristic: Check if "world" is in the filename to enable World-specific features
        self.is_open = "world" in Path(model_path).name.lower() or "yoloe" in Path(model_path).name.lower()
        model_type = "YOLO-Open" if self.is_open else "Standard YOLO 26 (COCO)"
        
        print(f"Loading Model: {model_path}")
        print(f"Detected Type: {model_type}")

        load_start = time.time()
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        print(f"Using device:  {self.device}\n")
        
        # 3. Load Model
        try:
            self.model = YOLO(model_path)
            self.model.to(self.device)
        except Exception as e:
            self.model = YOLOE(model_path)
            self.model.to(self.device)

        load_time = time.time() - load_start
        print(f"Model loaded in {load_time:.2f} seconds\n")
        
    def detect_objects(self, image_paths: List[str], classes: List[str] = None, 
                       conf_threshold: float = 0.25, output_dir: str = "output_results") -> Dict: 
        """
        Detect objects in a list of images.
        - If Standard YOLO: filters results using COCO indices.
        - If YOLO-World: sets custom classes via set_classes().
        """
        # Validate paths
        valid_paths = [str(p) for p in image_paths if Path(p).exists()]
        if not valid_paths:
            raise FileNotFoundError("No valid image paths provided.")

        # Ensure output directory exists
        out_path = Path(output_dir)
        out_path.mkdir(parents=True, exist_ok=True)

        # --- CLASS HANDLING LOGIC ---
        predict_kwargs = {}
        
        if classes:
            if self.is_open:
                # YOLO-Open: We set the custom vocabulary directly
                print(f"YOLO-Open: Setting custom classes to {classes}")
                # Note: Ultralytics 'set_classes' persists on the model object
                self.model.set_classes(classes)
                # We do NOT pass 'classes' filter to predict(), 
                # because the model itself is now restricted to these classes.
            else:
                # Standard YOLO: We must map strings to COCO indices
                print(f"Standard YOLO: Mapping classes to COCO indices...")
                name_to_id = {v: k for k, v in self.model.names.items()}
                target_indices = []
                for c in classes:
                    if c in name_to_id:
                        target_indices.append(name_to_id[c])
                    else:
                        print(f"  Warning: '{c}' not in COCO dataset. Ignoring.")
                
                if target_indices:
                    print(f"  Filtering for indices: {target_indices}")
                    predict_kwargs['classes'] = target_indices
                else:
                    print("  Warning: No valid COCO classes found. detecting ALL classes.")

        print(f"Processing {len(valid_paths)} images...")

        # --- RUN INFERENCE ---
        # Note: 'stream=False' ensures we get a list of Results immediately
        results_list = self.model.predict(
            source=valid_paths, 
            conf=conf_threshold, 
            verbose=False,
            device=self.device,
            stream=False,
            **predict_kwargs
        )
        
        # --- PROCESS RESULTS & STATS ---
        consolidated_results = []
        total_inference_time = 0.0

        print("\nProcessing results and saving images...")

        for i, result in enumerate(results_list):
            original_path = Path(valid_paths[i])
            boxes = result.boxes
            
            # 1. Extract Timing Stats (ms)
            # Result.speed returns {'preprocess': float, 'inference': float, 'postprocess': float}
            timings = result.speed
            # Calculate total time per image
            image_total_time = sum(timings.values())
            total_inference_time += timings['inference']

            # 2. Save Annotated Image
            annotated_frame = result.plot()
            annotated_image = Image.fromarray(annotated_frame[..., ::-1])
            output_filename = f"detected_{original_path.name}"
            output_image_path = out_path / output_filename
            annotated_image.save(output_image_path)
            
            # 3. Extract Detections
            image_detections = []
            if len(boxes) > 0:
                for box in boxes:
                    class_id = int(box.cls[0].item())
                    # Handle case where names might be missing (rare)
                    class_name = result.names[class_id] if result.names else str(class_id)
                    confidence = box.conf[0].item()
                    bbox = box.xyxy[0].cpu().numpy()
                    
                    image_detections.append({
                        "class": class_name,
                        "confidence": round(confidence, 4),
                        "bbox": [round(x, 2) for x in bbox.tolist()]
                    })

            # 4. Build Record
            consolidated_results.append({
                "image_name": original_path.name,
                "output_image": str(output_image_path),
                "stats": {
                    "num_detections": len(image_detections),
                    "image_size": result.orig_shape,  # (h, w)
                    "time_ms": {
                        "preprocess": round(timings.get('preprocess', 0), 2),
                        "inference": round(timings.get('inference', 0), 2),
                        "postprocess": round(timings.get('postprocess', 0), 2),
                        "total": round(image_total_time, 2)
                    }
                },
                "detections": image_detections
            })
            
            print(f"  -> {original_path.name}: {len(image_detections)} detections | Inf: {timings['inference']:.1f}ms")

        # --- FINAL SUMMARY JSON ---
        avg_inference = total_inference_time / len(valid_paths) if valid_paths else 0
        
        final_data = {
            "metadata": {
                "model_name": Path(self.model_path).name,
                "model_type": "YOLO-Open" if self.is_open else "Standard YOLO",
                "device": self.device,
                "classes_requested": classes,
                "conf_threshold": conf_threshold,
                "total_images": len(valid_paths),
                "avg_inference_time_ms": round(avg_inference, 2)
            },
            "results": consolidated_results
        }

        return final_data

    def print_summary(self, data: Dict):
        """Pretty print a summary of the batch results"""
        meta = data["metadata"]
        print("\n" + "="*60)
        print(f"BATCH SUMMARY: {meta['model_type']}")
        print("="*60)
        print(f"Model:        {meta['model_name']}")
        print(f"Avg Inf Time: {meta['avg_inference_time_ms']} ms / image")
        print(f"Total Images: {meta['total_images']}")
        print("-" * 60)
        
        for res in data["results"]:
            stats = res['stats']
            print(f"Img: {res['image_name']:<15} | Det: {stats['num_detections']:<3} | Time: {stats['time_ms']['total']:.1f}ms")
            
        print("="*60 + "\n")

    def save_results(self, results: Dict, output_path: str):
        with open(output_path, 'w') as f:
            json.dump(results, f, indent=2)
        print(f"Full JSON results saved to: {output_path}")

def main():
    # ==========================================
    # CONFIGURATION
    # ==========================================
    
    # TOGGLE THIS to switch between Open vocab and Standard
    USE_YOLO_Open = True  
    
    if USE_YOLO_Open:
        # 1. YOLO-Open Vocab Config
        model_file = "yoloe-26n-seg.pt" 
        # YOLO-Open can detect anything you type
        target_classes = ["books"]
        conf_thresh = 0.02 # World models often need lower thresholds
        output_folder = "output_yolo_open"
        json_file = "results_open.json"
    else:
        # 2. Standard YOLO Config
        model_file = "yolo26n.pt"
        # Standard YOLO only supports COCO classes (e.g., 'chair', not 'gray seat')
        target_classes = ["chair", "person", "laptop"] 
        conf_thresh = 0.25
        output_folder = "output_yolo_standard"
        json_file = "results_standard.json"

    # ==========================================
    # EXECUTION
    # ==========================================

    # 1. Initialize Tester
    # Pass the model path. If it contains "yoloe", the class adapts automatically.
    tester = YOLOTester(model_path=model_file)
    
    # 2. Setup Images
    base_path = Path(__file__).parent / "test_images"
    image_list = []
    for i in range(1, 13):
        # Check for both jpg and jpeg
        for ext in [".jpeg", ".jpg", ".png"]:
            p = base_path / f"test{i}{ext}"
            if p.exists():
                image_list.append(str(p))
                break
    
    if not image_list:
        print(f"No images found in {base_path}. Please add test1.jpg, test2.jpg, etc.")
        return

    # 3. Run Detection
    results = tester.detect_objects(
        image_paths=image_list, 
        classes=target_classes, 
        conf_threshold=conf_thresh, 
        output_dir=output_folder
    )

    # 4. Save & Print
    tester.print_summary(results)
    tester.save_results(results, json_file)

if __name__ == "__main__":
    main()