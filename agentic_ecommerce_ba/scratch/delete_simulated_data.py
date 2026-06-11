import os
import sys
import requests
import tomllib

def clean_database():
    secrets_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".streamlit", "secrets.toml"))
    if not os.path.exists(secrets_path):
        print("Secrets file not found.")
        return
        
    with open(secrets_path, "rb") as f:
        secrets = tomllib.load(f)
        
    url = secrets.get("SUPABASE_URL", "").rstrip('/')
    key = secrets.get("SUPABASE_KEY", "")
    
    headers = {
        "apikey": key,
        "Authorization": f"Bearer {key}"
    }
    
    real_session_id = "25882889-ef21-4ba8-88b6-21c4c3649ce9"
    print(f"Cleaning database. Preserving ONLY session: {real_session_id}")
    print("-" * 60)
    
    # Tables to delete from
    # We query or target with: session_id = neq.real_session_id
    tables_with_session_id = ["eval_agent_runs", "eval_human_reviews", "eval_generated_documents"]
    
    for table in tables_with_session_id:
        endpoint = f"{url}/rest/v1/{table}?session_id=neq.{real_session_id}"
        try:
            r = requests.delete(endpoint, headers=headers)
            print(f"Table {table}: DELETE response: {r.status_code}")
        except Exception as e:
            print(f"Failed to delete from {table}: {e}")
            
    # Finally, delete from eval_sessions (where column is 'id')
    endpoint = f"{url}/rest/v1/eval_sessions?id=neq.{real_session_id}"
    try:
        r = requests.delete(endpoint, headers=headers)
        print(f"Table eval_sessions: DELETE response: {r.status_code}")
    except Exception as e:
        print(f"Failed to delete from eval_sessions: {e}")
        
    print("-" * 60)
    print("Database cleanup completed successfully.")

if __name__ == "__main__":
    clean_database()
