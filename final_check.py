import json
import base64
import os
import requests
from dotenv import load_dotenv

load_dotenv()

# Read your agent credentials
api_key_id = os.getenv("WEBSITE_API_KEY_ID") or os.getenv("WEBSITE_API_API_KEY_ID") or "muid_kid_181b5b092681ac7dda80f68cf673a5e8"
secret = os.getenv("WEBSITE_API_SECRET") or os.getenv("WEBSITE_SECRET")
base_url = "https://api.staging.mudraid.ai"
platform_id = "be210da7-8c1d-4323-aaf7-e4c38b8d3271" # pradeepplatform

print("\n=======================================================")
print(f"Testing Delegatee Token Minting")
print(f"Agent:    {api_key_id}")
print(f"Platform: {platform_id}")
print("=======================================================")

payload = {
    "api_key_id": api_key_id,
    "secret": secret,
    "platform_id": platform_id,
    "scopes": []
}

response = requests.post(
    f"{base_url}/api/v1/auth/token",
    json=payload,
    headers={"Content-Type": "application/json"}
)

if response.status_code == 200:
    print("\n✅ HTTP STATUS: 200 OK")
    token = response.json().get("access_token")
    
    # Safely decode JWT payload
    payload_b64 = token.split(".")[1]
    payload_b64 += "=" * ((4 - len(payload_b64) % 4) % 4)
    decoded = json.loads(base64.urlsafe_b64decode(payload_b64).decode("utf-8"))
    
    print("\n👉 DECODED JWT SCOPES:")
    print(f"  {decoded.get('scopes')}")
    
elif response.status_code == 403:
    print(f"\n❌ HTTP STATUS: 403 Forbidden")
    try:
        print(f"👉 EXACT ERROR SENTENCE:\n  {response.json().get('detail')}")
    except Exception:
        print(f"  {response.text}")
else:
    print(f"\n❌ UNEXPECTED STATUS: {response.status_code}")
    print(response.text)

print("\n=======================================================\n")
