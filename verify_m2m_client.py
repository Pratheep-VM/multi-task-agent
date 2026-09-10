import time
import uuid
import jwt
import requests

# =====================================================================
# 1. Exact Configuration for testing-machine-client-4
# =====================================================================
CLIENT_ID = "muid_mc_017f5174d12681a7f34f4b6f2e1e2bf2"
KID = "kid_46fbf4431874"
TOKEN_ENDPOINT = "https://api.staging.mudraid.ai/oauth2/token"

# Your target resource from the registration:
RESOURCE_URI = "https://pradeepplatform.mudraidtesting.online" 

# =====================================================================
# 2. Build & Sign RFC 7523 Client Assertion
# =====================================================================
print("\n[Step 1] Signing RFC 7523 Client Assertion locally...")

with open("private_key.pem", "rb") as f:
    private_key = f.read()

now = int(time.time())
claims = {
    "iss": CLIENT_ID,
    "sub": CLIENT_ID,
    "aud": TOKEN_ENDPOINT,
    "iat": now,
    "exp": now + 60,
    "jti": uuid.uuid4().hex,
}

headers = {
    "alg": "RS256",
    "kid": KID
}

client_assertion = jwt.encode(claims, private_key, algorithm="RS256", headers=headers)
print("✅ Client assertion signed!")

# =====================================================================
# 3. Request Access Token from MudraID
# =====================================================================
print(f"\n[Step 2] Exchanging assertion for Access Token at {TOKEN_ENDPOINT}...")

payload = {
    "grant_type": "client_credentials",
    "client_assertion_type": "urn:ietf:params:oauth:client-assertion-type:jwt-bearer",
    "client_assertion": client_assertion,
    "resource":"https://pradeepplatform.mudraidtesting.online",
    "scope": "tasks:read",
}

response = requests.post(TOKEN_ENDPOINT, data=payload)

if response.status_code == 200:
    data = response.json()
    access_token = data.get("access_token")
    print("\n=======================================================")
    print("🎉 SUCCESS! M2M ACCESS TOKEN ACQUIRED:")
    print("=======================================================")
    print(f"• Access Token : {access_token[:40]}...")
    print(f"• Token Type   : {data.get('token_type', 'Bearer')}")
    print(f"• Expires In   : {data.get('expires_in')} seconds")
    print(f"• Scope        : {data.get('scope')}")
    print("=======================================================\n")
else:
    print(f"\n❌ Token Request Failed (HTTP {response.status_code}):")
    print(response.text)
    exit(1)

# =====================================================================
# 4. Call Target Platform
# =====================================================================
print(f"[Step 3] Calling Target Platform at {RESOURCE_URI}...")
api_headers = {
    "Authorization": f"Bearer {access_token}",
    "Content-Type": "application/json"
}

try:
    api_resp = requests.get(RESOURCE_URI, headers=api_headers, timeout=5)
    print(f"✅ Platform Response (HTTP {api_resp.status_code}): {api_resp.text[:150]}")
except Exception as e:
    print(f"ℹ️ Network observation: {e}")
