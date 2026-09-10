import time
import uuid
import jwt

# --- Fixed Configuration (Static for this Key) ---
CLIENT_ID = "muid_mc_81ded832a8666fd0190a7f9b9ed54d57"
KEY_ID = "muid_ck_f06013270ed6eea740df2dbdefae3612"
KID = "kid_0d5cff87e0cc"
AUDIENCE = "https://api.staging.mudraid.ai/oauth2/client-keys/proof"

with open("private_key.pem", "rb") as f:
    private_key = f.read()

print("--- MUDRAID FAST PROOF SIGNER ---")
challenge_id = input("1. Paste Challenge ID: ").strip()
nonce = input("2. Paste Nonce: ").strip()

now = int(time.time())
claims = {
    "challenge_id": challenge_id,
    "nonce": nonce,
    "aud": AUDIENCE,
    "iss": CLIENT_ID,
    "sub": CLIENT_ID,
    "key_id": KEY_ID,
    "iat": now,
    "exp": now + 300,
    "jti": uuid.uuid4().hex,
}

headers = {"alg": "RS256", "kid": KID}

proof_jws = jwt.encode(claims, private_key, algorithm="RS256", headers=headers)

print("\n================ COPY THIS JWS ================")
print(proof_jws)
print("================================================\n")
