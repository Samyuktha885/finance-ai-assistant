from pydantic import BaseModel
from typing import Optional, List, Dict, Any


class ChatRequest(BaseModel):
    session_id: str
    message: str


class SourceRef(BaseModel):
    doc_id: str
    snippet: str
    score: float


class ChatResponse(BaseModel):
    session_id: str
    reply: str
    confidence: float
    handover: bool
    handover_summary: Optional[str] = None
    sources: List[SourceRef] = []
    explanation: Optional[str] = None
    remembered_facts: Dict[str, Any] = {}


class SessionState(BaseModel):
    session_id: str
    history: List[Dict[str, str]] = []      # [{"role": "user"/"assistant", "content": "..."}]
    facts: Dict[str, Any] = {}                 # extracted user facts, e.g. {"monthly_income": 50000}
    failed_turns: int = 0                        # consecutive low-confidence turns, drives handover
