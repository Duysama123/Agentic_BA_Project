import streamlit as st
import requests
import json
import base64
import os
import uuid
import csv
from datetime import datetime

class DatabaseManager:
    def __init__(self):
        # Setup local telemetry directory at base_dir/data/telemetry
        self.local_dir = os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
            "data",
            "telemetry"
        )
        try:
            os.makedirs(self.local_dir, exist_ok=True)
        except Exception as e:
            print(f"Warning: Failed to create local telemetry directory: {e}")
            
        try:
            self.url = st.secrets["SUPABASE_URL"].rstrip('/')
            self.key = st.secrets["SUPABASE_KEY"]
            self.connected = True
        except Exception as e:
            self.connected = False
            self.error = str(e)

    def _log_to_local_csv(self, filename: str, row_dict: dict):
        """Helper to append a flat dictionary row to a local CSV file in data/telemetry/."""
        filepath = os.path.join(self.local_dir, filename)
        
        # Add timestamp if not present
        if "created_at" not in row_dict:
            row_dict = {"created_at": datetime.now().isoformat(), **row_dict}
            
        file_exists = os.path.exists(filepath)
        
        try:
            with open(filepath, mode="a", encoding="utf-8", newline="") as f:
                # Flatten complex dictionary/list types to JSON strings
                flat_row = {}
                for k, v in row_dict.items():
                    if isinstance(v, (dict, list)):
                        flat_row[k] = json.dumps(v, ensure_ascii=False)
                    else:
                        flat_row[k] = v
                
                writer = csv.DictWriter(f, fieldnames=list(flat_row.keys()))
                if not file_exists:
                    writer.writeheader()
                writer.writerow(flat_row)
        except Exception as e:
            print(f"Error logging locally to CSV {filename}: {e}")

    def _log_to_local_json(self, filename: str, entry: dict):
        """Helper to append a JSON object as a single line (JSONL) to a local file in data/telemetry/."""
        filepath = os.path.join(self.local_dir, filename)
        
        # Add timestamp if not present
        if "created_at" not in entry:
            entry = {"created_at": datetime.now().isoformat(), **entry}
            
        try:
            with open(filepath, mode="a", encoding="utf-8") as f:
                f.write(json.dumps(entry, ensure_ascii=False) + "\n")
        except Exception as e:
            print(f"Error logging locally to JSONL {filename}: {e}")

    def _headers(self, auth_token=None):
        headers = {
            "apikey": self.key,
            "Content-Type": "application/json"
        }
        if auth_token:
            headers["Authorization"] = f"Bearer {auth_token}"
        else:
            headers["Authorization"] = f"Bearer {self.key}"
        return headers

    def login(self, email, password):
        if not self.connected: raise Exception("Missing Supabase Keys")
        endpoint = f"{self.url}/auth/v1/token?grant_type=password"
        payload = {"email": email, "password": password}
        res = requests.post(endpoint, headers=self._headers(), json=payload)
        if res.status_code != 200:
            raise Exception(res.json().get('error_description', 'Login failed'))
            
        data = res.json()
        st.session_state.access_token = data.get('access_token')
        
        class UserMock:
            def __init__(self, u):
                self.id = u.get("id")
                self.email = u.get("email")
                
        class AuthRespMock:
            def __init__(self, d):
                self.user = UserMock(d.get("user", {}))
                
        return AuthRespMock(data)

    def signup(self, email, password):
        if not self.connected: raise Exception("Missing Supabase Keys")
        endpoint = f"{self.url}/auth/v1/signup"
        payload = {"email": email, "password": password}
        res = requests.post(endpoint, headers=self._headers(), json=payload)
        if res.status_code not in [200, 201]:
            raise Exception(res.json().get('msg', 'Signup failed'))
        return res.json()

    def logout(self):
        if 'access_token' in st.session_state:
            del st.session_state.access_token

    def save_project(self, user_id, project_name, image_bytes, vision_json, ba_json, diagram_json, qa_json, testcase_json=None):
        if not self.connected: raise Exception("Missing Supabase Keys")
        
        image_base64 = ""
        if image_bytes:
            image_base64 = base64.b64encode(image_bytes).decode('utf-8')
            
        data = {
            "user_id": user_id,
            "name": project_name,
            "image_base64": image_base64,
            "vision_data": json.loads(vision_json) if vision_json else {},
            "ba_data": json.loads(ba_json) if ba_json else {},
            "diagram_data": json.loads(diagram_json) if diagram_json else {},
            "testcase_data": json.loads(testcase_json) if testcase_json else {},
            "qa_data": json.loads(qa_json) if qa_json else {}
        }
        
        endpoint = f"{self.url}/rest/v1/projects"
        headers = self._headers(st.session_state.get('access_token'))
        headers["Prefer"] = "return=representation"
        
        res = requests.post(endpoint, headers=headers, json=data)
        if res.status_code not in [200, 201]:
            raise Exception(res.text)
            
        class RespMock:
            def __init__(self, content):
                self.data = content
        return RespMock(res.json())

    def get_projects(self, user_id):
        if not self.connected: raise Exception("Missing Supabase Keys")
        endpoint = f"{self.url}/rest/v1/projects?user_id=eq.{user_id}&select=id,name,created_at&order=created_at.desc"
        res = requests.get(endpoint, headers=self._headers(st.session_state.get('access_token')))
        if res.status_code != 200:
            raise Exception(res.text)
        return res.json()
        
    def get_project_details(self, project_id):
        if not self.connected: raise Exception("Missing Supabase Keys")
        endpoint = f"{self.url}/rest/v1/projects?id=eq.{project_id}&select=*"
        res = requests.get(endpoint, headers=self._headers(st.session_state.get('access_token')))
        if res.status_code != 200:
            raise Exception(res.text)
        data = res.json()
        if len(data) > 0:
            return data[0]
        return None

    # ==========================================
    # EVALUATION & TELEMETRY TRACKING METHODS
    # ==========================================
    def create_eval_session(self, input_image_name):
        session_id = str(uuid.uuid4())
        data = {
            "id": session_id,
            "input_image_name": input_image_name,
            "total_processing_time": 0,
            "final_status": "processing"
        }
        # Log to local CSV and JSONL
        self._log_to_local_csv("eval_sessions.csv", data)
        self._log_to_local_json("eval_sessions.jsonl", data)
        
        if not self.connected: 
            return session_id
            
        endpoint = f"{self.url}/rest/v1/eval_sessions"
        headers = self._headers(st.session_state.get('access_token'))
        headers["Prefer"] = "return=representation"
        try:
            db_data = {
                "id": session_id,
                "input_image_name": input_image_name,
                "total_processing_time": 0,
                "final_status": "processing"
            }
            res = requests.post(endpoint, headers=headers, json=db_data)
        except Exception as e:
            print(f"Error creating eval session on Supabase: {e}")
        return session_id

    def update_eval_session(self, session_id, total_processing_time, final_status):
        data = {
            "session_id": session_id,
            "total_processing_time": total_processing_time,
            "final_status": final_status
        }
        # Log to local CSV and JSONL
        self._log_to_local_csv("eval_session_updates.csv", data)
        self._log_to_local_json("eval_session_updates.jsonl", data)
        
        if not self.connected or not session_id: 
            return
            
        endpoint = f"{self.url}/rest/v1/eval_sessions?id=eq.{session_id}"
        headers = self._headers(st.session_state.get('access_token'))
        try:
            requests.patch(endpoint, headers=headers, json={
                "total_processing_time": total_processing_time,
                "final_status": final_status
            })
        except Exception as e:
            print(f"Error updating eval session on Supabase: {e}")

    def log_agent_run(self, session_id, agent_name, attempt_number, input_data, output_data, processing_time, llm_tokens_used, status):
        data = {
            "session_id": session_id,
            "agent_name": agent_name,
            "attempt_number": attempt_number,
            "input_data": input_data if input_data else {},
            "output_data": output_data if output_data else {},
            "processing_time": processing_time,
            "llm_tokens_used": llm_tokens_used,
            "status": status
        }
        # Log to local CSV and JSONL
        self._log_to_local_csv("eval_agent_runs.csv", data)
        self._log_to_local_json("eval_agent_runs.jsonl", data)
        
        if not self.connected or not session_id: 
            return
            
        endpoint = f"{self.url}/rest/v1/eval_agent_runs"
        try:
            requests.post(endpoint, headers=self._headers(st.session_state.get('access_token')), json=data)
        except Exception as e:
            print(f"Error logging agent run on Supabase: {e}")

    def log_human_review(self, session_id, checkpoint, action, original_value, edited_value, time_spent_seconds):
        data = {
            "session_id": session_id,
            "checkpoint": checkpoint,
            "action": action,
            "original_value": original_value if original_value else {},
            "edited_value": edited_value if edited_value else {},
            "time_spent_seconds": time_spent_seconds
        }
        # Log to local CSV and JSONL
        self._log_to_local_csv("eval_human_reviews.csv", data)
        self._log_to_local_json("eval_human_reviews.jsonl", data)
        
        if not self.connected or not session_id: 
            return
            
        endpoint = f"{self.url}/rest/v1/eval_human_reviews"
        try:
            requests.post(endpoint, headers=self._headers(st.session_state.get('access_token')), json=data)
        except Exception as e:
            print(f"Error logging human review on Supabase: {e}")

    def save_generated_document(self, session_id, version_number, srs_json, diagrams_mermaid, erd_sql, qa_checklist_result):
        data = {
            "session_id": session_id,
            "version_number": version_number,
            "srs_json": srs_json if srs_json else {},
            "diagrams_mermaid": {"mermaid": diagrams_mermaid} if isinstance(diagrams_mermaid, str) else diagrams_mermaid,
            "erd_sql": {"sql": erd_sql} if isinstance(erd_sql, str) else erd_sql,
            "qa_checklist_result": qa_checklist_result if qa_checklist_result else {}
        }
        # Log to local CSV and JSONL
        self._log_to_local_csv("eval_generated_documents.csv", data)
        self._log_to_local_json("eval_generated_documents.jsonl", data)
        
        if not self.connected or not session_id: 
            return
            
        endpoint = f"{self.url}/rest/v1/eval_generated_documents"
        try:
            requests.post(endpoint, headers=self._headers(st.session_state.get('access_token')), json=data)
        except Exception as e:
            print(f"Error saving generated document on Supabase: {e}")


