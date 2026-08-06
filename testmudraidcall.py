import requests
import mudraid

print("1️⃣ Testing Direct HTTP call (without MudraID)...")
try:
    res1 = requests.post("http://127.0.0.1:8000/api/v1/tasks", json={"title": "Direct Test Task"})
    print(f"   Status Code: {res1.status_code}")
    print(f"   Response   : {res1.text[:200]}")
except Exception as e:
    print(f"   Error: {e}")

print("\n2️⃣ Testing MudraID Authenticated call...")
try:
    client = mudraid.Agent()
    res2 = client.post("http://127.0.0.1:8000/api/v1/tasks", json={"title": "MudraID Test Task"})
    print(f"   Status Code: {res2.status_code}")
    print(f"   Response   : {res2.text[:200]}")
except Exception as e:
    print(f"   Error: {e}")