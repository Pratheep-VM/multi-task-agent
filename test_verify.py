import logging
from mudraid import Agent
import os
from dotenv import load_dotenv
load_dotenv()

logging.basicConfig(level=logging.INFO)

# Automatically reads MUDRAID_API_KEY_ID & MUDRAID_SECRET from your .env
Agent(
    api_key_id=os.getenv("SUPERVISOR_KEY_ID"),
    secret=os.getenv("SUPERVISOR_SECRET")
)
print(f"Agent ID: {Agent.api_key_id}")

# Triggers /auth/agents/me/platforms and verification
Agent.refresh_platforms(self=Agent)
print("✅ Done!")
