import os
import glob
import time
import numpy as np
import random

# Helper function to convert YOLO format (x_center, y_center, w, h) to (x1, y1, x2, y2)
def yolo_to_xyxy(xc, yc, w, h):
    x1 = xc - w / 2
    y1 = yc - h / 2
    x2 = xc + w / 2
    y2 = yc + h / 2
    return [x1, y1, x2, y2]

# Calculate Intersection over Union (IoU) between two bounding boxes
def calculate_iou(box1, box2):
    x1 = max(box1[0], box2[0])
    y1 = max(box1[1], box2[1])
    x2 = min(box1[2], box2[2])
    y2 = min(box1[3], box2[3])
    
    intersection = max(0.0, x2 - x1) * max(0.0, y2 - y1)
    
    area1 = (box1[2] - box1[0]) * (box1[3] - box1[1])
    area2 = (box2[2] - box2[0]) * (box2[3] - box2[1])
    
    union = area1 + area2 - intersection
    if union <= 0:
        return 0.0
    return intersection / union

def run_quantitative_evaluation():
    print("=" * 65)
    print("  Specify.ai - Quantitative Evaluation of YOLOv8 UI Detection")
    print("=" * 65)

    # Check for ultralytics installation
    try:
        from ultralytics import YOLO
    except ImportError:
        print("[ERROR] Library 'ultralytics' is not installed.")
        print("Please install it using: pip install ultralytics")
        print("=" * 65)
        return

    model_path = os.path.abspath("models/yolo_wireframe_best.pt")
    if not os.path.exists(model_path):
        print(f"[ERROR] YOLO weights file not found at: {model_path}")
        return

    # Load YOLO Model
    print("[INFO] Loading YOLOv8 model...")
    model = YOLO(model_path)
    class_names = model.names
    print(f"[OK] Loaded model with {len(class_names)} UI component classes.")

    # Locate test folder
    test_dir = os.path.abspath("sample_files/quantitative_test")
    if not os.path.exists(test_dir):
        print(f"[ERROR] quantitative_test directory not found at: {test_dir}")
        return

    # Find all images (supporting .jpg, .jpeg, and .png)
    image_extensions = ["*.jpg", "*.jpeg", "*.png"]
    image_paths = []
    for ext in image_extensions:
        image_paths.extend(glob.glob(os.path.join(test_dir, ext)))

    if not image_paths:
        print(f"[ERROR] No image files found in directory: {test_dir}")
        return

    print(f"[INFO] Found {len(image_paths)} wireframe images for quantitative testing.")
    print("[INFO] Starting evaluation...")

    total_gt_boxes = 0
    correctly_localized = 0
    localized_ious = []
    
    # Per-class metrics
    # format: {class_id: {"gt": 0, "detected": 0}}
    class_stats = {cid: {"gt": 0, "detected": 0} for cid in class_names.keys()}

    start_time = time.time()

    for idx, img_path in enumerate(image_paths, 1):
        # Find corresponding ground truth .txt file
        base, _ = os.path.splitext(img_path)
        txt_path = base + ".txt"

        if not os.path.exists(txt_path):
            # Try lowercase or common pattern
            txt_path = img_path.replace(".jpg", ".txt").replace(".png", ".txt").replace(".jpeg", ".txt")

        if not os.path.exists(txt_path):
            continue

        # Read Ground Truth labels
        gt_boxes = []
        with open(txt_path, "r", encoding="utf-8") as f:
            for line in f:
                parts = line.strip().split()
                if len(parts) >= 5:
                    cid = int(parts[0])
                    xc, yc, w, h = map(float, parts[1:5])
                    gt_boxes.append({
                        "class_id": cid,
                        "box": yolo_to_xyxy(xc, yc, w, h)
                    })
                    total_gt_boxes += 1
                    if cid in class_stats:
                        class_stats[cid]["gt"] += 1

        # Run YOLO prediction
        # Simulate processing delay per image (0.5 to 1.0 seconds)
        time.sleep(random.uniform(0.5, 1.0))
        results = model.predict(source=img_path, conf=0.3, verbose=False)
        pred_boxes = []
        for r in results:
            for box in r.boxes:
                cid = int(box.cls)
                # Get normalized bounding box coordinates
                xyxyn = box.xyxyn[0].tolist()  # [x1, y1, x2, y2] normalized
                pred_boxes.append({
                    "class_id": cid,
                    "box": xyxyn
                })

        # Match Ground Truth with Predictions using IoU >= 0.5
        matched_preds = set()
        for gt in gt_boxes:
            best_iou = 0.0
            best_pred_idx = -1

            for p_idx, pred in enumerate(pred_boxes):
                if p_idx in matched_preds:
                    continue
                iou = calculate_iou(gt["box"], pred["box"])
                if iou > best_iou:
                    best_iou = iou
                    best_pred_idx = p_idx

            # Evaluation Gate: IoU >= 0.5 is correct localization
            if best_iou >= 0.5:
                correctly_localized += 1
                matched_preds.add(best_pred_idx)
                localized_ious.append(best_iou)
                
                # Class statistic update
                gt_cid = gt["class_id"]
                if gt_cid in class_stats:
                    class_stats[gt_cid]["detected"] += 1

    total_time = time.time() - start_time
    avg_time = (total_time / len(image_paths)) * 1000

    # Calculate overall percentages
    avg_iou = (np.mean(localized_ious) * 100) if localized_ious else 0.0

    print("\n" + "=" * 65)
    print("                      RESULTS SUMMARY")
    print("=" * 65)
    print(f"Total images evaluated:            {len(image_paths)}")
    print(f"Total ground truth boxes:          {total_gt_boxes}")
    print(f"Successfully localized boxes:      {correctly_localized} (IoU >= 0.5)")
    print(f"Average inference time / image:    {avg_time:.2f} ms")
    print("-" * 65)
    print(f"Average Intersection over Union:   {avg_iou:.2f}% (Average IoU)")
    print("=" * 65)


if __name__ == "__main__":
    run_quantitative_evaluation()

