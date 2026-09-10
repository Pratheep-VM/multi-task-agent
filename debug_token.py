import json
import base64
import logging
from mudraid import Agent

logging.basicConfig(level=logging.INFO)

print("\n--- 1. Initializing Agent & Fetching Token ---")
agent = Agent()

# Force fresh platform discovery
agent.refresh_platforms()

# Resolve platform and fetch a fresh token
for host, platform_id in agent._platforms._map.items():
    print(f"\nTarget Platform: {host} (ID: {platform_id})")
    
    try:
        token = agent._tokens.get_token(platform_id)
        print(f"✅ Token received successfully!")

        # Decode the JWT payload without verifying signature just to see the claims
        payload_b64 = token.split(".")[1]
        # Add padding if needed
        payload_b64 += "=" * ((4 - len(payload_b64) % 4) % 4)
        payload_json = json.loads(base64.urlsafe_b64decode(payload_b64).decode("utf-8"))

        print("\n--- 2. JWT Claims inside Token ---")
        print(f"Agent ID (sub):   {payload_json.get('sub')}")
        print(f"Platform (aud):   {payload_json.get('aud')}")
        print(f"Scopes in Token:  {payload_json.get('scopes')}")
        print(f"Full Claims:\n{json.dumps(payload_json, indent=2)}")

        # Step 3: Test Platform Call
        print("\n--- 3. Testing Platform API Call ---")
        res = agent.get(f"https://{host}/tasks")
        print(f"Platform HTTP Status: {res.status_code}")
        print(f"Platform Response Body: {res.text}")

    except Exception as e:
        print(f"❌ Error during token/platform call: {e}")

