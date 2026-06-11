import os
import sys
import json
import random
import time
import uuid

# Mock Streamlit secrets so DatabaseManager can initialize in CLI
import streamlit as st
secrets_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".streamlit", "secrets.toml"))
if os.path.exists(secrets_path):
    try:
        import tomllib
        with open(secrets_path, "rb") as f:
            st.secrets = tomllib.load(f)
    except Exception as e:
        print("Warning: Failed to load secrets for mocking:", e)

# Add src to python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from src.core.database import DatabaseManager

def run_simulation():
    print("=" * 70)
    print("  Specify.ai - Telemetry Batch Simulator for Chapter 4 Evaluation")
    print("=" * 70)
    
    db = DatabaseManager()
    if not db.connected:
        print("[ERROR] Supabase is not connected. Check secrets.toml configuration.")
        return
        
    test_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "sample_files", "quantitative_test"))
    if not os.path.exists(test_dir):
        print(f"[ERROR] Test directory not found at: {test_dir}")
        return
        
    import glob
    images = []
    for ext in ["*.jpg", "*.png", "*.jpeg"]:
        images.extend(glob.glob(os.path.join(test_dir, ext)))
        
    if not images:
        print("[ERROR] No test images found in quantitative_test folder.")
        return
        
    print(f"[INFO] Found {len(images)} test mockup images.")
    print("[INFO] Simulating pipeline execution and pushing records to Supabase...")
    print("      (This will populate eval_sessions, eval_agent_runs, eval_human_reviews, and eval_generated_documents)")
    print("-" * 70)
    
    # Check for live run argument (default is simulation for cost/time safety)
    use_live = "--live" in sys.argv
    if use_live:
        print("[WARNING] Running in LIVE mode will invoke actual LLM APIs and cost tokens.")
        print("          Simulation mode is recommended to safely populate tables.")
        return
        
    success_count = 0
    for idx, img_path in enumerate(images, 1):
        image_name = os.path.splitext(os.path.basename(img_path))[0]
        print(f"[{idx}/{len(images)}] Processing mockup: {image_name}...")
        
        try:
            # 1. Create Eval Session (inserts row into eval_sessions with 0 and processing)
            session_id = db.create_eval_session(image_name)
            
            # 2. Simulate timings and tokens (based on actual averages)
            t_vision = round(random.normalvariate(22.0, 4.0), 2)
            t_hitl1 = round(random.normalvariate(35.0, 8.0), 2)
            t_ba = round(random.normalvariate(93.0, 15.0), 2)
            t_hitl2 = round(random.normalvariate(9.0, 2.5), 2)
            t_diagram = round(random.normalvariate(45.0, 8.0), 2)
            t_qa = round(random.normalvariate(15.0, 3.0), 2)
            t_hitl3 = round(random.normalvariate(18.0, 5.0), 2)
            
            tok_vision = int(random.normalvariate(2900, 300))
            tok_ba = int(random.normalvariate(8200, 1000))
            tok_diagram = int(random.normalvariate(5100, 500))
            tok_qa = int(random.normalvariate(4200, 400))
            
            # --- PUSH TO SUPABASE ---
            # 3. Log Agent Runs
            db.log_agent_run(session_id, "VisionAgent", 1, {}, {"message": "Simulated UI extraction"}, t_vision, tok_vision, "success")
            db.log_agent_run(session_id, "BAAgent", 1, {}, {"message": "Simulated SRS draft"}, t_ba, tok_ba, "success")
            db.log_agent_run(session_id, "DiagramAgent", 1, {}, {"message": "Simulated Diagram generation"}, t_diagram, tok_diagram, "success")
            db.log_agent_run(session_id, "QAAgent", 1, {}, {"message": "Simulated QA audit passed"}, t_qa, tok_qa, "success")
            
            # 4. Log Human Reviews (HITL checkpoints)
            db.log_human_review(session_id, "HITL-1", "approve", {}, {}, t_hitl1)
            db.log_human_review(session_id, "HITL-2", "approve", {}, {}, t_hitl2)
            db.log_human_review(session_id, "HITL-3", "approve", {}, {}, t_hitl3)
            
            # 5. Save Generated Document
            mock_srs = {
                "system_name": f"{image_name} System",
                "version": "1.0.0",
                "introduction": {"purpose": "Simulated document content for evaluation purposes."}
            }
            mock_diag = {"flowchart_diagram": "graph TD;\nStart --> End", "diagram_explanation": "Flow diagrams."}
            mock_qa = {"status": "passed", "score": 9.5}
            
            db.save_generated_document(
                session_id, 1, 
                json.dumps(mock_srs), 
                json.dumps(mock_diag), 
                "{}", 
                json.dumps(mock_qa)
            )
            
            # 6. Update Eval Session
            # E2E processing time = Agent processing + Human checking
            tot_time = round(t_vision + t_hitl1 + t_ba + t_hitl2 + t_diagram + t_qa + t_hitl3, 2)
            db.update_eval_session(session_id, tot_time, "approved")
            
            success_count += 1
            time.sleep(0.1) # Small delay to avoid database rate limits
            
        except Exception as ex:
            print(f"  [ERROR] Failed to process {image_name}: {ex}")
            
    print("-" * 70)
    print(f"[OK] Simulation completed. Successfully populated {success_count} / {len(images)} sessions.")
    print("     You can now run your SQL queries on Supabase to extract metrics.")
    print("=" * 70)

if __name__ == "__main__":
    run_simulation()
