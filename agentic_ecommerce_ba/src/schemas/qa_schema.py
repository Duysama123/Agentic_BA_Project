from pydantic import BaseModel, Field
from typing import List, Literal

class Discrepancy(BaseModel):
    module_source: Literal["Vision", "BA_SRS", "Data_Architect", "Diagram", "Cross_Module"] = Field(description="Phân hệ nào đang gặp lấn cấn hoặc có lỗi logic chéo (Cross-Module)")
    description: str = Field(description="Mô tả sự mâu thuẫn rõ ràng. (VD: Hình báo có chức năng 'Scan Voucher' nhưng BA không viết Functional Rule, Database cũng không có cột lưu 'Voucher')")
    severity: Literal["low", "medium", "high", "critical"] = Field(description="Mức độ nghiêm trọng của sai ngạch này")

class QAAuditReport(BaseModel):
    is_approved: bool = Field(description="True nếu không có lỗi lớn, mọi thứ ăn khớp. False nếu phát hiện lấn cấn nghiêm trọng (Từ chối duyệt).")
    discrepancies: List[Discrepancy] = Field(default=[], description="Danh sách các điểm mâu thuẫn, thiếu sót bắt được sau khi chiếu chéo 3 file JSON.")
    feedback_for_agents: str = Field(description="Lời chỉ dẫn tổng quát để các bot trước tự fix lỗi vào lần chạy sau.")
