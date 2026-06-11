import requests
import json

url = "https://lgfnexklmxzsltewmrum.supabase.co"
key = "sb_publishable_8uS7-QVVNYLvZtZ0RbzbnA_Za6NTR4n"

headers = {
    "apikey": key,
    "Authorization": f"Bearer {key}",
    "Content-Type": "application/json"
}

session_id = "276e794a-367a-4470-b5db-ba41ef36394b"

res_docs = requests.get(f"{url}/rest/v1/eval_generated_documents?session_id=eq.{session_id}", headers=headers)
print("NO-HITL GENERATED DOCUMENT:")
print(json.dumps(res_docs.json(), indent=2))
