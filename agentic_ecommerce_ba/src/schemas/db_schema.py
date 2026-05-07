from pydantic import BaseModel, Field
from typing import List, Optional

class ColumnDef(BaseModel):
    name: str = Field(description="Tên cột (VD: id, user_id, price)")
    data_type: str = Field(description="Kiểu dữ liệu SQL (VD: VARCHAR(255), INT, DECIMAL, TIMESTAMP)")
    is_primary_key: bool = Field(default=False, description="Đánh dấu nếu đây là Khoá chính")
    is_foreign_key: bool = Field(default=False, description="Đánh dấu nếu đây là Khoá ngoại")
    references: Optional[str] = Field(default=None, description="Tên bảng và cột tham chiếu (VD: users.id)")
    description: str = Field(description="Giải thích ngắn gọn ý nghĩa của cột")

class TableDef(BaseModel):
    name: str = Field(description="Tên bảng dữ liệu (VD: users, orders)")
    description: str = Field(description="Miêu tả ngắn gọn vai trò của bảng")
    columns: List[ColumnDef]

class DatabaseSchema(BaseModel):
    tables: List[TableDef] = Field(description="Danh sách các thiết kế Cấu trúc bảng")
    relationships: List[str] = Field(description="Giải nghĩa bằng văn bản các Mối quan hệ giữa các bảng")
    erd_mermaid: str = Field(description="Mã nguồn loại `erDiagram` của Mermaid.js vẽ sơ đồ cấu trúc Thực thể - Liên kết")
