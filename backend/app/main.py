from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.models import ChatRequest, ChatResponse, SourceRef
from app.agents import orchestrator, knowledge_agent
from app.graph import compiled_graph
from app import memory

app = FastAPI(title="Ledgr — AI Business Finance Advisor")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # tighten before any real deployment
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def warm_up_embedding_model():
    """
    Loads the sentence-transformers embedding model into memory at server
    startup instead of on the first real chat request. Without this, the very
    first /chat call pays the cost of loading the model (can take 20-30+
    seconds), which looks like the app hanging. Every request after that is
    fast regardless — this just moves that one-time cost to server startup,
    where a short delay is expected, instead of the user's first message.
    """
    try:
        knowledge_agent.retrieve("warm up query", top_k=1)
        print("Embedding model warmed up — ready for fast responses.")
    except Exception as e:
        # KB might not be ingested yet — don't crash startup over this
        print(f"Warm-up skipped (KB may not be ingested yet): {e}")


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/chat", response_model=ChatResponse)
async def chat(req: ChatRequest):
    session_id = req.session_id
    message = req.message

    # Orchestrator: extract facts, log turn, prep context
    turn_context = orchestrator.prepare_turn_context(session_id, message)
    session = memory.get_session(session_id)

    # Greetings/small talk get a warm reply directly, skipping the finance
    # KB/calculator pipeline entirely — otherwise "hi" would (correctly, but
    # unhelpfully) come back as "I don't have enough information to answer."
    if orchestrator.is_greeting(message):
        reply = orchestrator.GREETING_REPLY
        orchestrator.finalize_turn(session_id, reply, was_confident=True)
        return ChatResponse(
            session_id=session_id,
            reply=reply,
            confidence=1.0,
            handover=False,
            handover_summary=None,
            sources=[],
            explanation="Greeting detected — handled directly without KB lookup.",
            remembered_facts=session.facts,
        )

    # If the person just stated facts about their business with no actual
    # question ("our revenue is 800000", no "?", no question word), acknowledge
    # what was learned and ask what they need — rather than pushing unsolicited
    # advice from whatever KB doc happens to loosely match the topic.
    newly_extracted = orchestrator.extract_facts(message)
    if newly_extracted and not orchestrator.looks_like_question(message):
        fact_summary = ", ".join(f"{k.replace('_', ' ')}: {v}" for k, v in newly_extracted.items())
        reply = f"Got it — noted {fact_summary}. What would you like help with — cash flow, loans, break-even, working capital, or something else?"
        orchestrator.finalize_turn(session_id, reply, was_confident=True)
        return ChatResponse(
            session_id=session_id,
            reply=reply,
            confidence=1.0,
            handover=False,
            handover_summary=None,
            sources=[],
            explanation="Facts recorded, no question asked yet — prompted for what's needed.",
            remembered_facts=session.facts,
        )

    graph_input = {
        "question": message,
        "facts_text": turn_context["facts_text"],
        "history_text": turn_context["history_text"],
        "consecutive_failed_turns": session.failed_turns,
    }

    result = await compiled_graph.ainvoke(graph_input)

    overall_confidence = result["overall_confidence"]
    will_handover = result["will_handover"]

    if will_handover:
        reply = (
            "I want to make sure you get the right answer here, so I'm connecting you "
            "with a member of our team who can help further."
        )
        was_confident = False
    else:
        reply = result["answer"]
        was_confident = overall_confidence >= 0.45  # mirrors confidence.HANDOVER_THRESHOLD

    orchestrator.finalize_turn(session_id, reply, was_confident)

    sources = [
        SourceRef(doc_id=c["source"], snippet=c["text"][:200], score=round(c["similarity"], 3))
        for c in result["kb_chunks"]
    ]

    return ChatResponse(
        session_id=session_id,
        reply=reply,
        confidence=overall_confidence,
        handover=will_handover,
        handover_summary=result.get("handover_summary"),
        sources=sources,
        explanation=result.get("justification"),
        remembered_facts=session.facts,
    )