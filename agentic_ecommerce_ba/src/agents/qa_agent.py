import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agents.base_agent import BaseAgent
from schemas.qa_schema import QAAuditReport
from core.i18n import t, get_lang

class QAAgent(BaseAgent):
    """
    Tác tử chuyên trách: QA Manager / Software Gatekeeper.
    Nhiệm vụ: Cầm trên tay 3 file lớn (Vision, BA SRS, DB Schema) để Cross-Audit (soi lỗi mâu thuẫn).
    Bắt buộc phải xài gemini-2.5-pro để có Memory Context rộng, Reasoning logic sâu để đối chiếu chéo cực mạnh.
    """

    def __init__(self):
        super().__init__(role_name="QA Agent", model_name="gemini-2.5-flash")

    def audit_system(self, vision_json: str, srs_json: str, db_json: str) -> QAAuditReport:
        system_prompt = t("prompt_qa_system")
        
        lang = get_lang()
        if lang == "vi":
            user_prompt = (
                "### DỮ LIỆU INPUT ĐỂ KIỂM TOÁN CHÉO (CROSS-VALIDATION):\n\n"
                f"--- 1. VISION REPORT (Mô tả Giao diện thô) ---\n{vision_json}\n\n"
                f"--- 2. BA SRS (Đặc tả Logic Business Rules) ---\n{srs_json}\n\n"
                f"--- 3. DATA ARCHITECT (Cấu trúc DB Schema) ---\n{db_json}\n\n"
                "Là giám đốc QA Gatekeeper, hãy soi lỗi vô lý giữa 3 tài liệu này và xuất báo cáo Audit cuối cùng."
            )
        else:
            user_prompt = (
                "### CROSS-AUDIT INPUT DATA:\n\n"
                f"--- 1. VISION RAW (UI Elements Details) ---\n{vision_json}\n\n"
                f"--- 2. BA SRS (Logic & Rules Specs) ---\n{srs_json}\n\n"
                f"--- 3. DATA ARCHITECT (DB Schema Design) ---\n{db_json}\n\n"
                "As the QA Gatekeeper, analyze any inconsistencies among these 3 documents and output a final Audit Report."
            )
            
        result = self.call_llm(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            pydantic_schema=QAAuditReport
        )
        
        return result
