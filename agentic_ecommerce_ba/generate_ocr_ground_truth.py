import os
import sys
import glob
import json
import time
from PIL import Image

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.core.config import Config
from src.agents.vision_agent import VisionAgent

def generate_ground_truth():
    print("=" * 70)
    print("  Specify.ai - Generating OCR Ground Truth Dataset (27 Images)")
    print("=" * 70)

    # Load API Keys
    api_keys = Config.get_api_keys()
    if not api_keys or api_keys[0] == "":
        print("[ERROR] Không tìm thấy Gemini API Key. Vui lòng cấu hình biến môi trường.")
        return

    agent = VisionAgent()
    test_dir = os.path.abspath("sample_files/quantitative_test")
    output_json = os.path.join(test_dir, "ocr_ground_truth.json")

    image_paths = glob.glob(os.path.join(test_dir, "*.jpg"))
    if not image_paths:
        print(f"[ERROR] Không tìm thấy ảnh .jpg nào trong {test_dir}")
        return

    print(f"[INFO] Tìm thấy {len(image_paths)} ảnh cần gán nhãn chữ.")
    print("[INFO] Bắt đầu gọi Gemini để tự động số hóa nhãn Ground Truth...")
    
    ground_truth = {}
    
    # If file already exists, load existing to avoid re-running
    if os.path.exists(output_json):
        try:
            with open(output_json, "r", encoding="utf-8") as f:
                ground_truth = json.load(f)
            print(f"[INFO] Đã tải {len(ground_truth)} nhãn đã có sẵn từ ocr_ground_truth.json.")
        except Exception as e:
            print(f"[WARNING] Lỗi đọc file ocr_ground_truth.json cũ: {e}")

    for idx, img_path in enumerate(image_paths, 1):
        fname = os.path.basename(img_path)
        if fname in ground_truth:
            continue

        print(f"[{idx}/{len(image_paths)}] Đang trích xuất nhãn cho {fname}...")
        
        success = False
        retries = 3
        while not success and retries > 0:
            try:
                img = Image.open(img_path)
                
                # We call Gemini with a prompt designed to get a clean, concatenated text representation of the mockups
                system_prompt = (
                    "You are a professional OCR engine. Read the handwritten mockups and output ALL "
                    "text labels, button text, and text fields you see in the mockup. "
                    "Output only the extracted text words separated by space, in English. Do not write coordinates, "
                    "do not write formatting, do not write JSON."
                )
                
                response = agent.call_llm(
                    system_prompt=system_prompt,
                    user_prompt="Extract all text words in this image.",
                    image_data=img
                )
                
                clean_text = response.strip()
                # Clean up formatting like ``` or quotes
                if clean_text.startswith("```"):
                    clean_text = clean_text.replace("```", "")
                
                ground_truth[fname] = clean_text
                print(f"   -> Kết quả: {clean_text}")
                success = True
                
            except Exception as e:
                retries -= 1
                error_str = str(e)
                if "429" in error_str or "RESOURCE_EXHAUSTED" in error_str:
                    print(f"   [WARNING] Gặp lỗi 429 (Rate Limit). Đang chờ 10s...")
                    time.sleep(10)
                else:
                    print(f"   [ERROR] Lỗi gọi Gemini: {e}")
                    break

        # Rotate key and wait to be safe
        time.sleep(2)

    # Save to JSON
    with open(output_json, "w", encoding="utf-8") as f:
        json.dump(ground_truth, f, ensure_ascii=False, indent=4)
        
    print("\n" + "=" * 70)
    print(f"[OK] Đã hoàn thành! Đã ghi file Ground Truth tại: {output_json}")
    print("=" * 70)

if __name__ == "__main__":
    generate_ground_truth()
