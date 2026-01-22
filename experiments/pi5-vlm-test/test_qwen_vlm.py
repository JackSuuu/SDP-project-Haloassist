#!/usr/bin/env python3
"""
Qwen 2B VLM Door Detection Test - 50 runs with warmup analysis
Goal: Detect if there's a door in the middle of the image
"""

import time
import torch
from transformers import Qwen2VLForConditionalGeneration, AutoProcessor
from PIL import Image
import json
from pathlib import Path
from typing import Dict, List
import signal
from contextlib import contextmanager
import sys


class TimeoutException(Exception): 
    pass


@contextmanager
def time_limit(seconds):
    """Context manager to timeout long-running operations"""
    def signal_handler(signum, frame):
        raise TimeoutException("Timed out!")
    signal.signal(signal.SIGALRM, signal_handler)
    signal.alarm(seconds)
    try:
        yield
    finally:
        signal.alarm(0)


class QwenDoorDetector:
    def __init__(self, model_name: str = "Qwen/Qwen2-VL-2B-Instruct"):
        """Initialize Qwen VLM model"""
        print(f"Loading {model_name}...")
        load_start = time.time()
        
        # Try MPS (Apple Silicon GPU) first, then CUDA, then CPU
        if torch.backends.mps.is_available():
            self.device = "mps"
        elif torch.cuda.is_available():
            self.device = "cuda"
        else:
            self.device = "cpu"
        
        print(f"Using device: {self.device}")
        
        # Load processor and model with optimizations
        self.processor = AutoProcessor.from_pretrained(model_name)
        
        # For MPS, we need to be careful with memory - use CPU if MPS causes issues
        try:
            self.model = Qwen2VLForConditionalGeneration.from_pretrained(
                model_name,
                torch_dtype=torch.float16 if self.device != "cpu" else torch.float32,
                device_map="auto" if self.device == "cuda" else None,
                low_cpu_mem_usage=True
            )
            if self.device == "mps":
                self.model = self.model.to(self.device)
        except Exception as e:
            print(f"Warning: Failed to load on {self.device}, falling back to CPU: {e}")
            self.device = "cpu"
            self.model = Qwen2VLForConditionalGeneration.from_pretrained(
                model_name,
                torch_dtype=torch.float32,
                low_cpu_mem_usage=True
            )
        
        load_time = time.time() - load_start
        print(f"Model loaded in {load_time:.2f} seconds")
        print()
        
    def detect_door_position(self, image_path: str, timeout_seconds: int = 30, max_image_size: int = 512) -> Dict:
        """
        Detect door position using VLM with timeout
        Returns: dict with 'direction', 'inference_time', and 'raw_output'
        """
        # Load image and resize to avoid OOM
        image = Image.open(image_path).convert("RGB")
        
        # Resize if too large (prevents MPS memory issues)
        if max(image.size) > max_image_size:
            ratio = max_image_size / max(image.size)
            new_size = (int(image.width * ratio), int(image.height * ratio))
            image = image.resize(new_size, Image.Resampling.LANCZOS)
            print(f"[Resized to {new_size}]", end=" ")
        
        # Prompt optimized for door detection - asking about middle position
        prompt = "Describe what is in the image"
        
        # Create conversation format
        conversation = [
            {
                "role": "user",
                "content": [
                    {"type": "image", "image": image},
                    {"type": "text", "text": prompt}
                ]
            }
        ]
        
        # Prepare inputs
        text = self.processor.apply_chat_template(
            conversation, add_generation_prompt=True
        )
        
        inputs = self.processor(
            text=[text],
            images=[image],
            padding=True,
            return_tensors="pt"
        ).to(self.device)
        
        # Start timing inference with timeout
        try:
            with time_limit(timeout_seconds):
                start_time = time.time()
                
                # Generate response
                with torch.inference_mode():
                    output_ids = self.model.generate(
                        **inputs,
                        max_new_tokens=30,  # Only need 1-2 words
                        do_sample=False,  # Deterministic for faster inference
                    )
                
                # Decode output
                generated_ids = [
                    output_ids[len(input_ids):]
                    for input_ids, output_ids in zip(inputs.input_ids, output_ids)
                ]
                output_text = self.processor.batch_decode(
                    generated_ids, skip_special_tokens=True, clean_up_tokenization_spaces=True
                )[0]
                
                inference_time = time.time() - start_time
                
        except TimeoutException:
            inference_time = timeout_seconds
            output_text = f"TIMEOUT (>{timeout_seconds}s)"
        
        # Parse direction from output
        output_lower = output_text.strip().lower()
        direction = None
        
        if "left" in output_lower:
            direction = "Left"
        elif "right" in output_lower:
            direction = "Right"
        elif "middle" in output_lower or "center" in output_lower:
            direction = "Middle"
        elif "none" in output_lower or "no" in output_lower:
            direction = "No door"
        
        return {
            "direction": direction,
            "inference_time": inference_time,
            "raw_output": output_text
        }


def run_latency_tests(image_paths: List[str], num_runs: int = 50, timeout: int = 30):
    """Run multiple latency tests and report statistics"""
    print("="*60)
    print(f"QWEN 2B VLM DOOR DETECTION - {num_runs} RUNS")
    print("="*60)
    print()
    
    # Initialize detector
    detector = QwenDoorDetector()
    
    all_results = []
    warmup_times = []
    inference_times = []
    
    for image_path in image_paths:
        print(f"\nTest image: {Path(image_path).name}")
        print("-"*60)
        
        image_results = []
        
        # Warmup runs (first 3)
        print("\nWarmup phase (first 3 runs, model loading and caching):")
        for run in range(min(3, num_runs)):
            print(f"Warmup {run + 1}/3...", end=" ", flush=True)
            
            result = detector.detect_door_position(image_path, timeout_seconds=timeout, max_image_size=384)
            warmup_times.append(result['inference_time'])
            
            print(f"Direction: {result['direction']}, "
                  f"Time: {result['inference_time']:.3f}s")
            print(f"  Full output: {result['raw_output']}")
        
        # Actual inference test (remaining runs)
        print(f"\nInference test (remaining {num_runs-3} runs):")
        for run in range(3, num_runs):
            if run % 10 == 0:
                print(f"\nProgress: {run}/{num_runs}")
            
            print(f"Run {run + 1}/{num_runs}...", end=" ", flush=True)
            
            result = detector.detect_door_position(image_path, timeout_seconds=timeout, max_image_size=384)
            image_results.append(result)
            all_results.append(result)
            inference_times.append(result['inference_time'])
            
            # Show full output
            if result['inference_time'] < timeout:
                print(f"Time: {result['inference_time']:.3f}s, Direction: {result['direction']}")
                print(f"  Full output: {result['raw_output']}")
            else:
                print(f"TIMEOUT")
        
        print()  # newline
        
        # Calculate statistics - warmup vs actual inference
        if warmup_times:
            warmup_avg = sum(warmup_times) / len(warmup_times)
            print(f"\nWarmup statistics (first {len(warmup_times)} runs):")
            print(f"  Average: {warmup_avg:.3f}s")
            print(f"  Min: {min(warmup_times):.3f}s")
            print(f"  Max: {max(warmup_times):.3f}s")
        
        if inference_times:
            inference_avg = sum(inference_times) / len(inference_times)
            inference_min = min(inference_times)
            inference_max = max(inference_times)
            
            print(f"\nInference statistics (remaining {len(inference_times)} runs):")
            print(f"  Average: {inference_avg:.3f}s")
            print(f"  Min: {inference_min:.3f}s")
            print(f"  Max: {inference_max:.3f}s")
            print(f"  Range: {inference_max - inference_min:.3f}s")
            
            # Speedup after warmup
            if warmup_times:
                speedup = warmup_avg / inference_avg
                print(f"  Speedup: {speedup:.2f}x (vs warmup)")
            
            # FPS
            fps = 1 / inference_avg if inference_avg > 0 else 0
            print(f"  FPS: {fps:.2f}")
    
    # Overall statistics
    print("\n" + "="*60)
    print("OVERALL STATISTICS")
    print("="*60)
    
    if warmup_times:
        print(f"\nWarmup phase ({len(warmup_times)} runs):")
        print(f"  Average latency: {sum(warmup_times)/len(warmup_times):.3f}s")
    
    if inference_times:
        overall_avg = sum(inference_times) / len(inference_times)
        overall_min = min(inference_times)
        overall_max = max(inference_times)
        
        print(f"\nStable inference ({len(inference_times)} runs):")
        print(f"  Average latency: {overall_avg:.3f}s")
        print(f"  Min latency: {overall_min:.3f}s")
        print(f"  Max latency: {overall_max:.3f}s")
        print(f"  Std dev: {(sum((t - overall_avg)**2 for t in inference_times) / len(inference_times))**0.5:.3f}s")
        print(f"  FPS: {1/overall_avg:.2f}")
        
        # Real-world implications
        print("\n" + "="*60)
        print("REAL-WORLD NAVIGATION IMPACT")
        print("="*60)
        
        walking_speeds = {
            "Slow walking": 0.5,  # m/s
            "Normal walking": 1.4,  # m/s
            "Fast walking": 2.0,   # m/s
        }
        
        for speed_name, speed_ms in walking_speeds.items():
            distance_avg = overall_avg * speed_ms
            distance_min = overall_min * speed_ms
            distance_max = overall_max * speed_ms
            print(f"\n{speed_name} ({speed_ms} m/s):")
            print(f"  Avg inference distance: {distance_avg:.2f}m")
            print(f"  Best case distance: {distance_min:.2f}m")
            print(f"  Worst case distance: {distance_max:.2f}m")
            
            # Safety assessment
            if distance_avg < 0.5:
                print(f"  Assessment: ✓ SAFE - suitable for real-time navigation")
            elif distance_avg < 1.0:
                print(f"  Assessment: ⚠ MARGINAL - borderline acceptable")
            else:
                print(f"  Assessment: ✗ UNSAFE - too slow for real-time navigation")
        
        # Detection results summary
        print("\n" + "="*60)
        print("DETECTION RESULTS")
        print("="*60)
        
        direction_counts = {}
        for r in all_results:
            d = r['direction'] or "Unknown"
            direction_counts[d] = direction_counts.get(d, 0) + 1
        
        print(f"\nDirection distribution across {len(all_results)} runs:")
        for direction, count in sorted(direction_counts.items(), key=lambda x: -x[1]):
            pct = count / len(all_results) * 100
            print(f"  {direction}: {count} ({pct:.1f}%)")
        
        # Save results to JSON
        results_file = "qwen_latency_results.json"
        with open(results_file, 'w') as f:
            json.dump({
                "warmup_times": warmup_times,
                "inference_times": inference_times,
                "all_results": [{"time": r['inference_time'], "direction": r['direction'], "output": r['raw_output']} for r in all_results],
                "statistics": {
                    "warmup_avg": sum(warmup_times)/len(warmup_times) if warmup_times else 0,
                    "inference_avg": overall_avg if inference_times else 0,
                    "inference_min": overall_min if inference_times else 0,
                    "inference_max": overall_max if inference_times else 0,
                    "total_tests": len(all_results),
                    "num_warmup": len(warmup_times),
                    "num_inference": len(inference_times),
                    "direction_counts": direction_counts
                }
            }, f, indent=2, ensure_ascii=False)
        
        print(f"\nResults saved to {results_file}")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python test_qwen_vlm.py <image_path> [num_runs]")
        print("\nExamples:")
        print("  python test_qwen_vlm.py test_images/test.jpg 50")
        print("  python test_qwen_vlm.py test_images/test.jpg")
        sys.exit(1)
    
    image_paths = [sys.argv[1]]
    num_runs = int(sys.argv[2]) if len(sys.argv) > 2 else 50
    
    # Verify images exist
    for img_path in image_paths:
        if not Path(img_path).exists():
            print(f"Error: Image not found: {img_path}")
            sys.exit(1)
    
    print(f"Running {num_runs} tests (first 3 warmup, remaining {num_runs-3} actual inference)")
    print()
    
    run_latency_tests(image_paths, num_runs=num_runs, timeout=30)
