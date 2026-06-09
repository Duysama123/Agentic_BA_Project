import os
import sys
import requests

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

def backfill():
    print("=" * 70)
    print("  Specify.ai - Telemetry Input/Output Tokens Backfill Engine")
    print("=" * 70)
    
    print("Fetching all agent runs from Supabase...")
    res = requests.get(f"{url}/rest/v1/eval_agent_runs", headers=headers)
    if res.status_code != 200:
        print(f"[ERROR] Failed to fetch agent runs: {res.text}")
        return
        
    runs = res.json()
    print(f"Found {len(runs)} agent runs to process.")
    
    success_count = 0
    for idx, run in enumerate(runs, 1):
        run_id = run['id']
        agent_name = run['agent_name']
        total_tokens = int(run.get('llm_tokens_used') or 0)
        
        # Calculate split based on agent type
        if agent_name == 'VisionAgent':
            input_tokens = int(total_tokens * 0.70)
            output_tokens = total_tokens - input_tokens
        elif agent_name == 'BAAgent':
            input_tokens = int(total_tokens * 0.90)
            output_tokens = total_tokens - input_tokens
        elif agent_name == 'DiagramAgent':
            input_tokens = int(total_tokens * 0.90)
            output_tokens = total_tokens - input_tokens
        else: # QAAgent or local
            input_tokens = 0
            output_tokens = 0
            
        # Update row in Supabase
        patch_res = requests.patch(
            f"{url}/rest/v1/eval_agent_runs?id=eq.{run_id}",
            headers=headers,
            json={
                "llm_input_tokens": input_tokens,
                "llm_output_tokens": output_tokens
            }
        )
        
        if patch_res.status_code in [200, 204]:
            success_count += 1
        else:
            print(f"  [ERROR] Failed to update run {run_id} ({agent_name}): {patch_res.text}")
            
        if idx % 20 == 0 or idx == len(runs):
            print(f"  [{idx}/{len(runs)}] Processed {idx} runs...")
            
    print("-" * 70)
    print(f"[OK] Backfill complete. Successfully updated {success_count}/{len(runs)} runs.")
    print("=" * 70)

if __name__ == "__main__":
    backfill()
