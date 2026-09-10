import logging
import os
import json
import base64
from dotenv import load_dotenv
from mudraid import Agent

load_dotenv()
logging.basicConfig(level=logging.INFO)

api_key_id = os.getenv("WEBSITE_API_KEY_ID")
secret = os.getenv("WEBSITE_API_SECRET")
base_url = os.getenv("MUDRAID_BASE_URL") or "https://api.staging.mudraid.ai"

print(f"\n=======================================================")
print(f"Testing Delegatee: Website API Agent ({api_key_id})")
print(f"=======================================================")

agent = Agent(
    api_key_id=api_key_id,
    secret=secret,
    base_url=base_url
)

# 1. Force the platform map to load over the network
platforms_map = agent._platforms._ensure_loaded()
print(f"\n✅ Platforms Loaded from MudraID: {platforms_map}")

if not platforms_map:
    print("⚠️ No active/verified platforms found for this agent in MudraID!")

# 2. Fetch token and decode JWT
for host, platform_id in platforms_map.items():
    print(f"\n==========================================")
    print(f"Target Platform: {host} (ID: {platform_id})")
    print(f"==========================================")
    
    try:
        token = agent._tokens.get_token(platform_id)
        print(f"✅ Token received from MudraID!")

        # Decode JWT to check scopes
        payload_b64 = token.split(".")[1]
        payload_b64 += "=" * ((4 - len(payload_b64) % 4) % 4)
        payload_json = json.loads(base64.urlsafe_b64decode(payload_b64).decode("utf-8"))

        print("\n-------------------------------------------------------")
        print(f"👉 SCOPES IN TOKEN:  {payload_json.get('scopes')}")
        print("-------------------------------------------------------")
        print(f"Full Token Claims:\n{json.dumps(payload_json, indent=2)}")

    except Exception as e:
        print(f"❌ Error during token minting: {e}")

