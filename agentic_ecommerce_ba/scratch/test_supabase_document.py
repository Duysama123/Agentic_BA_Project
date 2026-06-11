import os
import sys
import requests
import json
import tomllib

def test_document_insert():
    secrets_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".streamlit", "secrets.toml"))
    if not os.path.exists(secrets_path):
        print("Secrets file not found.")
        return
        
    with open(secrets_path, "rb") as f:
        secrets = tomllib.load(f)
        
    url = secrets.get("SUPABASE_URL", "").rstrip('/')
    key = secrets.get("SUPABASE_KEY", "")
    
    session_id = "25882889-ef21-4ba8-88b6-21c4c3649ce9"
    endpoint = f"{url}/rest/v1/eval_generated_documents"
    
    headers = {
        "apikey": key,
        "Content-Type": "application/json",
        "Authorization": f"Bearer {key}"
    }
    
    # 1. Test sending raw JSON strings (current implementation)
    srs_json_str = '{"system_name": "E-Commerce System"}'
    qa_json_str = '{"metrics": [1, 2, 3]}'
    diagrams_mermaid = '{"flowchart": "graph TD;"}'
    
    data = {
        "session_id": session_id,
        "version_number": 1,
        "srs_json": srs_json_str,
        "diagrams_mermaid": diagrams_mermaid,
        "erd_sql": {"sql": "{}"},
        "qa_checklist_result": qa_json_str
    }
    
    print("Testing payload with raw strings:")
    try:
        r = requests.post(endpoint, headers=headers, json=data)
        print("HTTP Status Code:", r.status_code)
        print("Response Body:", r.text)
    except Exception as e:
        print("Request failed:", e)
        
    # 2. Test sending loaded JSON dicts (correct implementation)
    data_loaded = {
        "session_id": session_id,
        "version_number": 1,
        "srs_json": json.loads(srs_json_str),
        "diagrams_mermaid": json.loads(diagrams_mermaid),
        "erd_sql": {"sql": "{}"},
        "qa_checklist_result": json.loads(qa_json_str)
    }
    
    print("\nTesting payload with loaded dicts:")
    try:
        r = requests.post(endpoint, headers=headers, json=data_loaded)
        print("HTTP Status Code:", r.status_code)
        print("Response Body:", r.text)
    except Exception as e:
        print("Request failed:", e)

if __name__ == "__main__":
    test_document_insert()
