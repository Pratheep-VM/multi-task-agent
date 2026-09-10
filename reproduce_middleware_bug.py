import time
import uuid
import json
import jwt
import requests

# =====================================================================
# 1. Mint a Real MudraID Access Token
# =====================================================================
CLIENT_ID = "muid_mc_017f5174d12681a7f34f4b6f2e1e2bf2"
KID = "kid_46fbf4431874"
TOKEN_ENDPOINT = "https://api.staging.mudraid.ai/oauth2/token"
RESOURCE_URI = "https://pradeepplatform.mudraidtesting.online"

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

payload = {
    "grant_type": "client_credentials",
    "client_assertion_type": "urn:ietf:params:oauth:client-assertion-type:jwt-bearer",
    "client_assertion": client_assertion,
    "resource": RESOURCE_URI,
    "scope": "tasks:read",
}
resp = requests.post(TOKEN_ENDPOINT, data=payload).json()
access_token = resp["access_token"]

# Decode token payload
token_claims = jwt.decode(access_token, options={"verify_signature": False})

print("====================================================================")
print("🔍 1. REAL TOKEN CLAIMS ISSUED BY MUDRAID:")
print("====================================================================")
print("Token 'scope' claim :", repr(token_claims.get("scope")), "(Type:", type(token_claims.get("scope")).__name__ + ")")
print("Token 'scopes' claim:", repr(token_claims.get("scopes")), "(Type:", type(token_claims.get("scopes")).__name__ + ")")

REQUIRED_ROUTE_SCOPE = "tasks:read"
print(f"\nTarget Route Requires Scope: '{REQUIRED_ROUTE_SCOPE}'")

# =====================================================================
# 2. RUNNING CURRENT BUGGY MIDDLEWARE CODE (from middleware.py:192)
# =====================================================================
print("\n====================================================================")
print("🧪 2. RUNNING CURRENT BUGGY MIDDLEWARE CODE (middleware.py:192):")
print("====================================================================")

# This is the exact check in mudraid-middleware package:
token_scopes = token_claims.get("scopes")

if not isinstance(token_scopes, list) or REQUIRED_ROUTE_SCOPE not in token_scopes:
    err_response = {
        "error_code": "MISSING_SCOPE",
        "message": f"required scope '{REQUIRED_ROUTE_SCOPE}' not present in token"
    }
    print("❌ HTTP 403 FORBIDDEN REJECTION:")
    print(json.dumps(err_response, indent=2))
    print("--> BUG TRIGGERED: Rejects valid token because 'scopes' is None!")
else:
    print("✅ Request Allowed")

# =====================================================================
# 3. RUNNING THE FIXED / PATCHED LOGIC
# =====================================================================
print("\n====================================================================")
print("🛠️ 3. RUNNING THE FIXED / PATCHED MIDDLEWARE LOGIC:")
print("====================================================================")

raw_scope = token_claims.get("scope") or token_claims.get("scopes")
if isinstance(raw_scope, str):
    parsed_scopes = set(raw_scope.split())
elif isinstance(raw_scope, (list, tuple, set)):
    parsed_scopes = set(raw_scope)
else:
    parsed_scopes = set()

if REQUIRED_ROUTE_SCOPE not in parsed_scopes:
    print("❌ HTTP 403: Scope Missing")
else:
    print("✅ HTTP 200 OK: REQUEST ALLOWED!")
    print(f"   Successfully matched '{REQUIRED_ROUTE_SCOPE}' inside token scope '{raw_scope}'")
print("====================================================================\n")
