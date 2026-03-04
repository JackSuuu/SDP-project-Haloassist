"""
Test script for ImageUploadDetector
Tests detection on static images with custom classes
"""
import sys
from pathlib import Path

# Add src to path
src_path = Path(__file__).parent.parent / 'src'
sys.path.insert(0, str(src_path))

from image_detector import ImageUploadDetector

# Detect from image
test_image = Path(__file__).parent.parent / 'test_images' / 'chair4.jpg'


def test_experiment1_description_formats():
    """
    Experiment 1: Testing Different Description Formats

    Test image: chair4.jpg
    Expected contents: 2 white chairs (left and right) + 1 yellow chair (middle)
    Goal: Find which description format best helps YOLO-World detect similar objects
    """
    print("="*60)
    print("EXPERIMENT 1: Testing Different Description Formats")
    print("="*60)
    print("\nTest Image: chair4.jpg")
    print("Expected: 2 white chairs + 1 yellow chair")
    print("="*60)

    detector = ImageUploadDetector(model_path='../yolov8s-world.pt', conf_threshold=0.1)

    if not test_image.exists():
        print(f"\n✗ Test image not found: {test_image}\n")
        return

    # Category 1: Basic Color - Test Color Sensitivity
    # Test hypothesis: Is model more sensitive to yellow than white?
    basic_color = {
        "Category 1: Basic Color Contrast": [
            'yellow chair',           # Expected: only middle chair
            'white chair',            # Expected: left and right chairs
            'yellow office chair',    # Add category attribute to see if confidence increases
        ]
    }

    # Category 2: Positional Descriptions - Simulate Blind User Spatial Awareness
    # Blind users often use "middle", "beside" in their descriptions
    # Tests YOLO-World's understanding of relative position semantics
    positional_phrases = {
        "Category 2: Positional Descriptions": [
            'the chair in the middle',                  # The middle chair
            'the chair between two white chairs',       # Chair between two white chairs (high difficulty test)
            'the leftmost white chair',                 # Leftmost white chair
            'the rightmost office chair',               # Rightmost office chair
        ]
    }

    # Category 3: Detailed Attribute Combinations - Increase Distinguishability
    # If simple "yellow chair" is unstable, add detail words to force model to focus on specific visual features
    detailed_attributes = {
        "Category 3: Detailed Attribute Combinations": [
            'yellow chair with black armrests',         # Yellow chair with black armrests
            'office chair with metal base',
            'yellow office chair with metal base', # White office chair with metal base
            'office chair with five wheels'         # Office chair with five wheels - verify model's extraction of structural details
        ]
    }

    # Category 4: Blind User Guidance Scenarios
    # Simulate commands blind users might give - usually vague or with strong contrast intention
    blind_guidance = {
        "Category 4: Blind User Guidance Scenarios": [
            'the only yellow object',              # Only yellow object - avoid "chair", test color saliency
            'the bright colored chair',            # Bright colored chair - test model's understanding of "bright"
            'a row of three chairs',               # Row of three chairs - test model's concept of "group"
        ]
    }

    # Combine all categories
    description_formats = {}
    description_formats.update(basic_color)
    description_formats.update(positional_phrases)
    description_formats.update(detailed_attributes)
    description_formats.update(blind_guidance)

    results_summary = {}

    print("\nTesting descriptions...\n")

    # Run tests for each category
    for category_name, descriptions in description_formats.items():
        print("-" * 60)
        print(f" {category_name}")
        print("-" * 60)

        category_results = {}

        for desc in descriptions:
            detector.set_custom_classes([desc])
            frame, detections = detector.detect_from_image(test_image)

            category_results[desc] = {
                'count': len(detections),
                'detections': detections
            }

            # Simple one-line output
            if detections:
                conf_str = ", ".join([f"{d['confidence']:.2f}" for d in detections])
                print(f"  '{desc}': {len(detections)} detected (conf: {conf_str})")
            else:
                print(f"  '{desc}': 0 detected")

        results_summary[category_name] = category_results
        print()


def test_experiment2_chair_types():
    """
    Experiment 2: Test office chair vs wooden chair detection
    Test image: chair3.jpg
    """
    print("="*60)
    print("EXPERIMENT 2: Office Chair vs Wooden Chair")
    print("="*60)

    detector = ImageUploadDetector(model_path='../yolov8s-world.pt', conf_threshold=0.3)

    test_image_chair3 = Path(__file__).parent.parent / 'test_images' / 'chair3.jpg'

    if not test_image_chair3.exists():
        print(f"\n✗ Test image not found: {test_image_chair3}\n")
        return

    # Test different chair type descriptions
    test_descriptions = [
        'office chair',
        'wooden chair'
    ]

    results = {}

    print("\nTesting chair type descriptions...\n")

    for desc in test_descriptions:
        detector.set_custom_classes([desc])
        frame, detections = detector.detect_from_image(test_image_chair3)

        results[desc] = {
            'count': len(detections),
            'detections': detections
        }

        print(f"'{desc}': {len(detections)} detected")
        for i, det in enumerate(detections, 1):
            print(f"  {i}. Confidence: {det['confidence']:.2f}")

    # Summary
    print("\n" + "="*60)
    print("RESULTS SUMMARY")
    print("="*60)

    office_detected = any(results[desc]['count'] > 0 for desc in ['office chair', 'desk chair'])
    wooden_detected = any(results[desc]['count'] > 0 for desc in ['wooden chair', 'wood chair', 'dining chair'])

    print(f"\nOffice chair detected: {'✓' if office_detected else '✗'}")
    print(f"Wooden chair detected: {'✓' if wooden_detected else '✗'}")

    if office_detected and wooden_detected:
        print("\n✓ Model CAN distinguish between chair types")
    elif results['chair']['count'] > 0:
        print("\n⚠ Model detected 'chair' but not specific types")
        print("  Recommendation: Use 'chair' + post-processing")
    else:
        print("\n✗ Model failed to detect chairs")

    print("\n" + "="*60 + "\n")

    return results

if __name__ == "__main__":
    print("\n" + "="*80)
    print(" " * 20 + "YOLO-WORLD DETECTION EXPERIMENTS")
    print("="*80)
    print("\nGoal: Test how YOLO-World detects similar objects (white vs red chairs)")
    print("Test Image: chair.jpg (2 white chairs + 1 red chair)")
    print("="*80 + "\n")

    try:
        # Experiment 1: Test different description formats
        print("\n" + " Starting Experiment 1...")
        exp1_results = test_experiment1_description_formats()

        # Experiment 2: Test office chair vs wooden chair detection
        print("\n" + " Starting Experiment 2...")
        exp4_results = test_experiment2_chair_types()

    except Exception as e:
        print(f"\n✗ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
