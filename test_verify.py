import logging
from mudraid import Agent
import os
from dotenv import load_dotenv
load_dotenv()

logging.basicConfig(level=logging.INFO)

# Automatically reads MUDRAID_API_KEY_ID & MUDRAID_SECRET from your .env
agent=Agent(
    api_key_id=os.getenv("SUPERVISOR_KEY_ID"),
    secret=os.getenv("SUPERVISOR_SECRET")
)
print(f"Agent ID: {agent.api_key_id}")

# Triggers /auth/agents/me/platforms and verification
agent.refresh_platforms()
print("✅ Done!")
print("\n--- Sending request through MudraID ---")
try:
    response = agent.get("https://app.staging.mudraid.ai/mcp")
    print(f"Response Status Code: {response.status_code}")
except Exception as e:
    print(f"Request result: {e}")

print("\n✅ Verification complete!")
