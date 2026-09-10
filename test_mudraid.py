from mudraid import Agent

client = Agent(base_url="https://api.staging.mudraid.ai")

URL = "https://pradeepplatform.mudraidtesting.online/api/v1/tasks"

print("--- EXECUTING POST REQUEST ---")
res_post = client.post(URL, json={"title": "Testing Declared operating limits"})

print(f"\nStatus Code: {res_post.status_code}")

# 1. PRINT MUDRAID REQUEST HEADERS SENT BY SDK
print("\n📤 --- REQUEST HEADERS (Sent by MudraID SDK) ---")
for key, value in res_post.request.headers.items():
    print(f"  {key}: {value}")

# 2. PRINT FULL RESPONSE HEADERS FROM SERVER
print("\n📥 --- FULL RESPONSE HEADERS (Returned by Server) ---")
for key, value in res_post.headers.items():
    print(f"  {key}: {value}")

print("\n📦 --- RESPONSE BODY ---")
print(res_post.text)
