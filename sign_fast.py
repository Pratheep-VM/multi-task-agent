import time
import uuid
import jwt

# --- Pre-filled with client-4 details ---
CLIENT_ID = "muid_mc_49c859dded880fd160cc750d0a883ce5"
KEY_ID = "muid_ck_7885cabdb4293c98371a6accaa0c35c7"
KID = "kid_6a57465b5494"
AUDIENCE = "https://api.staging.mudraid.ai/oauth2/client-keys/proof"

with open("private_key.pem", "rb") as f:
    private_key = f.read()

print("\n--- MUDRAID PROOF SIGNER (CLIENT 4) ---")
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

with open("proof.txt", "w") as f:
    f.write(proof_jws)

print("\n=======================================================")
print("✅ Full token saved to 'proof.txt'!")
print("=======================================================\n")
