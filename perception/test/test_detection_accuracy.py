"""
Critical Test #3: Detection Accuracy Testing
Tests YOLO detection accuracy for supermarket assistance scenario

Focus Tests:
1. Object Type Accuracy - Which objects are easier to detect?
2. Distance vs Accuracy - How does distance affect detection?

Output: Report-ready statistics
"""
import sys
import os
from pathlib import Path
import cv2

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from perception.detector import ObjectDetector


class DetectionAccuracyTester:
    """Test detection accuracy on prepared test images"""

    def __init__(self, test_images_dir='test_images', model_path='yolov8n.pt'):
        self.test_images_dir = Path(test_images_dir)
        self.model_path = model_path
        self.detector = None
        self.results = []

        # YOLO class name mapping (COCO dataset classes)
        # Maps filename object names to YOLO class names
        self.class_mapping = {
            'bottle': 'bottle',
            'bottles': 'bottle',
            'cup': 'cup',
            'cups': 'cup',
            'apple': 'apple',
            'apples': 'apple',
            'banana': 'banana',
            'bananas': 'banana',
            'orange': 'orange',
            'oranges': 'orange',
            'broccoli': 'broccoli',
            'carrot': 'carrot',
            'chair': 'chair',
            'book': 'book',
            'backpack': 'backpack',
            'cell_phone': 'cell phone',
            'can': 'bottle',  # Cans often detected as bottles
            'box': 'box',
            'boxes': 'box',
            'bag': 'handbag',
            'bags': 'handbag',
            'shampoo': 'bottle',
            'shampoos': 'bottle',
            'detergent': 'bottle',
            'potato': 'potato',
            'chip': 'donut',  # Approximate mapping
        }

    def parse_filename(self, filename):
        """
        Parse test image filename to extract metadata

        Format: {object_description}_{distance}.jpg
        Examples:
          - bottles_near.jpg → ('bottles', 'near', 'good')
          - bottles_in_stands_middle.jpg → ('bottles', 'middle', 'good')
          - apples_near.jpg → ('apples', 'near', 'good')
          - chair.jpg → ('chair', 'unknown', 'good')
        """
        stem = Path(filename).stem  # Remove .jpg

        # Check for distance suffix (last part)
        distance = 'unknown'
        if stem.endswith('_near'):
            distance = 'near'
            stem = stem[:-5]  # Remove '_near'
        elif stem.endswith('_middle'):
            distance = 'middle'
            stem = stem[:-7]  # Remove '_middle'
        elif stem.endswith('_far'):
            distance = 'far'
            stem = stem[:-4]  # Remove '_far'
        elif stem.endswith('_medium'):
            distance = 'medium'
            stem = stem[:-7]  # Remove '_medium'

        # Extract object name (what remains after removing distance)
        # Clean up object name: remove extra words like "in", "stands", numbers
        obj_parts = stem.split('_')

        # Filter out common descriptive words and numbers
        filter_words = {'in', 'on', 'the', 'stands', 'with', 'and', 'of'}
        obj_parts_cleaned = []
        for part in obj_parts:
            if part not in filter_words and not part.isdigit():
                obj_parts_cleaned.append(part)

        # Take the main object (usually first word, or combine if needed)
        if obj_parts_cleaned:
            obj = obj_parts_cleaned[0]  # Main object is usually first word
        else:
            obj = stem  # Fallback to full stem

        # Extract condition (check for dark/occluded keywords)
        condition = 'good'
        full_stem = Path(filename).stem.lower()
        if 'dark' in full_stem:
            condition = 'dark'
        elif 'occluded' in full_stem or 'crowded' in full_stem:
            condition = 'occluded'

        return obj, distance, condition

    def test_single_image(self, image_path):
        """
        Test detection on a single image

        Returns:
            dict with test result
        """
        filename = image_path.name
        expected_obj, distance, condition = self.parse_filename(filename)

        # Read image
        img = cv2.imread(str(image_path))
        if img is None:
            return {
                'filename': filename,
                'expected_object': expected_obj,
                'distance': distance,
                'condition': condition,
                'detected': False,
                'detected_object': None,
                'confidence': 0.0,
                'error': 'Failed to read image'
            }

        # Run detection
        detections = self.detector.detect(img)

        # Get expected YOLO class name
        expected_yolo_class = self.class_mapping.get(expected_obj, expected_obj).lower()

        # Check if expected object was detected
        detected = False
        detected_obj = None
        confidence = 0.0
        best_match_conf = 0.0

        for det in detections:
            detected_class = det['class'].lower()

            # Match detection (flexible matching)
            # Check if classes match or if one contains the other
            is_match = False

            # Exact match
            if expected_yolo_class == detected_class:
                is_match = True
            # Substring match (handle "cell phone" vs "cell_phone")
            elif expected_yolo_class in detected_class or detected_class in expected_yolo_class:
                is_match = True
            # Handle plural forms (bottle vs bottles)
            elif expected_yolo_class.rstrip('s') == detected_class.rstrip('s'):
                is_match = True

            if is_match:
                # Take the detection with highest confidence
                if det['confidence'] > best_match_conf:
                    detected = True
                    detected_obj = det['class']
                    confidence = det['confidence']
                    best_match_conf = det['confidence']

        return {
            'filename': filename,
            'expected_object': expected_obj,
            'distance': distance,
            'condition': condition,
            'detected': detected,
            'detected_object': detected_obj,
            'confidence': confidence,
            'all_detections': [d['class'] for d in detections]
        }

    def run_all_tests(self):
        """Run detection test on all images"""
        print("\n" + "="*80)
        print("DETECTION ACCURACY TEST - SUPERMARKET SCENARIO")
        print("="*80)
        print(f"Test images directory: {self.test_images_dir.absolute()}")
        print(f"YOLO model: {self.model_path}")
        print("="*80 + "\n")

        # Check if test_images directory exists
        if not self.test_images_dir.exists():
            print(f"❌ Error: Directory not found: {self.test_images_dir}")
            print("Please run download_test_images.py first!")
            return

        # Get all test images
        image_files = list(self.test_images_dir.glob('*.jpg'))

        if not image_files:
            print(f"❌ Error: No JPG images found in {self.test_images_dir}")
            return

        print(f"✓ Found {len(image_files)} test images")

        # Load YOLO model
        print(f"\nLoading YOLO model: {self.model_path}...")
        self.detector = ObjectDetector(model_path=self.model_path)
        print("✓ Model loaded\n")

        print("="*80)
        print("TESTING IMAGES:")
        print("="*80)
        print(f"{'#':<4} {'Filename':<30} {'Expected':<12} {'Detected?':<12} {'Confidence':<12}")
        print("-" * 80)

        # Test each image
        self.results = []
        for i, image_path in enumerate(sorted(image_files), 1):
            result = self.test_single_image(image_path)
            self.results.append(result)

            status = "✓ YES" if result['detected'] else "✗ NO"
            conf = f"{result['confidence']:.2f}" if result['detected'] else "N/A"

            print(f"{i:<4} {result['filename']:<30} {result['expected_object']:<12} {status:<12} {conf:<12}")

        print("="*80 + "\n")

        # Analyze results
        self.analyze_results()

    def analyze_results(self):
        """Analyze test results and print statistics"""

        if not self.results:
            print("No results to analyze")
            return

        total = len(self.results)
        detected = sum(1 for r in self.results if r['detected'])

        # High-confidence detections (confidence > 0.5)
        HIGH_CONF_THRESHOLD = 0.5
        high_conf_detected = sum(1 for r in self.results if r['detected'] and r['confidence'] > HIGH_CONF_THRESHOLD)

        overall_detection_rate = detected / total * 100 if total > 0 else 0
        overall_high_conf_rate = high_conf_detected / total * 100 if total > 0 else 0

        print("\n" + "="*80)
        print("TEST 1: OBJECT TYPE ACCURACY")
        print("="*80)
        print("Which supermarket objects are easier to detect?\n")

        # Group by object type
        HIGH_CONF_THRESHOLD = 0.5
        object_stats = {}
        for result in self.results:
            obj = result['expected_object']
            if obj not in object_stats:
                object_stats[obj] = {'total': 0, 'detected': 0, 'high_conf': 0, 'confidences': []}

            object_stats[obj]['total'] += 1
            if result['detected']:
                object_stats[obj]['detected'] += 1
                object_stats[obj]['confidences'].append(result['confidence'])
                if result['confidence'] > HIGH_CONF_THRESHOLD:
                    object_stats[obj]['high_conf'] += 1

        # Print object accuracy table
        print(f"{'Object':<15} {'Tested':<8} {'Detected':<10} {'High-Conf':<12} {'Det Rate':<10} {'H-C Rate':<10} {'Avg Conf':<10}")
        print("-" * 90)

        object_accuracies = []
        for obj, stats in sorted(object_stats.items()):
            det_rate = stats['detected'] / stats['total'] * 100 if stats['total'] > 0 else 0
            hc_rate = stats['high_conf'] / stats['total'] * 100 if stats['total'] > 0 else 0
            avg_conf = sum(stats['confidences']) / len(stats['confidences']) if stats['confidences'] else 0

            print(f"{obj:<15} {stats['total']:<8} {stats['detected']:<10} {stats['high_conf']:<12} "
                  f"{det_rate:>5.1f}%    {hc_rate:>5.1f}%    {avg_conf:>6.2f}")

            object_accuracies.append((obj, det_rate, hc_rate, stats['detected'], stats['high_conf'], stats['total'], avg_conf))

        # Find best and worst (by high-confidence rate)
        best_obj = max(object_accuracies, key=lambda x: x[2])  # x[2] is hc_rate
        worst_obj = min(object_accuracies, key=lambda x: x[2])

        print("\n" + "-"*90)
        print("KEY FINDINGS (Based on High-Confidence Rate):")
        print(f"  ✓ Best:  {best_obj[0]} (Det: {best_obj[1]:.0f}%, High-Conf: {best_obj[2]:.0f}%, Avg: {best_obj[6]:.2f})")
        print(f"  ✗ Worst: {worst_obj[0]} (Det: {worst_obj[1]:.0f}%, High-Conf: {worst_obj[2]:.0f}%, Avg: {worst_obj[6]:.2f})")
        print(f"\n  💡 High-Confidence Threshold: >{HIGH_CONF_THRESHOLD} (for reliable detection)")
        print(f"     Low confidence detections may be unreliable in real use!")

        print("\n" + "="*90)
        print("📋 COPY TO REPORT - TEST 1:")
        print("="*90)
        print("Object Type Detection Accuracy (Supermarket Scenario):\n")
        print(f"{'Object':<15} {'Detection Rate':<18} {'High-Conf Rate':<18} {'Avg Confidence':<15}")
        print("-" * 90)
        for obj, det_rate, hc_rate, detected, high_conf, total, avg_conf in sorted(object_accuracies, key=lambda x: -x[2]):
            print(f"  {obj:12s}  {det_rate:>5.1f}% ({detected}/{total})      "
                  f"{hc_rate:>5.1f}% ({high_conf}/{total})      {avg_conf:.2f}")
        print(f"\n  Best (High-Conf):  {best_obj[0]} at {best_obj[2]:.0f}% (avg conf: {best_obj[6]:.2f})")
        print(f"  Worst (High-Conf): {worst_obj[0]} at {worst_obj[2]:.0f}% (avg conf: {worst_obj[6]:.2f})")
        print(f"\n  Note: High-Confidence means detection with confidence > {HIGH_CONF_THRESHOLD}")
        print("="*90 + "\n")

        # TEST 2: Distance vs Accuracy
        print("\n" + "="*80)
        print("TEST 2: DISTANCE vs ACCURACY")
        print("="*80)
        print("How does distance affect detection accuracy?\n")

        # Group by distance
        distance_stats = {}
        for result in self.results:
            dist = result['distance']
            if dist not in distance_stats:
                distance_stats[dist] = {'total': 0, 'detected': 0, 'high_conf': 0, 'confidences': []}

            distance_stats[dist]['total'] += 1
            if result['detected']:
                distance_stats[dist]['detected'] += 1
                distance_stats[dist]['confidences'].append(result['confidence'])
                if result['confidence'] > HIGH_CONF_THRESHOLD:
                    distance_stats[dist]['high_conf'] += 1

        # Print distance accuracy table
        distance_order = ['near', 'middle', 'medium', 'far', 'unknown']
        distance_labels = {
            'near': 'Near (0.3-1m)',
            'middle': 'Middle (1-2m)',
            'medium': 'Medium (1-2m)',
            'far': 'Far (2-4m)',
            'unknown': 'Unknown'
        }

        print(f"{'Distance':<20} {'Tested':<8} {'Detected':<10} {'High-Conf':<12} {'Det Rate':<10} {'H-C Rate':<10} {'Avg Conf':<10}")
        print("-" * 95)

        distance_accuracies = []
        for dist in distance_order:
            if dist not in distance_stats:
                continue

            stats = distance_stats[dist]
            det_rate = stats['detected'] / stats['total'] * 100 if stats['total'] > 0 else 0
            hc_rate = stats['high_conf'] / stats['total'] * 100 if stats['total'] > 0 else 0
            avg_conf = sum(stats['confidences']) / len(stats['confidences']) if stats['confidences'] else 0

            label = distance_labels.get(dist, dist)
            print(f"{label:<20} {stats['total']:<8} {stats['detected']:<10} {stats['high_conf']:<12} "
                  f"{det_rate:>5.1f}%    {hc_rate:>5.1f}%    {avg_conf:>6.2f}")

            distance_accuracies.append((label, det_rate, hc_rate, stats['detected'], stats['high_conf'], stats['total'], avg_conf))

        print("\n" + "-"*95)
        print("KEY FINDINGS:")

        if len(distance_accuracies) >= 2:
            # Compare near vs far (using high-confidence rate)
            near_data = next(((label, det_rate, hc_rate, avg_conf) for label, det_rate, hc_rate, _, _, _, avg_conf in distance_accuracies if 'Near' in label), None)
            far_data = next(((label, det_rate, hc_rate, avg_conf) for label, det_rate, hc_rate, _, _, _, avg_conf in distance_accuracies if 'Far' in label), None)

            if near_data and far_data:
                near_label, near_det, near_hc, near_conf = near_data
                far_label, far_det, far_hc, far_conf = far_data

                diff_det = near_det - far_det
                diff_hc = near_hc - far_hc

                print(f"  Detection Rate:")
                print(f"    • Near: {near_det:.1f}%  |  Far: {far_det:.1f}%  |  Diff: {diff_det:+.1f}%")
                print(f"  High-Confidence Rate:")
                print(f"    • Near: {near_hc:.1f}%  |  Far: {far_hc:.1f}%  |  Diff: {diff_hc:+.1f}%")
                print(f"  Average Confidence:")
                print(f"    • Near: {near_conf:.2f}  |  Far: {far_conf:.2f}")

        print("\n" + "="*95)
        print("📋 COPY TO REPORT - TEST 2:")
        print("="*95)
        print("Detection Accuracy by Distance:\n")
        print(f"{'Distance':<20} {'Detection Rate':<20} {'High-Conf Rate':<20} {'Avg Confidence':<15}")
        print("-" * 95)
        for label, det_rate, hc_rate, detected, high_conf, total, avg_conf in distance_accuracies:
            print(f"  {label:18s}  {det_rate:>5.1f}% ({detected}/{total})       "
                  f"{hc_rate:>5.1f}% ({high_conf}/{total})       {avg_conf:.2f}")

        if len(distance_accuracies) >= 2:
            near_data = next(((det_rate, hc_rate) for label, det_rate, hc_rate, _, _, _, _ in distance_accuracies if 'Near' in label), None)
            far_data = next(((det_rate, hc_rate) for label, det_rate, hc_rate, _, _, _, _ in distance_accuracies if 'Far' in label), None)
            if near_data and far_data:
                near_det, near_hc = near_data
                far_det, far_hc = far_data
                print(f"\n  Impact Analysis:")
                print(f"    • Detection rate change: {near_det - far_det:+.1f}% (Near vs Far)")
                print(f"    • High-confidence rate change: {near_hc - far_hc:+.1f}% (Near vs Far)")
                if near_hc < far_hc:
                    print(f"    ⚠️  Note: Far distance actually has higher high-conf rate!")
                    print(f"           This may be due to sample size or specific objects tested.")
        print("="*95 + "\n")


        # Failed detections
        failed = [r for r in self.results if not r['detected']]
        if failed:
            print(f"\n❌ Failed detections ({len(failed)}):")
            for r in failed:
                print(f"   - {r['filename']} (expected: {r['expected_object']})")
                if r['all_detections']:
                    print(f"     Detected instead: {', '.join(r['all_detections'])}")


def main():
    """Run detection accuracy tests"""
    import argparse

    parser = argparse.ArgumentParser(description='Test YOLO detection accuracy')
    parser.add_argument('--images', type=str, default='../test_images',
                       help='Test images directory')
    parser.add_argument('--model', type=str, default='yolov8n.pt',
                       help='YOLO model path')

    args = parser.parse_args()

    tester = DetectionAccuracyTester(
        test_images_dir=args.images,
        model_path=args.model
    )

    tester.run_all_tests()


if __name__ == '__main__':
    main()
