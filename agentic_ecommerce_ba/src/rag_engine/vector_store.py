import os
import logging
import warnings

# Tắt toàn bộ thông báo cảnh báo (warnings) rác của HuggingFace và Transformers để cửa sổ Cmd sạch đẹp
os.environ["HF_HUB_DISABLE_SYMLINKS_WARNING"] = "1"
os.environ["TRANSFORMERS_VERBOSITY"] = "error"
os.environ["TOKENIZERS_PARALLELISM"] = "false"

# Ẩn các cảnh báo nội bộ của Pytorch/Transformers
logging.getLogger("transformers").setLevel(logging.ERROR)
warnings.filterwarnings("ignore")

import faiss
import numpy as np
from sentence_transformers import SentenceTransformer
from typing import List, Dict

class RAGVectorStore:
    def __init__(self, model_name: str = 'all-MiniLM-L6-v2'):
        """Khởi tạo FAISS Index và Load Engine Embeddings nội bộ (Local).
        Lý do dùng all-MiniLM-L6-v2: Nhỏ nhẹ, sinh Vector 384 chiều, tìm kiếm siêu tốc.
        """
        # Load model embedding (Cần mạng internet lần chạy đầu tiên để nó tải model về cache)
        self.encoder = SentenceTransformer(model_name)
        
        # Lấy kích thước vector. Với MiniLM-L6 thì biến này = 384
        self.embedding_dim = self.encoder.get_sentence_embedding_dimension()
        
        # Sử dụng thuật toán faiss.IndexFlatL2 (Tính khoảng cách Euclidean).
        # Khi Vector được chuẩn hoá bằng hàm normalize_L2, khoảng cách này tỷ lệ thuận với Cosine Similarity.
        self.index = faiss.IndexFlatL2(self.embedding_dim)
        
        # Mapping giữa số ID tự tăng (Vector Node) và đoạn text tương ứng
        self.document_map: Dict[int, str] = {}
        self.current_id = 0
        
    def add_chunks(self, chunks: List[str]):
        """Chuyển hoá văn bản (Chunks) thành số thực Vector và add vào CPU RAM (FAISS)."""
        if not chunks:
            return
            
        # 1. Mã hoá Text thành Vector NumPy
        embeddings = self.encoder.encode(chunks, convert_to_numpy=True)
        
        # 2. Bắt buộc: Chuẩn hoá Vector (Normalize) để IndexFlatL2 hoạt động như Cosine 
        faiss.normalize_L2(embeddings)
        
        # 3. Add vào FAISS Database
        self.index.add(embeddings)
        
        # 4. Map vào Dictionary để sau này truy ngược lại text
        for chunk in chunks:
            self.document_map[self.current_id] = chunk
            self.current_id += 1
            
    def search(self, query: str, top_k: int = 3) -> List[str]:
        """Tìm kiếm các chunks/luật liên quan nhất dựa theo câu hỏi của BA Agent."""
        if self.current_id == 0:
            return []
            
        # 1. Biến câu hỏi thành Vector và Chuẩn hoá
        query_vector = self.encoder.encode([query], convert_to_numpy=True)
        faiss.normalize_L2(query_vector)
        
        # 2. Search FAISS (trả về distances và mảng các index nằm trong Range)
        distances, indices = self.index.search(query_vector, top_k)
        
        # 3. Lấy text gốc từ Mapping để làm Input Prompt cho LLM
        results = []
        # Chú ý: FAISS trả indices là nested array 2 chiều cho nhiều batch câu hỏi. Ta lấy [0].
        for idx in indices[0]:
            if idx != -1 and idx in self.document_map:
                results.append(self.document_map[idx])
                
        return results
