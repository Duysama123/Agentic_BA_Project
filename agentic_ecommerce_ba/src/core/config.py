import os
from dotenv import load_dotenv

# Load biến môi trường từ file .env
load_dotenv()

class Config:
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
    
    # Hỗ trợ nhiều API Key xoay vòng (Round-robin)
    # Trong .env, khai báo nhiều key cách nhau bằng dấu phẩy:
    # GEMINI_API_KEYS=key1,key2,key3
    # Nếu không có GEMINI_API_KEYS, dùng GEMINI_API_KEY đơn lẻ.
    @staticmethod
    def get_api_keys():
        multi_keys = os.getenv("GEMINI_API_KEYS", "")
        if multi_keys and multi_keys.strip():
            return [k.strip() for k in multi_keys.split(",") if k.strip()]
        single_key = os.getenv("GEMINI_API_KEY", "")
        if single_key and single_key.strip():
            return [single_key.strip()]
        return []
    
    # Cấu hình đường dẫn (Paths)
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    DATA_DIR = os.path.join(BASE_DIR, "data")
    KNOWLEDGE_BASE_DIR = os.path.join(DATA_DIR, "knowledge_base")
    RAW_WIREFRAMES_DIR = os.path.join(DATA_DIR, "raw_wireframes")
    
    # Cấu hình RAG
    EMBEDDING_MODEL_NAME = "all-MiniLM-L6-v2"
    CHUNK_SIZE = 500
    CHUNK_OVERLAP = 50
    
    # Khác
    LOG_LEVEL = os.getenv("LOG_LEVEL", "DEBUG")
    
    # Cấu hình tối ưu hóa chống Rate Limit trên Free Tier
    GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.0-flash")

    GEMINI_STREAMING = os.getenv("GEMINI_STREAMING", "true").lower() in ("true", "1", "yes")

config = Config()

