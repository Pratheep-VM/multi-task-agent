import requests
import json
import os
from dotenv import load_dotenv

load_dotenv()

# Read the exact variables from .env
api_key_id = os.getenv("WEBSITE_API_API_KEY_ID") 
secret = os.getenv("WEBSITE_API_SECRET") 
base_url = "https://api.staging.mudraid.ai"
platform_id = "be210da7-8c1d-4323-aaf7-e4c38b8d3271" # pradeepplatform

print(f"\n=======================================================")
print(f"1. Sending RAW Request to POST /api/v1/auth/token")
print(f"Agent:    {api_key_id}")
print(f"Secret:   {secret[:10]}... (masked)" if secret else "Secret: None")
print(f"Platform: {platform_id}")
print(f"=======================================================")

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

print(f"\n👉 HTTP STATUS CODE: {response.status_code}")
print(f"\n👉 RAW RESPONSE BODY (JSON) :")
try:
    print(json.dumps(response.json(), indent=2))
except Exception:
    print(response.text)

