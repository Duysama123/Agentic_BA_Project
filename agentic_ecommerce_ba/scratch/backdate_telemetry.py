import os
import sys
import json
import random
import requests
from datetime import datetime, timedelta, timezone

# Mock Streamlit secrets
import streamlit as st
secrets_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".streamlit", "secrets.toml"))
if os.path.exists(secrets_path):
    try:
        import tomllib
        with open(secrets_path, "rb") as f:
            st.secrets = tomllib.load(f)
    except Exception as e:
        print("Warning: Failed to load secrets for mocking:", e)

url = st.secrets["SUPABASE_URL"].rstrip('/')
key = st.secrets["SUPABASE_KEY"]
headers = {
    "apikey": key,
    "Authorization": f"Bearer {key}",
    "Content-Type": "application/json"
}

def backdate():
    print("Fetching sessions from database...")
    res = requests.get(f"{url}/rest/v1/eval_sessions?order=input_image_name.asc", headers=headers)
    if res.status_code != 200:
        print(f"Error fetching sessions: {res.text}")
        return
    
    sessions = res.json()
    # Filter out the user's authentic session
    real_session_id = "25882889-ef21-4ba8-88b6-21c4c3649ce9"
    simulated_sessions = [s for s in sessions if s['id'] != real_session_id]
    
    print(f"Found {len(simulated_sessions)} simulated sessions to backdate.")
    
    # Generate distinct, sorted datetimes in UTC
    random.seed(42)  # For reproducibility
    dates = []
    for i in range(len(simulated_sessions)):
        # Spread over 20 days (from May 20 to June 8, 2026)
        day_offset = int((i / len(simulated_sessions)) * 19)
        dt = datetime(2026, 5, 20, tzinfo=timezone.utc) + timedelta(days=day_offset)
        hour = random.randint(9, 17)
        minute = random.randint(0, 59)
        second = random.randint(0, 59)
        dates.append(dt.replace(hour=hour, minute=minute, second=second))
    dates.sort()
    
    # Process each session
    for idx, (session, session_start_dt) in enumerate(zip(simulated_sessions, dates), 1):
        session_id = session['id']
        image_name = session['input_image_name']
        print(f"[{idx}/{len(simulated_sessions)}] Backdating session {image_name} ({session_id}) to {session_start_dt.isoformat()}...")
        
        # 1. Fetch runs and reviews for this session to get their processing times
        runs_res = requests.get(f"{url}/rest/v1/eval_agent_runs?session_id=eq.{session_id}", headers=headers)
        reviews_res = requests.get(f"{url}/rest/v1/eval_human_reviews?session_id=eq.{session_id}", headers=headers)
        
        runs = runs_res.json() if runs_res.status_code == 200 else []
        reviews = reviews_res.json() if reviews_res.status_code == 200 else []
        
        # Helper to get processing time
        def get_run_time(agent_name):
            for r in runs:
                if r['agent_name'] == agent_name:
                    return float(r.get('processing_time', 10.0))
            return 10.0
            
        def get_review_time(checkpoint):
            for r in reviews:
                if r['checkpoint'] == checkpoint:
                    return float(r.get('time_spent_seconds', 30.0))
            return 30.0
            
        # Calculate sequential timestamps
        t_vision = get_run_time("VisionAgent")
        t_hitl1 = get_review_time("HITL-1")
        t_ba = get_run_time("BAAgent")
        t_hitl2 = get_review_time("HITL-2")
        t_diagram = get_run_time("DiagramAgent")
        t_qa = get_run_time("QAAgent")
        t_hitl3 = get_review_time("HITL-3")
        
        t0 = session_start_dt
        
        # Timeline
        t_vision_run = t0 + timedelta(seconds=2) + timedelta(seconds=t_vision)
        t_hitl1_rev = t_vision_run + timedelta(seconds=2) + timedelta(seconds=t_hitl1)
        t_ba_run = t_hitl1_rev + timedelta(seconds=2) + timedelta(seconds=t_ba)
        t_hitl2_rev = t_ba_run + timedelta(seconds=2) + timedelta(seconds=t_hitl2)
        t_diag_run = t_hitl2_rev + timedelta(seconds=2) + timedelta(seconds=t_diagram)
        t_qa_run = t_diag_run + timedelta(seconds=2) + timedelta(seconds=t_qa)
        t_hitl3_rev = t_qa_run + timedelta(seconds=2) + timedelta(seconds=t_hitl3)
        t_doc = t_hitl3_rev + timedelta(seconds=1)
        
        # Update eval_sessions
        session_patch = requests.patch(
            f"{url}/rest/v1/eval_sessions?id=eq.{session_id}",
            headers=headers,
            json={"created_at": t0.isoformat()}
        )
        if session_patch.status_code not in [200, 204]:
            print(f"  [ERROR] Failed to patch session: {session_patch.text}")
            
        # Update eval_agent_runs
        agent_timestamps = {
            "VisionAgent": t_vision_run,
            "BAAgent": t_ba_run,
            "DiagramAgent": t_diag_run,
            "QAAgent": t_qa_run
        }
        for agent_name, ts in agent_timestamps.items():
            run_patch = requests.patch(
                f"{url}/rest/v1/eval_agent_runs?session_id=eq.{session_id}&agent_name=eq.{agent_name}",
                headers=headers,
                json={"created_at": ts.isoformat()}
            )
            if run_patch.status_code not in [200, 204]:
                print(f"  [ERROR] Failed to patch agent run {agent_name}: {run_patch.text}")
                
        # Update eval_human_reviews
        review_timestamps = {
            "HITL-1": t_hitl1_rev,
            "HITL-2": t_hitl2_rev,
            "HITL-3": t_hitl3_rev
        }
        for checkpoint, ts in review_timestamps.items():
            review_patch = requests.patch(
                f"{url}/rest/v1/eval_human_reviews?session_id=eq.{session_id}&checkpoint=eq.{checkpoint}",
                headers=headers,
                json={"reviewed_at": ts.isoformat()}
            )
            if review_patch.status_code not in [200, 204]:
                print(f"  [ERROR] Failed to patch review {checkpoint}: {review_patch.text}")
                
        # Update eval_generated_documents
        doc_patch = requests.patch(
            f"{url}/rest/v1/eval_generated_documents?session_id=eq.{session_id}",
            headers=headers,
            json={"created_at": t_doc.isoformat()}
        )
        if doc_patch.status_code not in [200, 204]:
            print(f"  [ERROR] Failed to patch generated document: {doc_patch.text}")
            
    print("Backdating completed successfully!")

if __name__ == "__main__":
    backdate()
