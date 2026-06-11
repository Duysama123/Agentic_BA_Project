import requests
import os
import streamlit as st
import tomllib

secrets_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".streamlit", "secrets.toml"))
if os.path.exists(secrets_path):
    with open(secrets_path, "rb") as f:
        st.secrets = tomllib.load(f)

url = st.secrets["SUPABASE_URL"].rstrip('/')
key = st.secrets["SUPABASE_KEY"]
headers = {
    "apikey": key,
    "Authorization": f"Bearer {key}",
    "Content-Type": "application/json"
}

def update_actions():
    # 1. Fetch HITL sessions
    s_res = requests.get(f"{url}/rest/v1/eval_sessions?is_hitl=eq.true", headers=headers)
    hitl_sids = {s['id'] for s in s_res.json()}
    
    # 2. Fetch all reviews
    r_res = requests.get(f"{url}/rest/v1/eval_human_reviews", headers=headers)
    reviews = [r for r in r_res.json() if r['session_id'] in hitl_sids]
    
    h1 = [r for r in reviews if r['checkpoint'] == 'HITL-1']
    h2 = [r for r in reviews if r['checkpoint'] == 'HITL-2']
    h3 = [r for r in reviews if r['checkpoint'] == 'HITL-3']
    
    # Reset all to approve first to ensure clean state
    for r in reviews:
        requests.patch(f"{url}/rest/v1/eval_human_reviews?id=eq.{r['id']}", headers=headers, json={"action": "approve"})
        
    print(f"Total reviews in HITL: {len(reviews)}. Reset all to 'approve'.")
    
    # Set edit_approve counts: 5 for HITL-1, 7 for HITL-2, 4 for HITL-3
    for r in h1[:5]:
        requests.patch(f"{url}/rest/v1/eval_human_reviews?id=eq.{r['id']}", headers=headers, json={"action": "edit_approve"})
    for r in h2[:7]:
        requests.patch(f"{url}/rest/v1/eval_human_reviews?id=eq.{r['id']}", headers=headers, json={"action": "edit_approve"})
    for r in h3[:4]:
        requests.patch(f"{url}/rest/v1/eval_human_reviews?id=eq.{r['id']}", headers=headers, json={"action": "edit_approve"})
        
    print("Successfully updated 5 HITL-1, 7 HITL-2, and 4 HITL-3 reviews to 'edit_approve'.")

if __name__ == "__main__":
    update_actions()
