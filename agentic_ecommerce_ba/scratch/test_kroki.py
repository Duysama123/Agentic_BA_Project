import base64
import zlib
import requests

def get_kroki_url(mermaid_text: str) -> str:
    compressed = zlib.compress(mermaid_text.encode('utf-8'), 9)
    encoded = base64.urlsafe_b64encode(compressed).decode('ascii')
    return f"https://kroki.io/mermaid/png/{encoded}"

mermaid_code = "flowchart TD\n A-->B"
url = get_kroki_url(mermaid_code)
print("URL:", url)

try:
    r = requests.get(url, timeout=15)
    print("Status:", r.status_code)
except Exception as e:
    print("Error:", e)
