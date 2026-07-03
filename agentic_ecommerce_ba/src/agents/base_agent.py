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
_key_index = 0  # Con trỏ đang chĩa vào key nào

def _get_next_key():
    """Bốc key tiếp theo trong vòng xoay. Mỗi lần gọi = nhảy sang key kế."""
    global _key_index
    keys = Config.get_api_keys()
    if not keys:
        raise ValueError("Không tìm thấy API Key nào! Hãy nhập API Key của bạn hoặc thiết lập biến môi trường GEMINI_API_KEY / GEMINI_API_KEYS")
    key = keys[_key_index % len(keys)]
    _key_index += 1
    return key

class BaseAgent:
    """Lớp nền tảng cho mọi Agent trong hệ thống Multi-Agent giao tiếp với Gemini LLM.
    Chức năng chính: Đóng gói kịch bản Gọi API, Xử lý lỗi (Exception), và Format Dữ liệu (JSON Data Contract) qua package google-genai mới nhất.
    Tích hợp Round-Robin Key Pool + Auto-Retry để chống chọi với API Quota Limit.
    """
    
    def __init__(self, role_name: str, model_name: str = "gemini-2.5-flash", force_model: bool = False):
        self.role_name = role_name
        # Sử dụng mô hình ghi đè từ Config/môi trường nếu có, ngược lại dùng mặc định của Agent
        if force_model:
            self.model_name = model_name
        else:
            self.model_name = os.getenv("GEMINI_MODEL", model_name)
        
        # Khởi tạo Client với key đầu tiên khả dụng tại thời điểm khởi tạo
        keys = Config.get_api_keys()
        if not keys:
            logger.warning(f"Chưa có API Key nào cấu hình lúc khởi tạo [{self.role_name}]. Người dùng cần nhập API Key ở giao diện.")
            self.client = None
        else:
            self.client = genai.Client(api_key=keys[0])
            logger.info(f"Đã khởi tạo [{self.role_name}] sử dụng não bộ {self.model_name} | Key Pool: {len(keys)} key(s)")

    def call_llm(self, system_prompt: str, user_prompt: str, pydantic_schema: Type[BaseModel] = None, image_data=None) -> Any:
        """Thực thi Gọi LLM với cơ chế Round-Robin Key + Auto-Retry."""
        system_prompt += "\n\nCRITICAL RULE: You MUST output all your responses, JSON values, and descriptions in ENGLISH ONLY."
        
        self.last_run_metadata = {
            "time": 0.0,
            "tokens": 0,
            "input_tokens": 0,
            "output_tokens": 0
        }
        start_time = _time.time()
        
        # Chỉ sử dụng duy nhất gemini-2.5-flash để tránh 404
        models_to_try = [self.model_name]
        if "gemini-2.5-flash" not in models_to_try:
            models_to_try.append("gemini-2.5-flash")
            
        last_error = None
        
        for model_idx, current_model in enumerate(models_to_try):
            keys = Config.get_api_keys()
            num_keys = len(keys)
            max_retries = num_keys + 1
            exhausted_keys = set()
            
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
                    
                    if hasattr(response, 'usage_metadata') and response.usage_metadata:
                        self.last_run_metadata['tokens'] = getattr(response.usage_metadata, 'total_token_count', 0)
                        self.last_run_metadata['input_tokens'] = getattr(response.usage_metadata, 'prompt_token_count', 0)
                        self.last_run_metadata['output_tokens'] = getattr(response.usage_metadata, 'candidates_token_count', 0)
                    
                    self.last_run_metadata['time'] = round(_time.time() - start_time, 2)
                    
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
                        except (json.JSONDecodeError, ValidationError) as e:
                            logger.error(f"[{self.role_name}] Lỗi Parse JSON hoặc Validation: {e}")
                            raise
                    
                    try:
                        res_json = json.loads(response.text)
                        return res_json
                    except:
                        return response.text
                    
                except Exception as e:
                    last_error = e
                    error_str = str(e)
                    is_rate_limit = "429" in error_str or "RESOURCE_EXHAUSTED" in error_str
                    is_retryable = (
                        is_rate_limit or "503" in error_str or "UNAVAILABLE" in error_str or
                        "403" in error_str or "PERMISSION_DENIED" in error_str or
                        "API key not valid" in error_str
                    )
                    
                    if is_rate_limit:
                        exhausted_keys.add(key_suffix)
                        if len(exhausted_keys) >= num_keys and model_idx < len(models_to_try) - 1:
                            logger.warning(f"[{self.role_name}] Tất cả key đều bị rate-limit. Đổi model...")
                            break
                    
                    if is_retryable and attempt < max_retries - 1:
                        wait_time = 5
                        logger.warning(f"[{self.role_name}] Key ...{key_suffix} lỗi. Chờ {wait_time}s...")
                        _time.sleep(wait_time)
                        continue
                    elif is_retryable and model_idx < len(models_to_try) - 1:
                        break
                    else:
                        logger.error(f"[{self.role_name}] Gọi LLM Thất bại: {error_str}")
                        raise e
        
        raise last_error

    def call_llm_stream(self, system_prompt: str, user_prompt: str, image_data: Any = None, 
                       pydantic_schema: Optional[Type[BaseModel]] = None, 
                       stream_callback: Optional[callable] = None) -> Any:
        """Streaming variant of call_llm."""
        system_prompt += "\n\nCRITICAL RULE: You MUST output all your responses, JSON values, and descriptions in ENGLISH ONLY."
        
        self.last_run_metadata = {
            "time": 0.0,
            "tokens": 0,
            "input_tokens": 0,
            "output_tokens": 0
        }
        start_time = _time.time()
        
        models_to_try = [self.model_name]
        if "gemini-2.5-flash" not in models_to_try:
            models_to_try.append("gemini-2.5-flash")
            
        last_error = None
        
        for model_idx, current_model in enumerate(models_to_try):
            keys = Config.get_api_keys()
            num_keys = len(keys)
            max_retries = num_keys + 1
            exhausted_keys = set()
            
            if model_idx > 0:
                logger.warning(f"[{self.role_name}] 🔄 Model {models_to_try[model_idx-1]} quá tải! Chuyển sang dự phòng: {current_model}")
            
            for attempt in range(max_retries):
                current_key = _get_next_key()
                self.client = genai.Client(api_key=current_key)
                key_suffix = current_key[-6:]
                
                logger.debug(f"[{self.role_name}] Stream Model={current_model} | Attempt {attempt+1}/{max_retries} | Key ...{key_suffix}")
                
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
                    response_stream = self.client.models.generate_content_stream(
                        model=current_model,
                        contents=contents,
                        config=gen_config
                    )
                    
                    full_text = ""
                    for chunk in response_stream:
                        if chunk.text:
                            full_text += chunk.text
                            if stream_callback:
                                try:
                                    stream_callback(full_text)
                                except Exception: pass
                                
                    self.last_run_metadata['time'] = round(_time.time() - start_time, 2)
                    
                    if pydantic_schema:
                        try:
                            clean_json = full_text.strip()
                            if clean_json.startswith("```json"):
                                clean_json = clean_json[7:-3].strip()
                            elif clean_json.startswith("```"):
                                clean_json = clean_json[3:-3].strip()
                            data_dict = json.loads(clean_json)
                            return pydantic_schema(**data_dict)
                        except (json.JSONDecodeError, ValidationError) as e:
                            logger.error(f"[{self.role_name}] Stream Lỗi Parse JSON hoặc Validation: {e}")
                            raise
                            
                    try:
                        res_json = json.loads(full_text)
                        return res_json
                    except:
                        return full_text
                        
                except Exception as e:
                    last_error = e
                    error_str = str(e)
                    is_rate_limit = "429" in error_str or "RESOURCE_EXHAUSTED" in error_str
                    is_retryable = (
                        is_rate_limit or "503" in error_str or "UNAVAILABLE" in error_str or
                        "403" in error_str or "PERMISSION_DENIED" in error_str or
                        "API key not valid" in error_str
                    )
                    
                    if is_rate_limit:
                        exhausted_keys.add(key_suffix)
                        if len(exhausted_keys) >= num_keys and model_idx < len(models_to_try) - 1:
                            logger.warning(f"[{self.role_name}] Stream: Hết key cho {current_model}. Đổi model...")
                            break
                            
                    if is_retryable and attempt < max_retries - 1:
                        wait_time = 5
                        logger.warning(f"[{self.role_name}] Stream: Key ...{key_suffix} lỗi. Đổi key, chờ {wait_time}s...")
                        _time.sleep(wait_time)
                        continue
                    elif is_retryable and model_idx < len(models_to_try) - 1:
                        break
                    else:
                        logger.error(f"[{self.role_name}] Stream Thất bại: {error_str}")
                        raise e
                        
        raise last_error
