import requests
import json

url = "https://lgfnexklmxzsltewmrum.supabase.co"
key = "sb_publishable_8uS7-QVVNYLvZtZ0RbzbnA_Za6NTR4n"

headers = {
    "apikey": key,
    "Authorization": f"Bearer {key}",
    "Content-Type": "application/json"
}

# 1. Fetch one session with is_hitl = true
res_sessions_hitl = requests.get(f"{url}/rest/v1/eval_sessions?is_hitl=eq.true&limit=1", headers=headers)
sessions = res_sessions_hitl.json()
if len(sessions) > 0:
    session = sessions[0]
    session_id = session['id']
    print("SESSION:")
    print(json.dumps(session, indent=2))
    
    # 2. Fetch all agent runs for this session
    res_runs = requests.get(f"{url}/rest/v1/eval_agent_runs?session_id=eq.{session_id}", headers=headers)
    print("\nAGENT RUNS:")
    for run in res_runs.json():
        print(f"Agent: {run.get('agent_name')}, Attempt: {run.get('attempt_number')}, Time: {run.get('processing_time')}, Status: {run.get('status')}, Tokens: {run.get('llm_tokens_used')}, InputTokens: {run.get('llm_input_tokens')}, OutputTokens: {run.get('llm_output_tokens')}")
        # Print keys of input_data and output_data
        print(f"  Input keys: {list(run.get('input_data', {}).keys()) if run.get('input_data') else 'None'}")
        print(f"  Output keys: {list(run.get('output_data', {}).keys()) if run.get('output_data') else 'None'}")
        
    # 3. Fetch all human reviews for this session
    res_reviews = requests.get(f"{url}/rest/v1/eval_human_reviews?session_id=eq.{session_id}", headers=headers)
    print("\nHUMAN REVIEWS:")
    for rev in res_reviews.json():
        print(f"Checkpoint: {rev.get('checkpoint')}, Action: {rev.get('action')}, Time: {rev.get('time_spent_seconds')}")
        
    # 4. Fetch generated documents
    res_docs = requests.get(f"{url}/rest/v1/eval_generated_documents?session_id=eq.{session_id}", headers=headers)
    print("\nGENERATED DOCUMENTS:")
    for doc in res_docs.json():
        print(f"Version: {doc.get('version_number')}, Created: {doc.get('created_at')}")
        print(f"  SRS Keys: {list(doc.get('srs_json', {}).keys()) if doc.get('srs_json') else 'None'}")
        print(f"  Diagram Keys: {list(doc.get('diagrams_mermaid', {}).keys()) if doc.get('diagrams_mermaid') else 'None'}")
        print(f"  QA Keys: {list(doc.get('qa_checklist_result', {}).keys()) if doc.get('qa_checklist_result') else 'None'}")
