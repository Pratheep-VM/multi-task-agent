import json
import uuid
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives import serialization
from jwt.algorithms import RSAAlgorithm

# 1. Generate RSA 2048-bit Private Key
private_key = rsa.generate_private_key(
    public_exponent=65537,
    key_size=2048
)

# 2. Save Private Key to private_key.pem
pem = private_key.private_bytes(
    encoding=serialization.Encoding.PEM,
    format=serialization.PrivateFormat.PKCS8,
    encryption_algorithm=serialization.NoEncryption()
).decode('utf-8')

with open("private_key.pem", "w") as f:
    f.write(pem)

# 3. Generate Public JWK JSON
kid = f"kid_{uuid.uuid4().hex[:12]}"
jwk_dict = json.loads(RSAAlgorithm.to_jwk(private_key.public_key()))
jwk_dict["kid"] = kid
jwk_dict["use"] = "sig"
jwk_dict["alg"] = "RS256"

print("\n=======================================================")
print("👉 COPY AND PASTE THIS ENTIRE JSON BLOCK INTO MUDRAID:")
print("=======================================================\n")
print(json.dumps(jwk_dict, indent=2))
print("\n=======================================================")
print(f"✅ Private key saved locally to: private_key.pem")
print(f"✅ Key ID (kid): {kid}")
print("=======================================================")
