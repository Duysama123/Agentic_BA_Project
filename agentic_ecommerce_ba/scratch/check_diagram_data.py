import os
import requests
import json

# Load secrets
import streamlit as st
secrets_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".streamlit", "secrets.toml"))
if os.path.exists(secrets_path):
    try:
        import tomllib
        with open(secrets_path, "rb") as f:
            st.secrets = tomllib.load(f)
    except Exception as e:
        print("Warning: Failed to load secrets:", e)

url = st.secrets["SUPABASE_URL"].rstrip('/')
key = st.secrets["SUPABASE_KEY"]
headers = {
    "apikey": key,
    "Authorization": f"Bearer {key}",
    "Content-Type": "application/json"
}

res = requests.get(f"{url}/rest/v1/projects?select=id,name,diagram_data&limit=5", headers=headers)
print(f"Response Status: {res.status_code}")
if res.status_code == 200:
    projects = res.json()
    print(f"Found {len(projects)} projects.")
    for p in projects:
        print(f"Project ID: {p['id']}, Name: {p['name']}")
        print(f"Diagram Data: {json.dumps(p['diagram_data'], indent=2)}")
        print("-" * 50)
else:
    print("Error fetching projects:", res.text)
