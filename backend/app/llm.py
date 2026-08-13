"""
Thin LLM client wrapper. Deliberately provider-agnostic so you can point this at
any OpenAI-compatible endpoint: Groq (free tier, fast), Together AI, a local Ollama
server, or the actual OpenAI/Anthropic API. This keeps agent code free of any
one vendor's SDK quirks.

Set env vars before running:
    LLM_API_BASE  e.g. https://api.groq.com/openai/v1
    LLM_API_KEY   your provider key
    LLM_MODEL     e.g. llama-3.1-8b-instant
"""
import os
import json
import httpx
from dotenv import load_dotenv

load_dotenv()  # reads a .env file in the backend/ folder, if present

LLM_API_BASE = os.environ.get("LLM_API_BASE", "")
LLM_API_KEY = os.environ.get("LLM_API_KEY", "")
LLM_MODEL = os.environ.get("LLM_MODEL", "")


async def chat_completion(messages: list[dict], temperature: float = 0.3, json_mode: bool = False) -> str:
    """
    messages: [{"role": "system"|"user"|"assistant", "content": "..."}]
    Returns the assistant's text content.

    If LLM_API_BASE isn't configured yet, raises a clear error rather than
    silently failing — fill in your provider details in .env or the shell
    before running the server.
    """
    if not LLM_API_BASE or not LLM_API_KEY or not LLM_MODEL:
        raise RuntimeError(
            "LLM not configured. Set LLM_API_BASE, LLM_API_KEY, LLM_MODEL env vars "
            "(see README.md setup section) before starting the server."
        )

    payload = {
        "model": LLM_MODEL,
        "messages": messages,
        "temperature": temperature,
    }
    if json_mode:
        payload["response_format"] = {"type": "json_object"}

    async with httpx.AsyncClient(timeout=30.0) as client:
        resp = await client.post(
            f"{LLM_API_BASE}/chat/completions",
            headers={"Authorization": f"Bearer {LLM_API_KEY}", "Content-Type": "application/json"},
            json=payload,
        )
        resp.raise_for_status()
        data = resp.json()
        return data["choices"][0]["message"]["content"]


async def chat_completion_json(messages: list[dict], temperature: float = 0.2) -> dict:
    """Same as chat_completion but parses the result as JSON. Strips code fences defensively."""
    raw = await chat_completion(messages, temperature=temperature, json_mode=True)
    cleaned = raw.strip().removeprefix("```json").removeprefix("```").removesuffix("```").strip()
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        return {"_parse_error": True, "raw": raw}
