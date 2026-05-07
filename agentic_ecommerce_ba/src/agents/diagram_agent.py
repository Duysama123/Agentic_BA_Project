import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agents.base_agent import BaseAgent
from schemas.diagram_schema import DiagramOutput
from core.i18n import t, get_lang

def sanitize_mermaid(mermaid_code: str) -> str:
    """
    Layer 2 Bảo vệ (Post-processing sanitizer):
    Loại bỏ các mã markdown chặn block ```mermaid nếu LLM lỡ sinh ra,
    để đảm bảo string là chuỗi Mermaid thuần tuý có thể render trên Streamlit.
    """
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

class DiagramAgent(BaseAgent):
    """
    Tác tử chuyên trách: Technical Writer / System Architect.
    Nhiệm vụ: Trực quan hoá văn bản SRS thành Sơ đồ quy trình bằng mã Mermaid.js.
    Triển khai kiến trúc Guardrail 3 lớp để chống lỗi Syntax Mermaid.
    """
    
    def __init__(self):
        super().__init__(role_name="Diagram Agent", model_name="gemini-2.5-flash")

    def generate_diagrams(self, srs_context: str) -> DiagramOutput:
        """Sinh sơ đồ từ tài liệu SRS JSON string."""
        
        system_prompt = t("prompt_diagram_system")
        
        lang = get_lang()
        if lang == "vi":
            user_prompt = f"### CHI TIẾT TÀI LIỆU SRS (TỪ BA AGENT):\n{srs_context}\n\n"
            user_prompt += "Hãy vẽ 1 Sơ đồ Flowchart (Luồng chức năng logic) và 1 Sơ đồ Sequence Diagram (Tuần tự giao tiếp) bằng mã Mermaid.js dựa trên tài liệu trên."
        else:
            user_prompt = f"### SRS DOCUMENT DETAILS (FROM BA AGENT):\n{srs_context}\n\n"
            user_prompt += "Please draw 1 Flowchart describing functional flows and 1 Sequence diagram describing system interactions using Mermaid.js code based on the document above."
            
        # Layer 3: Retry nhẹ (có kiểm soát) qua việc bắt Exception ở phía FSM sau này nếu cần
        # Tạm thời cứ gọi LLM
        result = self.call_llm(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            pydantic_schema=DiagramOutput
        )
        
        # Layer 2: Sanitizer - Tẩy rửa markdown thừa
        result.flowchart_diagram = sanitize_mermaid(result.flowchart_diagram)
        result.sequence_diagram = sanitize_mermaid(result.sequence_diagram)
        
        return result
