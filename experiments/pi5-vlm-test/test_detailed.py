#!/usr/bin/env python3
"""
Quick test with detailed prompt to understand door position detection
"""

import time
import torch
from transformers import Qwen2VLForConditionalGeneration, AutoProcessor
from PIL import Image
import sys

def test_detailed_output(image_path: str):
    print("="*60)
    print("DETAILED DOOR DETECTION TEST")
    print("="*60)
    
    # Load model
    print("\nLoading Qwen2-VL-2B...")
    device = "mps" if torch.backends.mps.is_available() else "cpu"
    print(f"Device: {device}")
    
    processor = AutoProcessor.from_pretrained("Qwen/Qwen2-VL-2B-Instruct")
    model = Qwen2VLForConditionalGeneration.from_pretrained(
        "Qwen/Qwen2-VL-2B-Instruct",
        torch_dtype=torch.float16 if device != "cpu" else torch.float32,
        low_cpu_mem_usage=True
    )
    if device == "mps":
        model = model.to(device)
    
    print("Model loaded!\n")
    
    # Load and resize image
    image = Image.open(image_path).convert("RGB")
    max_size = 384
    if max(image.size) > max_size:
        ratio = max_size / max(image.size)
        new_size = (int(image.width * ratio), int(image.height * ratio))
        image = image.resize(new_size, Image.Resampling.LANCZOS)
        print(f"Image resized to: {new_size}")
    
    # Different prompts to test
    prompts = [
        # Simple direction
        "Is there a door in this image? Answer with only: Left, Middle, Right, or None.",
        
        # Detailed description
        "Describe where the door is located in this image. Is it on the left side, middle/center, or right side? Explain briefly.",
        
        # Specific question about middle
        "Look at this image carefully. Is there a door in the CENTER/MIDDLE of the image? Answer yes or no and explain.",
        
        # Ask for coordinates
        "If there is a door in this image, describe its position. What percentage of the image width does the door occupy, and where is its center?",
    ]
    
    for i, prompt in enumerate(prompts):
        print(f"\n{'='*60}")
        print(f"Test {i+1}: {prompt[:60]}...")
        print("="*60)
        
        conversation = [
            {
                "role": "user",
                "content": [
                    {"type": "image", "image": image},
                    {"type": "text", "text": prompt}
                ]
            }
        ]
        
        text = processor.apply_chat_template(conversation, add_generation_prompt=True)
        inputs = processor(text=[text], images=[image], padding=True, return_tensors="pt").to(device)
        
        start = time.time()
        with torch.inference_mode():
            output_ids = model.generate(**inputs, max_new_tokens=150, do_sample=False)
        latency = time.time() - start
        
        generated_ids = [output_ids[len(input_ids):] for input_ids, output_ids in zip(inputs.input_ids, output_ids)]
        output = processor.batch_decode(generated_ids, skip_special_tokens=True)[0]
        
        print(f"\nLatency: {latency:.3f}s")
        print(f"Output:\n{output}")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python test_detailed.py <image_path>")
        sys.exit(1)
    
    test_detailed_output(sys.argv[1])
