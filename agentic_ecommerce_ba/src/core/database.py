import streamlit as st
import requests
import json
import base64

class DatabaseManager:
    def __init__(self):
        try:
            self.url = st.secrets["SUPABASE_URL"].rstrip('/')
            self.key = st.secrets["SUPABASE_KEY"]
            self.connected = True
        except Exception as e:
            self.connected = False
            self.error = str(e)
            
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

    def save_project(self, user_id, project_name, image_bytes, vision_json, ba_json, diagram_json, da_json, qa_json):
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
            "da_data": json.loads(da_json) if da_json else {},
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
