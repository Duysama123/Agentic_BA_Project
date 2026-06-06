import os
import sys
import json
from PIL import Image
from typing import Optional

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agents.base_agent import BaseAgent
from schemas.ui_schema import WireframeAnalysis

# ============================================================
#  YOLO LOCAL MODEL — Load một lần duy nhất khi khởi động
# ============================================================
_YOLO_MODEL = None
_YOLO_WEIGHTS_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
    "models", "yolo_wireframe_best.pt"
)

def _get_yolo_model():
    """Lazy-load YOLO model (singleton pattern)."""
    global _YOLO_MODEL
    if _YOLO_MODEL is None:
        try:
            from ultralytics import YOLO
            if os.path.exists(_YOLO_WEIGHTS_PATH):
                _YOLO_MODEL = YOLO(_YOLO_WEIGHTS_PATH)
        except ImportError:
            pass  # ultralytics chưa cài — fallback sang Gemini thuần
    return _YOLO_MODEL


def run_yolo_detection(image_path: str, conf_threshold: float = 0.3) -> dict:
    """
    Chạy YOLO local model để phát hiện UI components.
    Returns dict với danh sách component đã phát hiện + bounding boxes.
    """
    model = _get_yolo_model()
    if model is None:
        return {"available": False, "detections": [], "summary": ""}

    results = model.predict(
        source=image_path,
        conf=conf_threshold,
        verbose=False,
        save=False
    )

    detections = []
    class_counts = {}

    for r in results:
        for box in r.boxes:
            class_name = r.names[int(box.cls)]
            confidence = float(box.conf)
            x1, y1, x2, y2 = [round(float(v), 1) for v in box.xyxy[0]]

            detections.append({
                "type": class_name,
                "confidence": confidence,
                "bbox": {"x1": x1, "y1": y1, "x2": x2, "y2": y2}
            })
            class_counts[class_name] = class_counts.get(class_name, 0) + 1

    # Tạo summary dạng văn bản để inject vào prompt Gemini
    summary_parts = [f"{count} {cls}" for cls, count in sorted(class_counts.items())]
    summary = f"YOLO detected: {', '.join(summary_parts)}" if summary_parts else "No components detected"

    return {
        "available": True,
        "detections": detections,
        "class_counts": class_counts,
        "summary": summary,
        "total": len(detections)
    }


class VisionAgent(BaseAgent):
    """
    Tác tử chuyên trách: Chuyên viên Phân tích Hệ thống.
    Kiến trúc Hybrid Pipeline:
        Stage 1: YOLO local model → Phát hiện UI component (bounding boxes + class)
        Stage 2: Gemini Vision    → Hiểu ngữ nghĩa, đặt tên, suy luận user flows
    Lợi ích: Giảm hallucination, tăng độ chính xác, có thể chạy offline Stage 1.
    """

    def __init__(self):
        super().__init__(role_name="Vision Agent", model_name="gemini-2.5-flash")

    def analyze_wireframe(self, image_path: str, user_notes: str = "") -> WireframeAnalysis:
        """
        Thực thi phân tích ảnh Wireframe theo kiến trúc 2 giai đoạn.
        Stage 1: YOLO detection (local, fast, ~77ms)
        Stage 2: Gemini semantic understanding (cloud, rich)
        """
        if not os.path.exists(image_path):
            raise FileNotFoundError(f"Vision Agent cannot access image at: {image_path}")

        img = Image.open(image_path)
        
        # Layer 1 Token Saving: Resize image to max 1024x1024 to save Vision Tokens
        # This reduces the number of tokens Gemini charges for image input significantly.
        img.thumbnail((1024, 1024), Image.Resampling.LANCZOS)


        # ── STAGE 1: YOLO Local Detection ──────────────────────────
        yolo_result = run_yolo_detection(image_path)

        # ── STAGE 2: Gemini Semantic Understanding ─────────────────
        system_prompt = (
            "You are a professional System Analyst / UI-UX Specialist. "
            "Your task is to examine wireframe sketches and extract their components "
            "into a clear technical data structure.\n"
            "STRICTLY FOLLOW THE SPECIFIED OUTPUT SCHEMA. "
            "Respond in English ONLY."
        )

        user_prompt = "Below is a wireframe sketch image for analysis.\n\n"

        # Inject YOLO results as grounding context
        if yolo_result["available"] and yolo_result["total"] > 0:
            user_prompt += (
                f"[PRE-ANALYSIS BY LOCAL YOLO MODEL — USE AS GROUND TRUTH REFERENCE]\n"
                f"{yolo_result['summary']}\n"
                f"Total detected: {yolo_result['total']} components\n"
                f"Detailed detections: {json.dumps(yolo_result['class_counts'])}\n\n"
                "[YOUR TASK]\n"
                "1. Use the YOLO detections above as your baseline — DO NOT invent components that YOLO did not find.\n"
                "2. Enrich each detected component: assign a meaningful ID, label (text visible in UI), and description.\n"
                "3. Infer the user interaction flows based on the layout and component types.\n"
            )
        else:
            user_prompt += (
                "[NOTE: Local YOLO model unavailable. Perform full visual analysis independently.]\n"
                "Scan the entire image, list all independent UI components, and predict user flows.\n"
            )

        if user_notes:
            user_prompt += f"\n[ADDITIONAL NOTES FROM BA LEAD]: {user_notes}\n"

        result = self.call_llm(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            pydantic_schema=WireframeAnalysis,
            image_data=img
        )

        return result
