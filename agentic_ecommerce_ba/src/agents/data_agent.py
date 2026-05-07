import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agents.base_agent import BaseAgent
from schemas.db_schema import DatabaseSchema
from core.i18n import t, get_lang

def sanitize_mermaid(mermaid_code: str) -> str:
    """Loại bỏ thẻ markdown bao bọc rác do LLM tự gen ra."""
    code = mermaid_code.strip()
    if "```mermaid" in code:
        code = code.split("```mermaid")[1]
        if "```" in code:
            code = code.split("```")[0]
    elif "```" in code:
        parts = code.split("```")
        if len(parts) > 2:
            code = parts[1]
    return code.strip()

class DataArchitectAgent(BaseAgent):
    """
    Tác tử chuyên trách: Thiết kế Cơ sở Dữ liệu.
    Nhận Data Contract là Bản đặc tả phần mềm JSON và sinh ra cấu trúc Tối ưu hoá cho DB,
    đồng thời sinh mã render Mermaid ERD.
    """
    def __init__(self):
        super().__init__(role_name="Data Architect Agent", model_name="gemini-2.5-flash")

    def design_database(self, srs_context: str) -> DatabaseSchema:
        system_prompt = t("prompt_da_system")
        
        lang = get_lang()
        if lang == "vi":
            user_prompt = f"### CHI TIẾT TÀI LIỆU SRS TỪ BA:\n{srs_context}\n\n"
            user_prompt += "Với tư cách là System Architect, dựa vào SRS hãy thiết kế cấu trúc Cơ sở dữ liệu chuẩn hoá (Ít nhất là Đạt chuẩn 3NF)."
        else:
            user_prompt = f"### SRS DOCUMENT DETAILS:\n{srs_context}\n\n"
            user_prompt += "As a System Architect, design a normalized Database schema (at least 3NF) based on this SRS."
            
        result = self.call_llm(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            pydantic_schema=DatabaseSchema
        )
        
        result.erd_mermaid = sanitize_mermaid(result.erd_mermaid)
        
        return result
