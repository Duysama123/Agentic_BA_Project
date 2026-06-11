import os
import requests
import json

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

res = requests.get(f"{url}/rest/v1/eval_generated_documents?select=id,diagram_data&limit=3", headers=headers)
print(f"Status Code: {res.status_code}")
if res.status_code == 200:
    docs = res.json()
    print(f"Found {len(docs)} documents.")
    for d in docs:
        print(f"Doc ID: {d['id']}")
        diag = d['diagram_data']
        print(f"Type of diagram_data: {type(diag)}")
        print(f"Diagram Data: {json.dumps(diag, indent=2)[:500]}...")
        print("-" * 50)
else:
    print("Error:", res.text)
