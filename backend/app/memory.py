"""
Session memory, persisted to a local JSON file so sessions survive server
restarts (not just in-memory for the life of one process). Simple file-based
storage is fine for a hackathon/demo scale — swap for Redis or a real database
if this needs to handle concurrent production traffic.
"""
import json
import os
from app.models import SessionState

STORE_PATH = os.path.join(os.path.dirname(__file__), "session_store.json")

_sessions: dict[str, SessionState] = {}


def _load_from_disk() -> None:
    """Loads persisted sessions from disk into memory at startup."""
    global _sessions
    if not os.path.exists(STORE_PATH):
        return
    try:
        with open(STORE_PATH, "r", encoding="utf-8") as f:
            raw = json.load(f)
        _sessions = {sid: SessionState(**data) for sid, data in raw.items()}
    except (json.JSONDecodeError, TypeError, ValueError):
        # Corrupted or incompatible store file — start fresh rather than crashing
        _sessions = {}


def _save_to_disk() -> None:
    """Persists all sessions to disk. Called after every mutation — fine at
    hackathon-demo scale, not optimized for high write throughput."""
    try:
        with open(STORE_PATH, "w", encoding="utf-8") as f:
            json.dump({sid: session.model_dump() for sid, session in _sessions.items()}, f)
    except OSError:
        pass  # don't crash a request just because the disk write failed


_load_from_disk()


def get_session(session_id: str) -> SessionState:
    if session_id not in _sessions:
        _sessions[session_id] = SessionState(session_id=session_id)
        _save_to_disk()
    return _sessions[session_id]


def add_turn(session_id: str, role: str, content: str) -> None:
    session = get_session(session_id)
    session.history.append({"role": role, "content": content})
    # Keep last 20 turns in context to bound prompt size — tune as needed
    session.history = session.history[-20:]
    _save_to_disk()


def update_facts(session_id: str, new_facts: dict) -> None:
    session = get_session(session_id)
    session.facts.update({k: v for k, v in new_facts.items() if v is not None})
    _save_to_disk()


def record_turn_outcome(session_id: str, was_confident: bool) -> None:
    session = get_session(session_id)
    session.failed_turns = 0 if was_confident else session.failed_turns + 1
    _save_to_disk()


def history_as_text(session_id: str, max_turns: int = 8) -> str:
    session = get_session(session_id)
    recent = session.history[-max_turns:]
    return "\n".join(f"{t['role']}: {t['content']}" for t in recent)


def facts_as_text(session_id: str) -> str:
    session = get_session(session_id)
    if not session.facts:
        return "none yet"
    return ", ".join(f"{k}={v}" for k, v in session.facts.items())