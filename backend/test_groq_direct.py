"""
Standalone Groq connectivity test — bypasses the whole app to isolate whether
the issue is your API key, network, or something in our app code.
Run with: python test_groq_direct.py
"""
import os
from dotenv import load_dotenv
import httpx

load_dotenv()

api_base = os.environ.get("LLM_API_BASE", "")
api_key = os.environ.get("LLM_API_KEY", "")
model = os.environ.get("LLM_MODEL", "")

print(f"LLM_API_BASE = {api_base}")
print(f"LLM_MODEL    = {model}")
print(f"LLM_API_KEY  = {'set, starts with ' + api_key[:7] if api_key else 'NOT SET'}")
print()
print("Sending a test request to Groq (10 second timeout)...")

try:
    response = httpx.post(
        f"{api_base}/chat/completions",
        headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
        json={
            "model": model,
            "messages": [{"role": "user", "content": "Say hello in exactly 3 words."}],
        },
        timeout=10.0,
    )
    print("Status code:", response.status_code)
    print("Response body:", response.text)
except Exception as e:
    print("FAILED with exception:", type(e).__name__, str(e))
