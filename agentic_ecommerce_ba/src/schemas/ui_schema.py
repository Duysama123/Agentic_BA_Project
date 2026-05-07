from pydantic import BaseModel, Field
from typing import List, Optional

class UIElement(BaseModel):
    id: str = Field(description="ID định danh viết liền, không dấu của component (VD: btn_checkout, input_email)")
    type: str = Field(description="Loại component (Hỗ trợ: button, text_input, image, dropdown, text_label)")
    label: Optional[str] = Field(description="Chữ viết trên component nếu AI đọc được (VD: 'Thanh toán', 'Thêm vào giỏ')")
    description: str = Field(description="Mô tả chi tiết tác dụng, hình khối hoặc vị trí của component này trên màn hình")

class WireframeAnalysis(BaseModel):
    page_name: str = Field(description="Tên dự đoán của trang giao diện (VD: Trang Thanh Toán Chi tiết)")
    elements: List[UIElement] = Field(description="Danh sách mảng chứa toàn bộ các thành phần UI rời rạc xuất hiện trên bản vẽ")
    detected_user_flows: List[str] = Field(description="Dự đoán mô tả các luồng hành vi mà người dùng có thể thực hiện khi bấm vào các element trên trang này")
