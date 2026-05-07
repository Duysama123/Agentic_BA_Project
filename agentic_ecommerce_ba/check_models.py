import google.generativeai as genai
import os
from dotenv import load_dotenv

load_dotenv(".env")
api_key = os.getenv("GEMINI_API_KEY")

if not api_key or "your_gemini_api_key_here" in api_key:
    print("NO_API_KEY_FOUND_OR_INVALID")
else:
    genai.configure(api_key=api_key)
    try:
        models = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
        print(f"AVAILABLE_MODELS_FOR_GENERATE: {models}")
    except Exception as e:
        print(f"API_ERROR: {e}")
