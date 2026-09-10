import time
import uuid
import json
import jwt
import requests

# =====================================================================
# 1. Configuration for Kong Protected MCP Staging Surface
# =====================================================================
CLIENT_ID = "muid_mc_017f5174d12681a7f34f4b6f2e1e2bf2"
KID = "kid_46fbf4431874"
TOKEN_ENDPOINT = "https://api.staging.mudraid.ai/oauth2/token"

# The Kong-Enforced MCP Surface (Triggers live MudraID /decide policy):
ENFORCED_SURFACE = "https://api.staging.mudraid.ai/mcp"

with open("private_key.pem", "rb") as f:
    PRIVATE_KEY = f.read()

# =====================================================================
# 2. Sign Assertion & Mint Token for the Enforced Surface
# =====================================================================
print("\n[Step 1] Minting Token for Enforced Surface...")
now = int(time.time())
claims = {
    "iss": CLIENT_ID, "sub": CLIENT_ID, "aud": TOKEN_ENDPOINT,
    "iat": now, "exp": now + 60, "jti": uuid.uuid4().hex,
}
assertion = jwt.encode(claims, PRIVATE_KEY, algorithm="RS256", headers={"alg": "RS256", "kid": KID})

payload = {
    "grant_type": "client_credentials",
    "client_assertion_type": "urn:ietf:params:oauth:client-assertion-type:jwt-bearer",
    "client_assertion": assertion,
    "resource": ENFORCED_SURFACE,
}
token_resp = requests.post(TOKEN_ENDPOINT, data=payload)

if token_resp.status_code == 200:
    access_token = token_resp.json().get("access_token")
    print("✅ Token acquired for enforced surface!")
else:
    # If client has a specific platform grant, use the platform token
    print(f"ℹ️ Minting with default grant (HTTP {token_resp.status_code})")
    access_token = None

# =====================================================================
# 3. Call Enforced Tool Actions to Trigger Evidence Decisions
# =====================================================================
print(f"\n[Step 2] Sending Enforced MCP Actions to {ENFORCED_SURFACE}...")

headers = {
    "Content-Type": "application/json"
}
if access_token:
    headers["Authorization"] = f"Bearer {access_token}"

# --- ACTION A: Public Discovery (Pass-through) ---
print("\n--- 1. Testing Discovery Method (tools/list) ---")
discovery_payload = {
    "jsonrpc": "2.0",
    "id": 1,
    "method": "tools/list",
    "params": {}
}
resp_discovery = requests.post(ENFORCED_SURFACE, headers=headers, json=discovery_payload)
print(f"Discovery Status: HTTP {resp_discovery.status_code}")
print(f"Discovery Body  : {resp_discovery.text[:120]}...")

# --- ACTION B: Protected Tool Invocation (Triggers Policy Decision) ---
print("\n--- 2. Invoking Protected Tool (tools/call: verify_agent) ---")
tool_payload = {
    "jsonrpc": "2.0",
    "id": 2,
    "method": "tools/call",
    "params": {
        "name": "verify_agent",
        "arguments": {"agent_id": "fe8ab67d-0134-469d-99ca-ee930e8e9216"}
    }
}
resp_tool = requests.post(ENFORCED_SURFACE, headers=headers, json=tool_payload)
print(f"Tool Execution Status: HTTP {resp_tool.status_code}")
print(f"Tool Execution Body  : {resp_tool.text}")

# --- ACTION C: Protected Non-Public Method (Triggers Gateway Enforcement Deny) ---
print("\n--- 3. Testing Policy Enforcement Denial (resources/list) ---")
deny_payload = {
    "jsonrpc": "2.0",
    "id": 3,
    "method": "resources/list",
    "params": {}
}
resp_deny = requests.post(ENFORCED_SURFACE, headers=headers, json=deny_payload)
print(f"Enforcement Denial Status: HTTP {resp_deny.status_code}")
print(f"Enforcement Denial Body  : {resp_deny.text}")

print("\n=======================================================")
print("🏁 ENFORCEMENT ACTIONS DISPATCHED!")
print("=======================================================\n")
