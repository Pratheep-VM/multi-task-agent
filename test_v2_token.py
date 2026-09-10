import json
import base64
import time
import uuid
import requests
import jwt
from cryptography.hazmat.primitives import serialization

CLIENT_ID = "muid_mc_81ded832a8666fd0190a7f9b9ed54d57"
TOKEN_ENDPOINT = "https://api.staging.mudraid.ai/oauth2/token"
RESOURCE = "https://pradeepplatform.mudraidtesting.online"

# 1. Load your local Private Key
with open("private_key.pem", "rb") as f:
    private_key = serialization.load_pem_private_key(f.read(), password=None)

# 2. Try both Token Endpoint URL and Base URL for Audience
audiences_to_test = [
    "https://api.staging.mudraid.ai/oauth2/token",
    "https://api.staging.mudraid.ai"
]

for aud in audiences_to_test:
    print(f"\n=======================================================")
    print(f"Testing with aud: {aud}")
    print(f"=======================================================")

    now = int(time.time())
    claims = {
        "iss": CLIENT_ID,
        "sub": CLIENT_ID,
        "aud": aud,
        "iat": now,
        "exp": now + 60,
        "jti": uuid.uuid4().hex
    }

    # Sign JWT - PyJWT attaches the standard RS256 header
    assertion = jwt.encode(claims, private_key, algorithm="RS256")

    form_data = {
        "client_id": CLIENT_ID,
        "grant_type": "client_credentials",
        "client_assertion_type": "urn:ietf:params:oauth:client-assertion-type:jwt-bearer",
        "client_assertion": assertion,
        "resource": RESOURCE,
        "scope": "tasks:read"
    }

    response = requests.post(TOKEN_ENDPOINT, data=form_data)
    print(f"Status Code: {response.status_code}")
    print(f"Response Body:\n{response.text}")

    if response.status_code == 200:
        print("\n🎉 SUCCESS! Token Minted!")
        break

