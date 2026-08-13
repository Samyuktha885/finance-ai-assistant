"""
Tests the JSON-mode request specifically (this is what reasoning_agent.py uses)
since the plain request already worked fine.
Run with: python test_groq_json_mode.py
"""
import os
from dotenv import load_dotenv
import httpx

load_dotenv()

api_base = os.environ.get("LLM_API_BASE", "")
api_key = os.environ.get("LLM_API_KEY", "")
model = os.environ.get("LLM_MODEL", "")

print("Sending a JSON-mode test request to Groq (15 second timeout)...")

try:
    response = httpx.post(
        f"{api_base}/chat/completions",
        headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
        json={
            "model": model,
            "messages": [
                {"role": "system", "content": "Respond only with a JSON object with one key 'greeting'."},
                {"role": "user", "content": "Say hello."},
            ],
            "response_format": {"type": "json_object"},
        },
        timeout=15.0,
    )
    print("Status code:", response.status_code)
    print("Response body:", response.text)
except Exception as e:
    print("FAILED with exception:", type(e).__name__, str(e))
