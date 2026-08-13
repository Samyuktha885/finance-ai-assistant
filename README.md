# Finance AI Assistant — iNextLabs Internship Selection Project

A trustworthy multi-agent conversational AI for personal finance (budgeting, investments,
tax planning, insurance, retirement) — built for the "Building Trustworthy Conversational
AI Agents" problem statement.

## Architecture

```
User (text/voice)
      |
      v
Orchestrator Agent  <-- session memory (per-session history + extracted facts)
      |
      +--> Knowledge Agent  (RAG over finance KB, ChromaDB + embeddings)
      |
      +--> Reasoning Agent  (finance calculators + self-reported confidence)
      |
      v
Confidence Check  (combines retrieval score + reasoning confidence)
      |
      +--> high confidence --> Response to user (with explanation)
      |
      +--> low confidence  --> Human handover (auto-generated summary)
```

## Project layout

```
backend/
  app/
    main.py            FastAPI app, exposes POST /chat
    graph.py            LangGraph wiring of the 3 agents + confidence branch
    memory.py            Session memory store (per-session history + facts)
    confidence.py        Confidence scoring + uncertainty logic
    handover.py           Handover trigger + summary generation
    models.py              Pydantic request/response schemas
    llm.py                   Thin LLM client wrapper — swap in any provider here
    agents/
      orchestrator.py         Routes turns, extracts facts, calls other agents
      knowledge_agent.py         RAG retrieval over the finance KB
      reasoning_agent.py            Finance calculators (SIP, budget split, tax hints)
    kb/
      docs/                            Markdown KB files — ADD YOUR CONTENT HERE
      ingest.py                          Loads docs/ into a local ChromaDB collection
  requirements.txt
```

## Setup

```bash
cd backend
python -m venv venv
source venv/bin/activate       # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

**Set an LLM provider.** `app/llm.py` is deliberately a thin wrapper so you can point it at
any OpenAI-compatible endpoint (Groq, Together, Ollama running locally, or the actual
OpenAI/Anthropic API). Set these env vars before running:

```bash
export LLM_API_BASE="https://api.groq.com/openai/v1"   # example: Groq free tier
export LLM_API_KEY="your-key-here"
export LLM_MODEL="llama-3.1-8b-instant"                  # any open-source model works
```

**Ingest the knowledge base** (run this after you add your KB docs to `app/kb/docs/`):

```bash
python -m app.kb.ingest
```

**Run the API:**

```bash
uvicorn app.main:app --reload --port 8000
```

Test it:

```bash
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"session_id": "demo1", "message": "I earn 50000 a month, how should I budget?"}'
```

## What's a stub vs what's real

- **Real, working**: FastAPI app, LangGraph graph wiring, session memory, ChromaDB
  ingestion, confidence-check branching logic, handover summary generation.
- **You need to fill in**: KB docs (`app/kb/docs/` — currently has 2 sample files, add
  15-20 more), and finance calculator logic in `reasoning_agent.py` (currently has one
  working SIP calculator as a template — add budget split, tax-saving hints, etc.).
- **Not built yet, on purpose**: React dashboard, voice I/O. This scaffold is the backend
  brain — wire the frontend to `POST /chat` once the agent logic is solid, per the build
  plan (memory + uncertainty + handover carry 55% of the grade; UI/voice carry 5%).

## How this maps to the evaluation criteria

| Criteria | Weight | Where it lives |
|---|---|---|
| Functional correctness / demo | 30% | `main.py`, `graph.py` — end-to-end pipeline |
| Context management & memory | 20% | `memory.py`, orchestrator fact extraction |
| Uncertainty handling | 20% | `confidence.py` — never answers below threshold without flagging it |
| Human handover | 15% | `handover.py` — trigger + auto-generated summary |
| Architecture & docs | 10% | This README + agent separation |
| Innovation / UX | 5% | Explainability in response payload, voice/dashboard (to add) |
