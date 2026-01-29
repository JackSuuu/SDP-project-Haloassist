#!/usr/bin/env python3
"""
YOLO World Model Test - Batch Processing
Tests YOLOv8-World model on a list of images and consolidates results.
"""

import time
import json
from pathlib import Path
from typing import Dict, List
import torch
from ultralytics import YOLOWorld
from PIL import Image

class YOLOWorldTester:
    def __init__(self, model_path: str = None):
        """
        Initialize YOLO World model
        """
        print("="*60)
        print("YOLO World Model Tester (Batch Mode)")
        print("="*60 + "\n")
        
        if model_path is None:
            # Try to find the model in the perception directory
            perception_dir = Path(__file__).parent.parent.parent / "perception" / "yolov8s-world.pt"
            model_path = str(perception_dir)
        
        print(f"Loading YOLOv8 World model from: {model_path}")

        load_start = time.time()
        # Explicitly define device
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        print(f"Using device: {self.device}\n")
        
        # Load YOLO World model
        try:
            self.model = YOLOWorld(model_path)
            # Explicitly move model to device
            self.model.to(self.device)
        except Exception as e:
            print(f"Error loading model: {e}")
            raise

        load_time = time.time() - load_start
        print(f"Model loaded in {load_time:.2f} seconds\n")
        
    def detect_objects(self, image_paths: List[str], classes: List[str] = None, 
                       conf_threshold: float = 0.15, output_dir: str = "output_results") -> Dict: 
        """
        Detect objects in a list of images, save annotated versions, 
        and return a consolidated dictionary of results.
        """
        # Validate paths
        valid_paths = []
        for p in image_paths:
            if Path(p).exists():
                valid_paths.append(str(p))
            else:
                print(f"Warning: Image not found at {p}, skipping.")
        
        if not valid_paths:
            raise FileNotFoundError("No valid image paths provided.")

        # Ensure output directory exists
        out_path = Path(output_dir)
        out_path.mkdir(parents=True, exist_ok=True)

        if not classes:
            classes = ['person', 'chair', 'table', 'door', 'window']
        
        self.model.set_classes(classes)
        print(f"Processing {len(valid_paths)} images with classes: {classes}...")

        # Run Batch Inference
        # Passing a list to predict() is more efficient than a loop
        inference_start = time.time()
        results_list = self.model.predict(
            source=valid_paths, 
            conf=conf_threshold, 
            verbose=False,
            device=self.device,
            stream=False # Ensure we get a list back, not a generator
        )
        total_inference_time = (time.time() - inference_start) * 1000  
        
        # Prepare Consolidated Results
        consolidated_data = {
            "summary": {
                "total_images": len(valid_paths),
                "total_inference_time_ms": round(total_inference_time, 2),
                "classes_searched": classes,
                "conf_threshold": conf_threshold
            },
            "results": []
        }

        print("\nProcessing results and saving images...")

        # Iterate through results (Ultralytics preserves order matches input list)
        for i, result in enumerate(results_list):
            original_path = Path(valid_paths[i])
            boxes = result.boxes
            
            # 1. Save Annotated Image
            annotated_frame = result.plot()
            annotated_image = Image.fromarray(annotated_frame[..., ::-1])
            
            # Create output filename: "detected_filename.jpg"
            output_filename = f"detected_{original_path.name}"
            output_image_path = out_path / output_filename
            annotated_image.save(output_image_path)
            
            # 2. Extract Detection Data
            image_detections = []
            detection_counter = 0
            
            if len(boxes) > 0:
                for box in boxes:
                    detection_counter += 1
                    class_id = int(box.cls[0].item())
                    class_name = result.names[class_id]
                    confidence = box.conf[0].item()
                    bbox = box.xyxy[0].cpu().numpy()
                    
                    image_detections.append({
                        "detection_id": detection_counter,
                        "class": class_name,
                        "confidence": round(confidence, 4),
                        "bbox": {
                            "x_min": round(float(bbox[0]), 2),
                            "y_min": round(float(bbox[1]), 2),
                            "x_max": round(float(bbox[2]), 2),
                            "y_max": round(float(bbox[3]), 2)
                        }
                    })

            # Add to consolidated list
            consolidated_data["results"].append({
                "image_name": original_path.name,
                "output_image": str(output_image_path),
                "num_detections": detection_counter,
                "detections": image_detections
            })
            
            print(f"  -> Saved {output_filename} ({detection_counter} detections)")

        return consolidated_data

    def print_summary(self, results: Dict):
        """Pretty print a summary of the batch results"""
        summary = results["summary"]
        print("\n" + "="*60)
        print("BATCH PROCESSING SUMMARY")
        print("="*60)
        print(f"Total Images: {summary['total_images']}")
        print(f"Total Time:   {summary['total_inference_time_ms']:.2f} ms")
        print(f"Classes:      {summary['classes_searched']}")
        print("-" * 60)
        
        for img_res in results["results"]:
            print(f"Image: {img_res['image_name']:<20} | Detections: {img_res['num_detections']}")
            if img_res['num_detections'] > 0:
                # Print just the classes found for brevity
                classes_found = list(set(d['class'] for d in img_res['detections']))
                print(f"    Found: {classes_found}")
        print("="*60 + "\n")

    def save_results(self, results: Dict, output_path: str):
        with open(output_path, 'w') as f:
            json.dump(results, f, indent=2)
        print(f"Full JSON results saved to: {output_path}")

def main():
    tester = YOLOWorldTester()
    
    # 1. Setup list of images (test1.jpeg through test6.jpeg)
    base_path = Path(__file__).parent / "test_images"
    image_list = []
    
    # Generate paths for test1 through test6
    for i in range(1, 9):
        img_path = base_path / f"test{i}.jpeg" 
        # Note: If some are .jpg and others .jpeg, you might need a check here
        if not img_path.exists():
            # Fallback to try .jpg if .jpeg doesn't exist
            img_path = base_path / f"test{i}.jpg"
            
        if img_path.exists():
            image_list.append(str(img_path))
        else:
            print(f"Warning: Could not find test image {i}")

    if not image_list:
        print("No images found to process.")
        return

    # 2. Define Classes

    COCO_classes = ["person", "bicycle", "car", "motorcycle", "airplane", "bus", "train", "truck", "boat", "traffic light",
    "fire hydrant", "stop sign", "parking meter", "bench", "bird", "cat", "dog", "horse", "sheep", "cow",
    "elephant", "bear", "zebra", "giraffe", "backpack", "umbrella", "handbag", "tie", "suitcase", "frisbee",
    "skis", "snowboard", "sports ball", "kite", "baseball bat", "baseball glove", "skateboard", "surfboard", "tennis racket", "bottle",
    "wine glass", "cup", "fork", "knife", "spoon", "bowl", "banana", "apple", "sandwich", "orange",
    "broccoli", "carrot", "hot dog", "pizza", "donut", "cake", "chair", "couch", "potted plant", "bed",
    "dining table", "toilet", "tv", "laptop", "mouse", "remote", "keyboard", "cell phone", "microwave", "oven",
    "toaster", "sink", "refrigerator", "book", "clock", "vase", "scissors", "teddy bear", "hair drier", "toothbrush"]

    target_classes = ["gray seat"]

    # 3. Run Batch Detection
    print(f"\nStarting batch detection on {len(image_list)} images...")
    
    # We pass the list of images, and an output directory for the images
    batch_results = tester.detect_objects(
        image_paths=image_list, 
        classes=target_classes, 
        conf_threshold=0.04, 
        output_dir="batch_output_images"
    )

    # 4. Print and Save
    tester.print_summary(batch_results)
    tester.save_results(batch_results, "yolo_world_batch_results.json")
    
    print("\nTest completed!")

if __name__ == "__main__":
    main()