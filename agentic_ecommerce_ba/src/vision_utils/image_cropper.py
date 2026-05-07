import cv2
import numpy as np
from typing import List, Tuple

def find_ui_components(binary_image: np.ndarray, min_area: int = 500) -> List[Tuple[int, int, int, int]]:
    """Phân tách các khối (Button, TextBox) từ ảnh nhị phân dùng thuật toán FindContours.
    
    Args:
        binary_image: Ảnh Trắng/Đen sinh ra từ enhancer.py.
        min_area: Diện tích tối thiểu để được coi là 1 thành phần UI (loại bỏ chấm mực rớt).
        
    Returns:
        Danh sách các tuple (x, y, w, h) biểu diễn Bounding Box.
    """
    # Tìm viền góc cạnh (contours). 
    # cv2.RETR_EXTERNAL: Chỉ lấy các khối bao ngoài lớn nhất (tránh lấy vòng tròn trong chữ 'O')
    contours, _ = cv2.findContours(binary_image, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    
    bounding_boxes = []
    for contour in contours:
        area = cv2.contourArea(contour)
        if area > min_area:
            # Lấy toạ độ hộp chữ nhật bao bọc nét vẽ
            x, y, w, h = cv2.boundingRect(contour)
            bounding_boxes.append((x, y, w, h))
            
    # Sắp xếp các box từ trên xuống dưới (theo trục y)
    bounding_boxes = sorted(bounding_boxes, key=lambda b: b[1])
    return bounding_boxes

def draw_bounding_boxes(original_image: np.ndarray, boxes: List[Tuple[int, int, int, int]]) -> np.ndarray:
    """Vẽ lại các hộp chữ nhật Xanh Lá lên ảnh gốc để Giám khảo/Người duyệt xem (Hiển thị lên Streamlit)."""
    output_img = original_image.copy()
    for (x, y, w, h) in boxes:
        # Xanh lá (BGR), nét vẽ 2px
        cv2.rectangle(output_img, (x, y), (x + w, y + h), (0, 255, 0), 2)
    return output_img

def crop_elements(image: np.ndarray, boxes: List[Tuple[int, int, int, int]]) -> List[np.ndarray]:
    """Cắt từng vùng UI ra thành danh sách ảnh con độc lập."""
    cropped_images = []
    for (x, y, w, h) in boxes:
        # OpenCV slicing: image[y_start:y_end, x_start:x_end]
        cropped = image[y:y+h, x:x+w]
        cropped_images.append(cropped)
    return cropped_images
