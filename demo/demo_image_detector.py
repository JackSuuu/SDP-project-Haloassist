"""
简单演示脚本 - 图像上传检测器
演示如何使用 ImageUploadDetector 测试白色椅子和黑色椅子的识别
"""
import sys
from pathlib import Path

# 添加 src 到路径
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir / 'src'))

from image_detector import ImageUploadDetector


def main():
    print("\n" + "="*60)
    print("图像上传检测器 - 演示")
    print("="*60 + "\n")

    # 初始化检测器
    print("正在初始化检测器...")
    model_path = current_dir / 'yolov8s-world.pt'
    detector = ImageUploadDetector(model_path=str(model_path), conf_threshold=0.4)
    print("✓ 检测器初始化完成\n")

    # 测试图片路径
    test_image = current_dir / 'test_images' / 'chair.jpg'

    if not test_image.exists():
        print(f"✗ 测试图片未找到: {test_image}")
        print("\n请提供图片路径:")
        test_image = input("图片路径: ").strip()
        test_image = Path(test_image)
        if not test_image.exists():
            print("图片不存在,退出程序")
            return

    print(f"使用测试图片: {test_image}\n")

    # 示例 1: 检测一般物体
    print("-" * 60)
    print("示例 1: 检测一般物体")
    print("-" * 60)

    general_classes = ['chair', 'person', 'table', 'bottle', 'laptop']
    print(f"检测类别: {general_classes}")

    detector.set_custom_classes(general_classes)
    frame, detections = detector.detect_from_image(test_image)

    print(f"\n发现 {len(detections)} 个物体:")
    for i, det in enumerate(detections, 1):
        print(f"  {i}. {det['class']}: 置信度 {det['confidence']:.2f}")

    # 保存结果
    results_dir = current_dir / 'test_results'
    results_dir.mkdir(exist_ok=True)
    detector.visualize_detections(frame, detections,
                                  save_path=str(results_dir / 'general_detection.jpg'))
    print(f"\n✓ 结果已保存至: {results_dir / 'general_detection.jpg'}\n")

    # 示例 2: 检测颜色特定的椅子
    print("-" * 60)
    print("示例 2: 区分白色椅子和黑色椅子")
    print("-" * 60)

    chair_classes = ['white chair', 'black chair']
    annotated, detections = detector.detect_with_custom_classes(
        image_path=test_image,
        custom_classes=chair_classes,
        save_result=str(results_dir / 'chair_color_detection.jpg')
    )

    print(f"\n发现 {len(detections)} 个特定颜色的椅子:")
    for i, det in enumerate(detections, 1):
        print(f"  {i}. {det['class']}: 置信度 {det['confidence']:.2f}")

    print(f"\n✓ 结果已保存至: {results_dir / 'chair_color_detection.jpg'}\n")

    # 示例 3: 对比不同描述
    print("-" * 60)
    print("示例 3: 对比不同物体描述的检测结果")
    print("-" * 60)

    comparison_classes = ['white chair', 'black chair', 'chair', 'wooden chair']
    print(f"对比类别: {comparison_classes}\n")

    comparison = detector.compare_objects(test_image, comparison_classes)

    print("\n对比结果总结:")
    print("-" * 40)
    for obj_class, dets in comparison.items():
        print(f"{obj_class:20s}: {len(dets)} 个检测")
        if dets:
            avg_conf = sum(d['confidence'] for d in dets) / len(dets)
            print(f"{'':20s}  平均置信度: {avg_conf:.2f}")

    print("\n" + "="*60)
    print("演示完成!")
    print("="*60)
    print(f"\n所有结果已保存至: {results_dir}")
    print("\n提示:")
    print("- 你可以修改 custom_classes 来检测不同的物体")
    print("- 降低 conf_threshold 可以检测更多物体(但可能有误检)")
    print("- 使用更具体的描述(如 'white wooden chair')可以提高精度")
    print()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n程序被用户中断")
    except Exception as e:
        print(f"\n✗ 发生错误: {e}")
        import traceback
        traceback.print_exc()
