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
    
    if code:
        # Heal corrupted stadium shape from history (e.g. "End('[End'") -> End(["End"])
        code = re.sub(
            r'"([A-Za-z0-9_-]+)\s*\(\s*\'\s*\[\s*([^\]\'\n]+?)\s*\'\s*"\s*\]\s*\)',
            r'\1(["\2"])',
            code
        )
        # Heal corrupted rectangle shape from history (e.g. "AccessPage['Access...'"] -> AccessPage["Access..."])
        code = re.sub(
            r'"([A-Za-z0-9_-]+)\s*\[\s*\'(.*?)\'\s*"\s*\]',
            r'\1["\2"]',
            code
        )
        # Correct the corrupted stadium node formatting where closing bracket is inside parentheses or misplaced
        code = re.sub(
            r'([A-Za-z0-9_-]+)\(\s*["\']?\s*\[\s*["\']?\s*([^\]"\'\n]+?)\s*["\']?\s*\]\s*["\']?\s*\)',
            r'\1(["\2"])',
            code
        )
    
    # ── SINGLE-LINE MERMAID CODE SPLITTER (FOR HISTORY OR LITE RUNS) ──
    # If the code is formatted on a single line or has almost no newlines,
    # split it systematically to allow proper parsing by Mermaid rendering engines.
    if code and (("\n" not in code) or (code.count("\n") <= 1)):
        # Normalize double spaces to single space to keep splitting stable
        code = re.sub(r' {2,}', ' ', code)
        
        # Check if flowchart/graph
        if code.startswith("flowchart") or code.startswith("graph"):
            # Split header, e.g., "flowchart TD " -> "flowchart TD\n    "
            code = re.sub(r'^(flowchart\s+[A-Za-z0-9_-]+|graph\s+[A-Za-z0-9_-]+)\s+', r'\1\n    ', code)
            # Split before node definitions, e.g., " ID[" -> "\n    ID["
            code = re.sub(r'\s+(?=[A-Za-z0-9_-]+(?:\[|\(|\{))', '\n    ', code)
            # Split before connections, e.g., " ID1 -->" or " ID1 -.->" or " ID1 ==>"
            # We use lookbehind (?<!\s--) to avoid splitting inside "-- text -->" links.
            code = re.sub(r'(?<!\s--)\s+(?=[A-Za-z0-9_-]+\s+(?:-->|-.->|==>))', '\n    ', code)
            # Split before labeled connections, e.g. " ID1 -- label -->"
            code = re.sub(r'\s+(?=[A-Za-z0-9_-]+\s+--\s+[^\n-]+?\s*-->)', '\n    ', code)
            
        # Check if sequence diagram
        elif code.startswith("sequenceDiagram"):
            # Split header
            code = re.sub(r'^sequenceDiagram\s+', 'sequenceDiagram\n    ', code)
            # Split before participant definitions
            code = re.sub(r'\s+(?=participant\s+|actor\s+)', '\n    ', code)
            # Split before messages, e.g. " User->>System:"
            code = re.sub(r'\s+(?=[A-Za-z0-9_-]+\s*(?:--?>>|--?x|--?\)|-\)->|->)\s*[A-Za-z0-9_-]+\s*:)', '\n    ', code)
            # Split before control statements (alt, else, end, opt, loop, rect, Note)
            code = re.sub(r'\s+(?=alt\s+|else\s+|end\b|opt\s+|loop\s+|rect\s+|Note\s+)', '\n    ', code)
    
    # ── SHAPE LABEL FIXER ──
    # Fixes unquoted node labels for all Mermaid flowchart shapes.
    # Uses specific opening/closing pattern guards to avoid corrupting nested shapes.
    shape_pairs = [
        (r'\(\[', r'\]\)'),          # Stadium ([Text])
        (r'\[\[', r'\]\]'),          # Subroutine [[Text]]
        (r'\[\(', r'\)\]'),          # Database [(Text)]
        (r'\(\(', r'\)\)'),          # Circle ((Text))
        (r'\{\{', r'\}\}'),          # Hexagon {{Text}}
        (r'\[/', r'/\]'),            # Parallelogram [/Text/]
        (r'\[\\', r'\\\]'),          # Parallelogram alt [\Text\]
        (r'\[/', r'\\\]'),           # Trapezoid [/Text\]
        (r'\[\\', r'/\]'),           # Trapezoid alt [\Text/]
        (r'(?<!\()(?<!\[)\[(?!\()', r'(?<!\))\](?!\))(?!\\])(?!\/)'),  # Rectangle [Text]
        (r'(?<!\()(?<!\[)\((?!\[)', r'(?<!\])\)(?!\))(?!\\])'),         # Round (Text)
        (r'(?<!\{)\{(?!\{)', r'(?<!\})\}(?!\})'),                       # Rhombus {Text}
        (r'(?<!-)(?<!=)\>', r'\]'),              # Asymmetric >Text]
    ]
    
    if code.startswith("flowchart") or code.startswith("graph"):
        for open_pattern, close_pattern in shape_pairs:
            # Use a guarded pattern for content to stop at statement ends and never cross lines or match arrows
            pattern = r'([A-Za-z0-9_-]+)\s*' + open_pattern + r'((?:(?!-->|-.->|==>|sequenceDiagram|flowchart|graph)[^\n])*?)' + close_pattern
            
            def replacer(match):
                node_id = match.group(1)
                content = match.group(2)
                
                full_match = match.group(0)
                
                content_stripped = content.strip()
                if (content_stripped.startswith('"') and content_stripped.endswith('"')) or \
                   (content_stripped.startswith("'") and content_stripped.endswith("'")):
                    return full_match
                
                # Find the opening and closing symbols directly from the match text
                id_len = len(node_id)
                content_start_idx = full_match.find(content, id_len)
                
                op_symbol = full_match[id_len:content_start_idx]
                cl_symbol = full_match[content_start_idx + len(content):]
                
                cleaned_content = content.replace('"', "'").strip()
                return f'{node_id}{op_symbol}"{cleaned_content}"{cl_symbol}'
                
            code = re.sub(pattern, replacer, code)
        
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
        # DiagramAgent requires a capable model (gemini-2.5-flash) to guarantee correct Mermaid syntax formatting
        super().__init__(role_name="Diagram Agent", model_name="gemini-2.5-flash", force_model=True)

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
