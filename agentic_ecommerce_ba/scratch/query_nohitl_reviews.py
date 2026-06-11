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

res_reviews = requests.get(f"{url}/rest/v1/eval_human_reviews?session_id=eq.{session_id}", headers=headers)
print("HUMAN REVIEWS FOR NO-HITL SESSION:")
print(json.dumps(res_reviews.json(), indent=2))
