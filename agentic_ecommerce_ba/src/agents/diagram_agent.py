import os
import sys
import re

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agents.base_agent import BaseAgent
from schemas.diagram_schema import DiagramOutput
from core.i18n import t, get_lang

def sanitize_mermaid(mermaid_code: str) -> str:
    """
    Layer 2: Post-processing sanitizer.
    Removes markdown fences, fixes common LLM mistakes, and ensures 
    the string is valid raw Mermaid code renderable by mermaid.js.
    """
    if not mermaid_code:
        return ""
    
    code = mermaid_code.strip()
    
    # Remove markdown code fences (```mermaid ... ```)
    if "```mermaid" in code:
        code = code.split("```mermaid", 1)[1]
        if "```" in code:
            code = code.rsplit("```", 1)[0]
    elif code.startswith("```"):
        lines = code.split("\n")
        # Remove first line (```xxx) and last line (```)
        if lines[-1].strip() == "```":
            lines = lines[1:-1]
        else:
            lines = lines[1:]
        code = "\n".join(lines)
    
    code = code.strip()
    
    def fix_labels(match):
        node_id = match.group(1)
        shape_open = match.group(2)
        content = match.group(3)
        shape_close = match.group(4)
        
        # If the content is already quoted, do not double-quote it
        content_stripped = content.strip()
        if (content_stripped.startswith('"') and content_stripped.endswith('"')) or \
           (content_stripped.startswith("'") and content_stripped.endswith("'")):
            return match.group(0)
            
        # Clean double quotes inside content and wrap with double quotes
        cleaned_content = content.replace('"', "'").strip()
        return f'{node_id}{shape_open}"{cleaned_content}"{shape_close}'
    
    # Only apply to flowchart sections
    if code.startswith("flowchart") or code.startswith("graph"):
        code = re.sub(r'([A-Za-z0-9_-]+)\s*(\[|\{|\(\(|\()([^\]\}\)]+)(\]|\}|\)\)|\))', fix_labels, code)
        
        # Guardrail: Remove empty arrow labels that crash dagre layout
        # Convert -->|| or -->| | to just -->
        code = re.sub(r'-->\|\s*\|', '-->', code)
        code = re.sub(r'-\.-\>\|\s*\|', '-.->', code)
        code = re.sub(r'==>\|\s*\|', '==>', code)
        
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
            
        # Retry up to 2 times for diagram generation
        max_retries = 2
        last_error = None
        
        for attempt in range(max_retries + 1):
            try:
                result = self.call_llm(
                    system_prompt=system_prompt,
                    user_prompt=user_prompt,
                    pydantic_schema=DiagramOutput
                )
                
                # Layer 2: Sanitizer
                result.flowchart_diagram = sanitize_mermaid(result.flowchart_diagram)
                result.sequence_diagram = sanitize_mermaid(result.sequence_diagram)
                
                # Basic validation: ensure each diagram starts with the correct keyword
                fc = result.flowchart_diagram.strip()
                sq = result.sequence_diagram.strip()
                
                if fc and not (fc.startswith("flowchart") or fc.startswith("graph")):
                    result.flowchart_diagram = "flowchart TD\n" + fc
                
                if sq and not sq.startswith("sequenceDiagram"):
                    result.sequence_diagram = "sequenceDiagram\n" + sq
                
                return result
                
            except Exception as e:
                last_error = e
                if attempt < max_retries:
                    continue
        
        # If all retries failed, return empty diagrams with error explanation
        return DiagramOutput(
            flowchart_diagram="flowchart TD\n    A[Start] --> B[Error generating diagram]",
            sequence_diagram="sequenceDiagram\n    Note over System: Diagram generation failed after retries",
            diagram_explanation=f"Diagram generation encountered an error: {last_error}"
        )
