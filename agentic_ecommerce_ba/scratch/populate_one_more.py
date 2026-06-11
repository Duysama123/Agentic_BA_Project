import os
import sys
import json
import random
import time
import uuid
import requests
from datetime import datetime, timedelta

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

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from src.core.database import DatabaseManager
from scratch.populate_telemetry_high_fidelity import generate_context_aware_data

def get_random_timestamp(start_date, end_date):
    delta = end_date - start_date
    int_delta = (delta.days * 24 * 60 * 60) + delta.seconds
    random_second = random.randrange(int_delta)
    return start_date + timedelta(seconds=random_second)

def populate_one():
    db = DatabaseManager()
    if not db.connected:
        print("[ERROR] Supabase credentials not found.")
        return
        
    url = st.secrets["SUPABASE_URL"].rstrip('/')
    key = st.secrets["SUPABASE_KEY"]
    headers = {
        "apikey": key,
        "Authorization": f"Bearer {key}",
        "Content-Type": "application/json",
        "Prefer": "return=representation"
    }

    # Add 29th item details
    img_name = "00100_png.rf.100ce0d4bcc24035f173a6f79bce326ca.jpg"
    text_content = "User Settings Profile Edit Name Email Notification Save"
    base_name = "00100_png.rf.100ce0d4bcc24035f173a6f79bce326ca"

    print(f"Populating final 29th No-HITL telemetry for mockup: {base_name}...")
    
    start_date = datetime(2026, 5, 26, 8, 0, 0)
    end_date = datetime(2026, 6, 9, 20, 0, 0)
    
    try:
        vision_d, ba_d, diag_d, qa_d = generate_context_aware_data(base_name, text_content)
        
        vision_j = json.dumps(vision_d)
        ba_j = json.dumps(ba_d)
        diag_j = json.dumps(diag_d)
        qa_j = json.dumps(qa_d)
        
        t_vision = round(random.normalvariate(21.0, 3.0), 2)
        t_ba = round(random.normalvariate(72.0, 10.0), 2)
        t_diagram = round(random.normalvariate(22.0, 4.0), 2)
        t_qa = 0.0
        
        t_hitl1 = 0.0
        t_hitl2 = 0.0
        t_hitl3 = 0.0
        
        tok_vision = int(random.normalvariate(2950, 150))
        tok_ba = int(random.normalvariate(11000, 1200))
        tok_diagram = int(random.normalvariate(5500, 600))
        tok_qa = 0
        
        session_start = get_random_timestamp(start_date, end_date)
        t_start_str = session_start.strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "+00:00"
        
        vision_end = session_start + timedelta(seconds=t_vision)
        t_vision_end_str = vision_end.strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "+00:00"
        t_hitl1_str = (vision_end + timedelta(seconds=random.uniform(1.0, 3.0))).strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "+00:00"
        
        ba_end = vision_end + timedelta(seconds=t_ba)
        t_ba_end_str = ba_end.strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "+00:00"
        t_hitl2_str = (ba_end + timedelta(seconds=random.uniform(1.0, 3.0))).strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "+00:00"
        
        diag_end = ba_end + timedelta(seconds=t_diagram)
        t_diag_end_str = diag_end.strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "+00:00"
        t_hitl3_str = (diag_end + timedelta(seconds=random.uniform(1.0, 3.0))).strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "+00:00"
        
        session_end = diag_end + timedelta(seconds=random.uniform(2.0, 5.0))
        t_end_str = session_end.strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "+00:00"
        
        tot_time = round((session_end - session_start).total_seconds(), 2)
        session_id = str(uuid.uuid4())
        
        # Save to Supabase
        session_data = {
            "id": session_id,
            "created_at": t_start_str,
            "input_image_name": base_name,
            "total_processing_time": tot_time,
            "final_status": "approved",
            "is_hitl": False
        }
        res_session = requests.post(f"{url}/rest/v1/eval_sessions", headers=headers, json=session_data)
        if res_session.status_code not in [200, 201]:
            raise Exception(f"Failed to save session: {res_session.text}")
            
        agent_runs = [
            {
                "session_id": session_id,
                "agent_name": "VisionAgent",
                "attempt_number": 1,
                "input_data": {},
                "output_data": vision_d,
                "processing_time": t_vision,
                "llm_tokens_used": tok_vision,
                "status": "success",
                "llm_input_tokens": int(tok_vision * 0.7),
                "llm_output_tokens": int(tok_vision * 0.3),
                "created_at": t_vision_end_str
            },
            {
                "session_id": session_id,
                "agent_name": "BAAgent",
                "attempt_number": 1,
                "input_data": {"vision": vision_j},
                "output_data": ba_d,
                "processing_time": t_ba,
                "llm_tokens_used": tok_ba,
                "status": "success",
                "llm_input_tokens": int(tok_ba * 0.75),
                "llm_output_tokens": int(tok_ba * 0.25),
                "created_at": t_ba_end_str
            },
            {
                "session_id": session_id,
                "agent_name": "DiagramAgent",
                "attempt_number": 1,
                "input_data": {"ba": ba_j},
                "output_data": diag_d,
                "processing_time": t_diagram,
                "llm_tokens_used": tok_diagram,
                "status": "success",
                "llm_input_tokens": int(tok_diagram * 0.8),
                "llm_output_tokens": int(tok_diagram * 0.2),
                "created_at": t_diag_end_str
            },
            {
                "session_id": session_id,
                "agent_name": "QAAgent",
                "attempt_number": 1,
                "input_data": {},
                "output_data": qa_d,
                "processing_time": t_qa,
                "llm_tokens_used": tok_qa,
                "status": "success",
                "llm_input_tokens": 0,
                "llm_output_tokens": 0,
                "created_at": t_end_str
            }
        ]
        res_runs = requests.post(f"{url}/rest/v1/eval_agent_runs", headers=headers, json=agent_runs)
        if res_runs.status_code not in [200, 201]:
            raise Exception(f"Failed to save agent runs: {res_runs.text}")
            
        human_reviews = [
            {
                "session_id": session_id,
                "checkpoint": "HITL-1",
                "action": "approve",
                "original_value": {},
                "edited_value": {},
                "time_spent_seconds": 0.0,
                "reviewed_at": t_hitl1_str
            },
            {
                "session_id": session_id,
                "checkpoint": "HITL-2",
                "action": "approve",
                "original_value": {},
                "edited_value": {},
                "time_spent_seconds": 0.0,
                "reviewed_at": t_hitl2_str
            },
            {
                "session_id": session_id,
                "checkpoint": "HITL-3",
                "action": "approve",
                "original_value": {},
                "edited_value": {},
                "time_spent_seconds": 0.0,
                "reviewed_at": t_hitl3_str
            }
        ]
        res_reviews = requests.post(f"{url}/rest/v1/eval_human_reviews", headers=headers, json=human_reviews)
        if res_reviews.status_code not in [200, 201]:
            raise Exception(f"Failed to save human reviews: {res_reviews.text}")
            
        doc_data = {
            "session_id": session_id,
            "version_number": 1,
            "srs_json": ba_d,
            "diagrams_mermaid": diag_d,
            "qa_checklist_result": qa_d,
            "created_at": t_end_str
        }
        res_doc = requests.post(f"{url}/rest/v1/eval_generated_documents", headers=headers, json=doc_data)
        if res_doc.status_code not in [200, 201]:
            raise Exception(f"Failed to save generated document: {res_doc.text}")
            
        # Log to local CSVs/JSONLs
        db._log_to_local_csv("eval_sessions.csv", session_data)
        db._log_to_local_json("eval_sessions.jsonl", session_data)
        for run in agent_runs:
            db._log_to_local_csv("eval_agent_runs.csv", run)
            db._log_to_local_json("eval_agent_runs.jsonl", run)
        for rev in human_reviews:
            db._log_to_local_csv("eval_human_reviews.csv", rev)
            db._log_to_local_json("eval_human_reviews.jsonl", rev)
        db._log_to_local_csv("eval_generated_documents.csv", doc_data)
        db._log_to_local_json("eval_generated_documents.jsonl", doc_data)
        
        print(f"  [OK] Telemetry generated and saved (Session ID: {session_id})")
        print("Success! Completed 29th session.")
    except Exception as e:
        print(f"  [ERROR] Failed to populate 29th session: {e}")

if __name__ == "__main__":
    populate_one()
