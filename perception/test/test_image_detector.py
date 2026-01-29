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
test_image = Path(__file__).parent.parent / 'test_images' / 'chair.jpg'

def test_color_specific_detection():
    """Test detection of color-specific objects (white chair vs black chair)"""
    print("="*60)
    print("Test 1: Color-Specific Object Detection")
    print("="*60)

    detector = ImageUploadDetector(model_path='../yolov8s-world.pt')

    if not test_image.exists():
        print(f"✗ Test image not found: {test_image}\n")
        return

    # Compare different chair colors
    object_classes = ['white chair', 'red chair']
    comparison = detector.compare_objects(test_image, object_classes)

    print("\n✓ Comparison completed\n")

if __name__ == "__main__":
    print("\n" + "="*60)
    print("IMAGE UPLOAD DETECTOR TEST SUITE")
    print("="*60 + "\n")

    try:
        test_color_specific_detection()

        print("="*60)
        print("ALL TESTS COMPLETED")
        print("="*60)

    except Exception as e:
        print(f"\n✗ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
