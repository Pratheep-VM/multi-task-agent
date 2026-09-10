import time
import uuid
import json
import jwt
import requests

# =====================================================================
# 1. Configuration for Client 5
# =====================================================================
CLIENT_ID = "muid_mc_8fd8f395841de047d1e9d9a524d2dfe1"
KID = "kid_8b7940177e69"
TOKEN_ENDPOINT = "https://api.staging.mudraid.ai/oauth2/token"
MCP_SURFACE = "https://api.staging.mudraid.ai/mcp"

# =====================================================================
# 2. Sign Assertion & Mint Token
# =====================================================================
print("\n[Step 1] Minting Access Token for MCP Surface...")
with open("private_key.pem", "rb") as f:
    private_key = f.read()

now = int(time.time())
claims = {
    "iss": CLIENT_ID, "sub": CLIENT_ID, "aud": TOKEN_ENDPOINT,
    "iat": now, "exp": now + 60, "jti": uuid.uuid4().hex,
}
headers_jws = {"alg": "RS256", "kid": KID}
client_assertion = jwt.encode(claims, private_key, algorithm="RS256", headers=headers_jws)

payload = {
    "grant_type": "client_credentials",
    "client_assertion_type": "urn:ietf:params:oauth:client-assertion-type:jwt-bearer",
    "client_assertion": client_assertion,
    "resource": MCP_SURFACE,
    "scope": "tools/list tools/call",
}
resp = requests.post(TOKEN_ENDPOINT, data=payload).json()
access_token = resp["access_token"]
print("✅ Token acquired successfully!")

# =====================================================================
# 3. Base Headers
# =====================================================================
api_headers = {
    "Authorization": f"Bearer {access_token}",
    "Content-Type": "application/json",
    "Accept": "application/json, text/event-stream"
}

# =====================================================================
# 4. Step A: Send MCP Protocol Handshake (initialize)
# =====================================================================
print("\n[Step 2A] Sending MCP 'initialize' handshake...")
init_payload = {
    "jsonrpc": "2.0",
    "id": 1,
    "method": "initialize",
    "params": {
        "protocolVersion": "2024-11-05",
        "capabilities": {},
        "clientInfo": {
            "name": "mudraid-python-client",
            "version": "1.0.0"
        }
    }
}
init_resp = requests.post(MCP_SURFACE, headers=api_headers, json=init_payload)
print(f"Handshake Status: HTTP {init_resp.status_code}")

# Capture session ID from response headers
session_id = init_resp.headers.get("Mcp-Session-Id") or init_resp.headers.get("mcp-session-id")

if session_id:
    print(f"✅ Established MCP Session ID: {session_id}")
    api_headers["Mcp-Session-Id"] = session_id

# =====================================================================
# 5. Step B: Query Tools List
# =====================================================================
print("\n[Step 2B] Querying MCP Tools Catalog ('tools/list')...")
list_payload = {
    "jsonrpc": "2.0",
    "id": 2,
    "method": "tools/list",
    "params": {}
}
list_resp = requests.post(MCP_SURFACE, headers=api_headers, json=list_payload)

print(f"\n================ MCP TOOL REGISTRY (HTTP {list_resp.status_code}) ================")
try:
    print(json.dumps(list_resp.json(), indent=2))
except Exception:
    print(list_resp.text)
print("=================================================================\n")

# =====================================================================
# 6. Step C: Execute on Direct Upstream Server 
# =====================================================================
DIRECT_UPSTREAM = "https://mcp-test.mudra.id/mcp"
print(f"\n[Step 2C] Invoking Tool on Direct Upstream ({DIRECT_UPSTREAM})...")

call_payload = {
    "jsonrpc": "2.0",
    "id": 3,
    "method": "tools/call",
    "params": {
        "name": "verify_agent",
        "arguments": {
            "agent_id": "d9ddd23f-e973-44d9-8ae7-99b4c3bc6b7c"
        }
    }
}

call_resp = requests.post(DIRECT_UPSTREAM, headers=api_headers, json=call_payload)

print(f"\n================ TOOL EXECUTION (HTTP {call_resp.status_code}) ================")
try:
    print(json.dumps(call_resp.json(), indent=2))
except Exception:
    print(call_resp.text)
print("=================================================================\n")
