import cv2
import numpy as np

def resize_image(image: np.ndarray, max_width: int = 1200) -> np.ndarray:
    """Giảm kích thước ảnh nếu quá lớn để tối ưu hoá tốc độ quét."""
    height, width = image.shape[:2]
    if width > max_width:
        ratio = max_width / width
        new_size = (max_width, int(height * ratio))
        return cv2.resize(image, new_size, interpolation=cv2.INTER_AREA)
    return image

def denoise_image(image: np.ndarray) -> np.ndarray:
    """Khử nhiễu ảnh dùng Median Blur (hữu ích với ảnh chụp điện thoại)."""
    return cv2.medianBlur(image, 3)

def binarize_image(image: np.ndarray) -> np.ndarray:
    """Chuyển ảnh màu sang ảnh nhị phân Trắng/Đen (Black & White).
    Sử dụng Adaptive Threshold chuyên trị ảnh vẽ tay chụp bằng điện thoại 
    bị tối/đổ bóng ở các góc.
    """
    if len(image.shape) == 3:
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    else:
        gray = image
        
    # Xoá phông mờ bằng Gaussian Blur nhẹ
    blur = cv2.GaussianBlur(gray, (5, 5), 0)
    
    # Adaptive Threshold giúp xử lý ảnh không đều sáng
    # cv2.ADAPTIVE_THRESH_GAUSSIAN_C tốt hơn MEAN_C cho nhiễu
    binary = cv2.adaptiveThreshold(
        blur, 255, 
        cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
        cv2.THRESH_BINARY_INV, 
        11, 2 # Khối 11x11, hằng số C=2. Cần test lại với ảnh thật
    )
    return binary

def enhance_wireframe(image_path: str) -> np.ndarray:
    """Pipeline tổng hợp tăng cường chất lượng ảnh Wireframe vẽ tay."""
    image = cv2.imread(image_path)
    if image is None:
        raise ValueError(f"Không thể đọc ảnh tại: {image_path}")
        
    # 1. Resize cho chuẩn
    resized = resize_image(image)
    # 2. Khử noise nhiễu hạt
    denoised = denoise_image(resized)
    # 3. Trắng đen tách nền
    binary = binarize_image(denoised)
    
    return binary
