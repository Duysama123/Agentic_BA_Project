import os
import json
import time as _time
from google import genai
from google.genai import types
from typing import Type, Any, Dict, Optional
from pydantic import BaseModel, ValidationError

# Đảm bảo đường dẫn module chạy đúng mọi nơi
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.config import Config, config
from core.logger import setup_logger

logger = setup_logger("BaseAgent")

# ====== ROUND-ROBIN KEY POOL (Module-level Singleton) ====== #
_api_keys = Config.get_api_keys()
_key_index = 0  # Con trỏ đang chĩa vào key nào

def _get_next_key():
    """Bốc key tiếp theo trong vòng xoay. Mỗi lần gọi = nhảy sang key kế."""
    global _key_index
    if not _api_keys:
        raise ValueError("Không tìm thấy API Key nào! Kiểm tra GEMINI_API_KEY hoặc GEMINI_API_KEYS trong .env")
    key = _api_keys[_key_index % len(_api_keys)]
    _key_index += 1
    return key

class BaseAgent:
    """Lớp nền tảng cho mọi Agent trong hệ thống Multi-Agent giao tiếp với Gemini LLM.
    Chức năng chính: Đóng gói kịch bản Gọi API, Xử lý lỗi (Exception), và Format Dữ liệu (JSON Data Contract) qua package google-genai mới nhất.
    Tích hợp Round-Robin Key Pool + Auto-Retry để chống chọi với API Quota Limit.
    """
    
    def __init__(self, role_name: str, model_name: str = "gemini-2.5-flash"):
        self.role_name = role_name
        self.model_name = model_name
        
        if not _api_keys:
            logger.critical("Thiếu cấu hình GEMINI_API_KEY trong file .env!")
            raise ValueError("GEMINI_API_KEY is missing or invalid. Please update .env file.")
            
        # Khởi tạo Client với key đầu tiên (sẽ xoay khi call_llm)
        self.client = genai.Client(api_key=_api_keys[0])
        logger.info(f"Đã khởi tạo [{self.role_name}] sử dụng não bộ {self.model_name} | Key Pool: {len(_api_keys)} key(s)")

    # Bảng Model dự phòng: nếu model chính bận, tụt xuống model phụ 
    FALLBACK_MODELS = {
        "gemini-2.5-flash": "gemini-2.0-flash",
        "gemini-2.5-pro": "gemini-2.0-flash",
    }

    def call_llm(self, system_prompt: str, user_prompt: str, pydantic_schema: Type[BaseModel] = None, image_data=None) -> Any:
        """Thực thi Gọi LLM với cơ chế Round-Robin Key + Auto-Retry + Fallback Model.
        Chiến lược: Xoay key → Nếu tất cả key đều lỗi → Đổi sang Model dự phòng → Xoay key lại.
        """
        
        models_to_try = [self.model_name]
        fallback = self.FALLBACK_MODELS.get(self.model_name)
        if fallback:
            models_to_try.append(fallback)
        
        last_error = None
        
        for model_idx, current_model in enumerate(models_to_try):
            max_retries = max(len(_api_keys), 2)
            
            if model_idx > 0:
                logger.warning(f"[{self.role_name}] 🔄 Model {models_to_try[model_idx-1]} quá tải! Chuyển sang dự phòng: {current_model}")
            
            for attempt in range(max_retries):
                current_key = _get_next_key()
                self.client = genai.Client(api_key=current_key)
                key_suffix = current_key[-6:]
                
                logger.debug(f"[{self.role_name}] Model={current_model} | Attempt {attempt+1}/{max_retries} | Key ...{key_suffix}")
                
                config_args = {
                    "temperature": 0.2,
                    "system_instruction": system_prompt
                }
                
                if pydantic_schema:
                    config_args["response_mime_type"] = "application/json"
                    config_args["response_schema"] = pydantic_schema
                    
                gen_config = types.GenerateContentConfig(**config_args)
                    
                contents = [user_prompt]
                if image_data:
                    contents.append(image_data)
                    
                try:
                    response = self.client.models.generate_content(
                        model=current_model,
                        contents=contents,
                        config=gen_config
                    )
                    
                    if pydantic_schema and hasattr(response, 'parsed') and response.parsed is not None:
                        if model_idx > 0:
                            logger.info(f"[{self.role_name}] ✅ Thành công với model dự phòng {current_model}!")
                        return response.parsed
                        
                    if pydantic_schema:
                        try:
                            clean_json = response.text.strip()
                            if clean_json.startswith("```json"):
                                clean_json = clean_json[7:-3].strip()
                            elif clean_json.startswith("```"):
                                clean_json = clean_json[3:-3].strip()
                                
                            data_dict = json.loads(clean_json)
                            return pydantic_schema(**data_dict)
                        except json.JSONDecodeError as e:
                            logger.error(f"[{self.role_name}] Lỗi Parse JSON: {e}")
                            raise
                        except ValidationError as e:
                            logger.error(f"[{self.role_name}] Lỗi Data Contract: {e}")
                            raise
                    
                    try:
                        return json.loads(response.text)
                    except:
                        return response.text
                    
                except Exception as e:
                    last_error = e
                    error_str = str(e)
                    is_retryable = (
                        "429" in error_str or "503" in error_str or 
                        "RESOURCE_EXHAUSTED" in error_str or "UNAVAILABLE" in error_str or
                        "403" in error_str or "PERMISSION_DENIED" in error_str or
                        "API key not valid" in error_str
                    )
                    
                    if is_retryable and attempt < max_retries - 1:
                        wait_time = (attempt + 1) * 3
                        logger.warning(f"[{self.role_name}] Key ...{key_suffix} lỗi ({error_str[:50]}...). Đổi key, chờ {wait_time}s...")
                        _time.sleep(wait_time)
                        continue
                    elif is_retryable and model_idx < len(models_to_try) - 1:
                        # Hết key cho model này → nhảy sang model dự phòng
                        logger.warning(f"[{self.role_name}] Hết key cho {current_model}. Thử model dự phòng...")
                        break
                    else:
                        logger.error(f"[{self.role_name}] Gọi LLM Thất bại: {error_str}")
                        raise e
        
        # Nếu tất cả model + key đều thất bại
        raise last_error


