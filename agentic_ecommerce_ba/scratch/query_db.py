import requests
import json

url = "https://lgfnexklmxzsltewmrum.supabase.co"
key = "sb_publishable_8uS7-QVVNYLvZtZ0RbzbnA_Za6NTR4n"

headers = {
    "apikey": key,
    "Authorization": f"Bearer {key}",
    "Content-Type": "application/json"
}

# 1. Get a session with is_hitl = true
res_sessions_hitl = requests.get(f"{url}/rest/v1/eval_sessions?is_hitl=eq.true&limit=1", headers=headers)
print("--- Session with HITL = True ---")
print(json.dumps(res_sessions_hitl.json(), indent=2))

# 2. Get a session with is_hitl = false
res_sessions_nohitl = requests.get(f"{url}/rest/v1/eval_sessions?is_hitl=eq.false&limit=1", headers=headers)
print("\n--- Session with HITL = False ---")
print(json.dumps(res_sessions_nohitl.json(), indent=2))

if res_sessions_hitl.status_code == 200 and len(res_sessions_hitl.json()) > 0:
    session_id = res_sessions_hitl.json()[0]['id']
    # Get agent runs for this session
    res_agent_runs = requests.get(f"{url}/rest/v1/eval_agent_runs?session_id=eq.{session_id}", headers=headers)
    print("\n--- Agent Runs for HITL Session ---")
    print(json.dumps(res_agent_runs.json()[:2], indent=2)) # Print first 2 runs
    
    # Get human reviews for this session
    res_human_reviews = requests.get(f"{url}/rest/v1/eval_human_reviews?session_id=eq.{session_id}", headers=headers)
    print("\n--- Human Reviews for HITL Session ---")
    print(json.dumps(res_human_reviews.json(), indent=2))
    
    # Get generated documents for this session
    res_docs = requests.get(f"{url}/rest/v1/eval_generated_documents?session_id=eq.{session_id}", headers=headers)
    print("\n--- Generated Documents for HITL Session ---")
    print(json.dumps(res_docs.json()[:1], indent=2))
