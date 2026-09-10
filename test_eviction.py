import requests
import time
import os
import datetime
from dotenv import load_dotenv

load_dotenv()

# We will pass the new dummy agent key/secret directly into the script later
api_key_id = os.getenv("DUMMY_KEY_ID")
secret = os.getenv("DUMMY_SECRET")
platform_id = "be210da7-8c1d-4323-aaf7-e4c38b8d3271" # pradeepplatform

print("\n🚀 Starting Cache Eviction Tester...")
print("Press Ctrl+C to stop.")
print("=======================================================\n")

while True:
    now = datetime.datetime.now().strftime('%H:%M:%S')
    try:
        response = requests.post(
            "https://api.staging.mudraid.ai/api/v1/auth/token",
            json={"api_key_id": api_key_id, "secret": secret, "platform_id": platform_id, "scopes": []},
            headers={"Content-Type": "application/json"}
        )
        status = response.status_code
        if status == 200:
            print(f"[{now}] 🟢 200 OK (Cache Warm / Active)")
        else:
            print(f"[{now}] 🔴 {status} Refused! ({response.json().get('detail', 'Unknown')})")
    except Exception as e:
        print(f"[{now}] ❌ Error: {e}")
    
    time.sleep(2) # Ping every 2 seconds
