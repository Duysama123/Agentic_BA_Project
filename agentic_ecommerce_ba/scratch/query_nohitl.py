import requests
import json

url = "https://lgfnexklmxzsltewmrum.supabase.co"
key = "sb_publishable_8uS7-QVVNYLvZtZ0RbzbnA_Za6NTR4n"

headers = {
    "apikey": key,
    "Authorization": f"Bearer {key}",
    "Content-Type": "application/json"
}

# Fetch the session with is_hitl = false
res_sessions = requests.get(f"{url}/rest/v1/eval_sessions?is_hitl=eq.false&limit=1", headers=headers)
sessions = res_sessions.json()
if len(sessions) > 0:
    session = sessions[0]
    session_id = session['id']
    print("SESSION (NO HITL):")
    print(json.dumps(session, indent=2))
    
    # Fetch agent runs
    res_runs = requests.get(f"{url}/rest/v1/eval_agent_runs?session_id=eq.{session_id}", headers=headers)
    print("\nAGENT RUNS:")
    for run in res_runs.json():
        print(f"Agent: {run.get('agent_name')}, Attempt: {run.get('attempt_number')}, Time: {run.get('processing_time')}, Status: {run.get('status')}, Tokens: {run.get('llm_tokens_used')}, InputTokens: {run.get('llm_input_tokens')}, OutputTokens: {run.get('llm_output_tokens')}")
        
    # Fetch human reviews (should be empty)
    res_reviews = requests.get(f"{url}/rest/v1/eval_human_reviews?session_id=eq.{session_id}", headers=headers)
    print(f"\nHUMAN REVIEWS COUNT: {len(res_reviews.json())}")
    
    # Fetch generated documents
    res_docs = requests.get(f"{url}/rest/v1/eval_generated_documents?session_id=eq.{session_id}", headers=headers)
    print("\nGENERATED DOCUMENTS:")
    for doc in res_docs.json():
        print(f"Version: {doc.get('version_number')}, Created: {doc.get('created_at')}")
