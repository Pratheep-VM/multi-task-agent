import os
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI

load_dotenv()

key = os.getenv("XAI_API_KEY", "")
print(f"🔑 Key found: '{key[:7]}...{key[-4:]}'" if key else "❌ Key NOT found in .env")

try:
    llm = ChatOpenAI(
        model="grok-2-latest",
        api_key=key,
        base_url="https://api.x.ai/v1"
    )
    res = llm.invoke("Say 'Grok is working!' in 3 words.")
    print("✅ SUCCESS:", res.content)
except Exception as e:
    print("❌ FAILED:", e)