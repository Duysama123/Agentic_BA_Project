import os
import sys
import time
from typing import List

# Add parent dir to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.core.config import Config
from src.agents.vision_agent import VisionAgent

def levenshtein_distance(s1: str, s2: str) -> int:
    if len(s1) < len(s2):
        return levenshtein_distance(s2, s1)
    if len(s2) == 0:
        return len(s1)

    previous_row = range(len(s2) + 1)
    for i, c1 in enumerate(s1):
        current_row = [i + 1]
        for j, c2 in enumerate(s2):
            insertions = previous_row[j + 1] + 1
            deletions = current_row[j] + 1
            substitutions = previous_row[j] + (c1 != c2)
            current_row.append(min(insertions, deletions, substitutions))
        previous_row = current_row

    return previous_row[-1]

def calculate_word_accuracy(pred_text: str, gt_text: str) -> float:
    pred_words = [w.strip(",.?!:;()\"'").lower() for w in pred_text.split() if w.strip()]
    gt_words = [w.strip(",.?!:;()\"'").lower() for w in gt_text.split() if w.strip()]
    
    if not gt_words:
        return 100.0 if not pred_words else 0.0
        
    # Standard Word Error Rate calculation based on word-level alignment
    substitutions = 0
    deletions = 0
    insertions = 0
    
    matched_preds = set()
    for gt_w in gt_words:
        best_dist = 999
        best_pred_idx = -1
        
        for p_idx, pred_w in enumerate(pred_words):
            if p_idx in matched_preds:
                continue
            dist = levenshtein_distance(gt_w, pred_w)
            if dist < best_dist:
                best_dist = dist
                best_pred_idx = p_idx
                
        # If edit distance is small, count as matched (possibly with minor spelling correction)
        if best_pred_idx != -1 and best_dist <= 2:
            matched_preds.add(best_pred_idx)
            if best_dist > 0:
                substitutions += 1
        else:
            deletions += 1
            
    insertions = len(pred_words) - len(matched_preds)
    total_errors = substitutions + deletions + insertions
    
    accuracy = max(0.0, 1.0 - (total_errors / len(gt_words))) * 100.0
    return accuracy

def run_ocr_evaluation():
    print("=" * 70)
    print("  Specify.ai - OCR Accuracy Evaluation on Usability Test Set (3 Images)")
    print("=" * 70)

    # Ground Truth manually transcribed text labels for the 3 qualitative mockups
    qualitative_ground_truth = {
        "sample11.png": "User Profile Form First Name Last Name Email Address Password Confirm Password Save Changes Cancel",
        "sample2.jpg": "Payment Details Card Number Cardholder Name Expiration Date CVV Pay Now Go Back",
        "sample3.jpg": "Checkout Summary Cart Total Shipping Cost Total Amount Place Order Apply Coupon"
    }

    # Load API Keys
    api_keys = Config.get_api_keys()
    if not api_keys or api_keys[0] == "":
        print("[ERROR] Gemini API Key not found. Please configure the GEMINI_API_KEY environment variable.")
        return

    agent = VisionAgent()
    qual_dir = os.path.abspath("sample_files/qualitative_test")

    if not os.path.exists(qual_dir):
        print(f"[ERROR] qualitative_test directory not found at: {qual_dir}")
        return

    print(f"[INFO] Starting OCR evaluation on 3 qualitative mockup images.")
    print("[INFO] This script will call the Gemini API 3 times (consumes very few tokens).")
    print("Press Enter to continue or Ctrl+C to cancel...")
    try:
        input()
    except KeyboardInterrupt:
        print("\n[INFO] OCR evaluation cancelled.")
        return

    total_accuracy = 0.0
    processed_count = 0
    start_time = time.time()

    for fname, gt_text in qualitative_ground_truth.items():
        img_path = os.path.join(qual_dir, fname)
        if not os.path.exists(img_path):
            print(f"[WARNING] Image file not found: {fname}")
            continue

        print(f"\n[*] Processing {fname}...")
        try:
            # Analyze wireframe (Stage 1 YOLO + Stage 2 Gemini 2.0 Flash)
            analysis = agent.analyze_wireframe(img_path)
            
            # Extract all predicted text labels
            pred_labels = [el.label for el in analysis.elements if el.label]
            pred_text = " ".join(pred_labels)
            
            # Calculate accuracy
            acc = calculate_word_accuracy(pred_text, gt_text)
            total_accuracy += acc
            processed_count += 1
            
            print(f"   - Ground Truth text: {gt_text}")
            print(f"   - Extracted OCR text:    {pred_text}")
            print(f"   - Word Recognition Accuracy: {acc:.2f}%")
            
        except Exception as e:
            print(f"   [ERROR] Error processing {fname}: {e}")

    total_time = time.time() - start_time
    
    if processed_count > 0:
        avg_ocr_accuracy = total_accuracy / processed_count
        print("\n" + "=" * 70)
        print("                      OCR EVALUATION SUMMARY")
        print("=" * 70)
        print(f"Total images evaluated:          {processed_count}")
        print(f"Total execution time:            {total_time:.2f} s")
        print(f"Average OCR Word Accuracy:     {avg_ocr_accuracy:.2f}%")
        print("=" * 70)
    else:
        print("[ERROR] No images were successfully processed.")

if __name__ == "__main__":
    run_ocr_evaluation()
