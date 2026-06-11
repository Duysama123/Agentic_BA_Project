import requests
import uuid

url = "https://lgfnexklmxzsltewmrum.supabase.co"
key = "sb_publishable_8uS7-QVVNYLvZtZ0RbzbnA_Za6NTR4n"

headers = {
    "apikey": key,
    "Authorization": f"Bearer {key}",
    "Content-Type": "application/json",
    "Prefer": "return=representation"
}

session_id = str(uuid.uuid4())
dummy_user_id = str(uuid.uuid4())

payload = {
    "id": session_id,
    "user_id": dummy_user_id,
    "input_image_name": "Test Image",
    "total_processing_time": 0,
    "final_status": "processing"
}

res = requests.post(f"{url}/rest/v1/eval_sessions", headers=headers, json=payload)
print(f"Status Code: {res.status_code}")
print(f"Response: {res.text}")
