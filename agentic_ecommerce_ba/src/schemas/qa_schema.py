from pydantic import BaseModel, Field
from typing import List, Literal

class QAStructuralCheck(BaseModel):
    type: Literal["error", "warning"] = Field(description="Loại kiểm tra: error hoặc warning")
    path: str = Field(description="Đường dẫn đến thuộc tính lỗi. VD: 'UC-02.alternative_flows' hoặc 'ERD.orders'")
    message: str = Field(description="Thông báo lỗi. VD: 'Missing', 'No primary key defined'")

class QAConsistencyCheck(BaseModel):
    type: Literal["error", "warning"] = Field(description="Loại lỗi consistency")
    message: str = Field(description="Thông báo. VD: 'Screen PromoPage from wireframe has no matching use case in SRS'")

class QADomainCheck(BaseModel):
    id: str = Field(description="Mã lỗi, VD: 'EC-02'")
    severity: Literal["CRITICAL", "HIGH", "MEDIUM", "LOW"] = Field(description="Mức độ nghiêm trọng")
    message: str = Field(description="Mô tả lỗi vi phạm quy tắc e-commerce")
    passed: bool = Field(description="Quy tắc này có thoả mãn hay không?")

class QADecision(BaseModel):
    action: Literal["approve", "retry_ba", "retry_da"] = Field(description="Quyết định cuối cùng")
    reason: str = Field(description="Lý do cho quyết định này")

class QAAuditReport(BaseModel):
    is_approved: bool = Field(default=False)
    structural_checks: List[QAStructuralCheck] = Field(default_factory=list)
    consistency_checks: List[QAConsistencyCheck] = Field(default_factory=list)
    domain_checks: List[QADomainCheck] = Field(default_factory=list)
    decision: QADecision = Field(default=None)
    feedback_for_agents: str = Field(default="")
    structural_errors_count: int = Field(default=0, description="Số lượng lỗi cấu trúc")
    entity_consistency_score: float = Field(default=100.0, description="Điểm nhất quán thực thể (%)")
    domain_policy_compliance_rate: float = Field(default=100.0, description="Tỷ lệ tuân thủ chính sách (%)")
    edge_case_density: float = Field(default=0.0, description="Mật độ trường hợp ngoại lệ")

