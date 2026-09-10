import time
import uuid
import json
import jwt
import requests

# --- Configuration ---
CLIENT_ID = "muid_mc_017f5174d12681a7f34f4b6f2e1e2bf2"
KID = "kid_46fbf4431874"
TOKEN_ENDPOINT = "https://api.staging.mudraid.ai/oauth2/token"
RESOURCE_URI = "https://pradeepplatform.mudraidtesting.online"

# 1. Sign RFC 7523 assertion locally
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

client_assertion = jwt.encode(claims, private_key, algorithm="RS256", headers={"alg": "RS256", "kid": KID})

# 2. Acquire Access Token from MudraID
payload = {
    "grant_type": "client_credentials",
    "client_assertion_type": "urn:ietf:params:oauth:client-assertion-type:jwt-bearer",
    "client_assertion": client_assertion,
    "resource": RESOURCE_URI,
    "scope": "tasks:read",
}

resp = requests.post(TOKEN_ENDPOINT, data=payload)

if resp.status_code != 200:
    print("❌ Error acquiring token:", resp.text)
    exit(1)

access_token = resp.json()["access_token"]

# 3. Decode Header and Payload Claims
token_header = jwt.get_unverified_header(access_token)
token_payload = jwt.decode(access_token, options={"verify_signature": False})

print("\n=======================================================")
print("🔐 1. ACCESS TOKEN - CRYPTOGRAPHIC HEADER:")
print("=======================================================")
print(json.dumps(token_header, indent=2))

print("\n=======================================================")
print("📋 2. ACCESS TOKEN - DECODED CLAIMS PAYLOAD:")
print("=======================================================")
print(json.dumps(token_payload, indent=2))
print("=======================================================\n")
