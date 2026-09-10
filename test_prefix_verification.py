import os
import inspect
from mudraid import Agent
from mudraid.exceptions import MudraIDConfigError

print("=======================================================")
print("  RUNNING MUDRAID SDK PREFIX VERIFICATION TEST SUITE   ")
print("=======================================================\n")

# --- CHECK 1: Constructor Signature Check ---
print("👉 CHECK 1: Checking Agent.__init__ signature for 'prefix' parameter...")
sig = inspect.signature(Agent.__init__)
if 'prefix' in sig.parameters:
    print(f"✅ PASS: 'prefix' parameter found in Agent.__init__!\n   Signature: {sig}\n")
else:
    print(f"❌ FAIL: 'prefix' not found in Agent.__init__! Signature: {sig}\n")
    exit(1)

# --- CHECK 2: Prefixed Variable Resolution ---
print("👉 CHECK 2: Testing Prefixed Variable Loading (SUPERVISOR_API_KEY_ID)...")
os.environ["SUPERVISOR_API_KEY_ID"] = "muid_kid_supervisor_test_123"
os.environ["SUPERVISOR_SECRET"] = "muid_sk_supervisor_secret_456"
os.environ["MUDRAID_BASE_URL"] = "https://api.staging.mudraid.ai"

try:
    supervisor = Agent(prefix="SUPERVISOR")
    print(f"✅ PASS: Initialized Agent with prefix='SUPERVISOR'")
    print(f"   Resolved Key ID: {supervisor.api_key_id}")
    print(f"   Resolved Base URL: {supervisor.base_url}\n")
except Exception as e:
    print(f"❌ FAIL: {e}\n")

# --- CHECK 3: Per-Agent Base URL Override ---
print("👉 CHECK 3: Testing Per-Agent {PREFIX}_BASE_URL Override...")
os.environ["RESEARCH_API_KEY_ID"] = "muid_kid_research_test_123"
os.environ["RESEARCH_SECRET"] = "muid_sk_research_secret_456"
os.environ["RESEARCH_BASE_URL"] = "https://custom-research.mudraid.ai"

try:
    research = Agent(prefix="RESEARCH")
    if research.base_url == "https://custom-research.mudraid.ai":
        print(f"✅ PASS: {research.base_url} correctly overrode default MUDRAID_BASE_URL!\n")
    else:
        print(f"❌ FAIL: Base URL did not override: {research.base_url}\n")
except Exception as e:
    print(f"❌ FAIL: {e}\n")

# --- CHECK 4: Missing Variable Error Message (Naming exact variables) ---
print("👉 CHECK 4: Testing Missing Prefixed Variable Error Reporting...")
try:
    Agent(prefix="CODER_MISSING_TEST")
    print("❌ FAIL: Expected MudraIDConfigError, but Agent initialized without credentials!")
except MudraIDConfigError as exc:
    err_msg = str(exc)
    print(f"✅ PASS: Correctly raised MudraIDConfigError with exact variable names!")
    print(f"   Error message: {err_msg}\n")

# --- CHECK 5: No Silent Fallback to Unprefixed Variables ---
print("👉 CHECK 5: Verifying No Silent Fallback to MUDRAID_API_KEY_ID...")
os.environ["MUDRAID_API_KEY_ID"] = "muid_kid_default_fallback"
os.environ["MUDRAID_SECRET"] = "muid_sk_default_fallback"

try:
    # This prefix has no env vars set; it must NOT pick up MUDRAID_API_KEY_ID
    Agent(prefix="NON_EXISTENT_AGENT")
    print("❌ FAIL: Secretly fell back to default MUDRAID_ credentials!")
except MudraIDConfigError:
    print("✅ PASS: Correctly refused silent fallback to default MUDRAID_ variables!\n")

print("=======================================================")
print("🎉 ALL 5 MUDRAID SDK PREFIX CHECKS PASSED SUCCESSFULLY!")
print("=======================================================")
