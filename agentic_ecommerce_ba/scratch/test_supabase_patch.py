import os
import sys
import requests
import tomllib  # Built-in in Python 3.11+

def test_patch():
    secrets_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".streamlit", "secrets.toml"))
    if not os.path.exists(secrets_path):
        print("Secrets file not found at:", secrets_path)
        return
        
    with open(secrets_path, "rb") as f:
        secrets = tomllib.load(f)
        
    url = secrets.get("SUPABASE_URL", "").rstrip('/')
    key = secrets.get("SUPABASE_KEY", "")
    
    if not url or not key:
        print("Supabase credentials not found in secrets.")
        return
        
    session_id = "25882889-ef21-4ba8-88b6-21c4c3649ce9"
    endpoint = f"{url}/rest/v1/eval_sessions?id=eq.{session_id}"
    
    headers = {
        "apikey": key,
        "Content-Type": "application/json",
        "Authorization": f"Bearer {key}"
    }
    
    print("Sending PATCH request to:", endpoint)
    payload = {
        "total_processing_time": 99.9,
        "final_status": "test_patched"
    }
    
    try:
        res = requests.patch(endpoint, headers=headers, json=payload)
        print("HTTP Status Code:", res.status_code)
        print("Response Body:", res.text)
    except Exception as e:
        print("Request failed:", e)

if __name__ == "__main__":
    test_patch()
