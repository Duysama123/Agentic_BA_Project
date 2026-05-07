from pydantic import BaseModel, Field

class DiagramOutput(BaseModel):
    flowchart_diagram: str = Field(description="Mã nguồn Mermaid.js cho lược đồ Flowchart mô tả luồng logic rẽ nhánh")
    sequence_diagram: str = Field(description="Mã nguồn Mermaid.js cho lược đồ Sequence Diagram mô tả tuần tự giao tiếp giữa Actor và Hệ thống")
    diagram_explanation: str = Field(description="Đoạn văn ngắn (1-2 câu) giải thích các đồ thị trên")
