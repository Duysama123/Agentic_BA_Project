import os
import PyPDF2
from typing import List

def extract_text_from_pdf(pdf_path: str) -> str:
    """Đọc toàn bộ văn bản từ file PDF."""
    if not os.path.exists(pdf_path):
        raise FileNotFoundError(f"Không tìm thấy file tài liệu tại: {pdf_path}")
        
    text = ""
    # Đọc nhị phân ('rb') để PyPDF2 xử lý đúng
    with open(pdf_path, 'rb') as file:
        reader = PyPDF2.PdfReader(file)
        for page in reader.pages:
            extracted = page.extract_text()
            if extracted:
                text += extracted + "\n"
                
    return text.strip()

def sliding_window_chunking(text: str, chunk_size: int = 400, overlap: int = 50) -> List[str]:
    """Cắt văn bản thành các đoạn nhỏ (chunk) sử dụng thuật toán Cửa sổ trượt.
    Code thuần Python không dùng Langchain để tối ưu hoá điểm số tự làm cốt lõi.
    
    Args:
        text (str): Văn bản gốc cần cắt chữ.
        chunk_size (int): Số lượng từ vựng (words) tối đa trong 1 đoạn.
        overlap (int): Số lượng từ vựng chồng chéo giữa đoạn sau và đoạn trước (để khỏi đứt gãy ngữ nghĩa).
        
    Returns:
        List[str]: Danh sách các đoạn văn bản.
    """
    words = text.split()
    chunks = []
    
    i = 0
    while i < len(words):
        # Lấy một đoạn từ vựng có độ dài chunk_size
        chunk_words = words[i:i + chunk_size]
        chunk_text = " ".join(chunk_words)
        chunks.append(chunk_text)
        
        # Nếu đã chạm tới cuối mảng từ thì dừng vòng lặp
        if i + chunk_size >= len(words):
            break
            
        # Trượt index lên phía trước với độ dài hụt đi overlap
        i += (chunk_size - overlap)
        
    return chunks

def process_document(pdf_path: str, chunk_size: int = 400, overlap: int = 50) -> List[str]:
    """Hàm chạy từ A đến Z cho 1 file PDF: Đọc text -> Cắt Chunk."""
    raw_text = extract_text_from_pdf(pdf_path)
    chunks = sliding_window_chunking(raw_text, chunk_size, overlap)
    return chunks
