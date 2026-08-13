"""
Quick manual test for the /chat endpoint. Run with:
    python test_chat.py
(server must already be running in another terminal: uvicorn app.main:app --port 8000)
"""
import httpx

response = httpx.post(
    "http://localhost:8000/chat",
    json={"session_id": "test1", "message": "I earn 50000 a month, how should I budget?"},
    timeout=30.0,
)

print("Status code:", response.status_code)
print(response.json())
