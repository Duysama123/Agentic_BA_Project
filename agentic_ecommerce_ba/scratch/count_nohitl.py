import requests

url = "https://lgfnexklmxzsltewmrum.supabase.co"
key = "sb_publishable_8uS7-QVVNYLvZtZ0RbzbnA_Za6NTR4n"

headers = {
    "apikey": key,
    "Authorization": f"Bearer {key}",
    "Content-Type": "application/json"
}

# 1. Get count of sessions with is_hitl = false
res_nohitl = requests.get(f"{url}/rest/v1/eval_sessions?is_hitl=eq.false", headers=headers)
print(f"Total No-HITL sessions: {len(res_nohitl.json())}")

# 2. Get count of sessions with is_hitl = true
res_hitl = requests.get(f"{url}/rest/v1/eval_sessions?is_hitl=eq.true", headers=headers)
print(f"Total HITL sessions: {len(res_hitl.json())}")
