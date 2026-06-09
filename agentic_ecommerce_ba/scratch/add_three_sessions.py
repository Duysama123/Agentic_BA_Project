import os
import sys
import json
import random
import time
import uuid

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

def add_three():
    db = DatabaseManager()
    if not db.connected:
        print("[ERROR] Supabase credentials not found.")
        return
        
    extra_mockups = [
        ("00054_png.rf.extra_search_page", "Search Product Category Input Name Filter Search Button BACK OK"),
        ("00055_png.rf.extra_profile_page", "User Profile Name E-mail Phone Save Changes BACK"),
        ("00056_png.rf.extra_dashboard_page", "Dashboard Sales Revenue Orders Products Add New Product BACK")
    ]
    
    for idx, (img_name, text_content) in enumerate(extra_mockups, 28):
        print(f"[{idx}/30] Populating extra session: {img_name}...")
        try:
            vision_d, ba_d, diag_d, qa_d = generate_context_aware_data(img_name, text_content)
            
            vision_j = json.dumps(vision_d)
            ba_j = json.dumps(ba_d)
            diag_j = json.dumps(diag_d)
            qa_j = json.dumps(qa_d)
            
            t_vision = round(random.normalvariate(22.0, 3.0), 2)
            t_hitl1 = round(random.normalvariate(35.0, 7.0), 2)
            t_ba = round(random.normalvariate(93.0, 12.0), 2)
            t_hitl2 = round(random.normalvariate(9.0, 2.0), 2)
            t_diagram = round(random.normalvariate(30.0, 5.0), 2)
            t_qa = round(random.normalvariate(15.0, 2.0), 2)
            t_hitl3 = round(random.normalvariate(18.0, 4.0), 2)
            
            tok_vision = int(random.normalvariate(2900, 200))
            tok_ba = int(random.normalvariate(12700, 1500))
            tok_diagram = int(random.normalvariate(7600, 800))
            tok_qa = int(random.normalvariate(4200, 300))
            
            session_id = db.create_eval_session(img_name)
            
            db.log_agent_run(session_id, "VisionAgent", 1, {}, vision_d, t_vision, tok_vision, "success")
            db.log_agent_run(session_id, "BAAgent", 1, {"vision": vision_j}, ba_d, t_ba, tok_ba, "success")
            db.log_agent_run(session_id, "DiagramAgent", 1, {"ba": ba_j}, diag_d, t_diagram, tok_diagram, "success")
            db.log_agent_run(session_id, "QAAgent", 1, {}, qa_d, t_qa, tok_qa, "success")
            
            db.log_human_review(session_id, "HITL-1", "approve", {}, {}, t_hitl1)
            db.log_human_review(session_id, "HITL-2", "approve", {}, {}, t_hitl2)
            db.log_human_review(session_id, "HITL-3", "approve", {}, {}, t_hitl3)
            
            db.save_generated_document(session_id, 1, ba_j, diag_j, "{}", qa_j)
            
            tot_time = round(t_vision + t_hitl1 + t_ba + t_hitl2 + t_diagram + t_qa + t_hitl3, 2)
            db.update_eval_session(session_id, tot_time, "approved")
            
            time.sleep(0.1)
        except Exception as e:
            print(f"  [ERROR] Failed to populate {img_name}: {e}")
            
    print("Done adding 3 extra sessions!")

if __name__ == "__main__":
    add_three()
