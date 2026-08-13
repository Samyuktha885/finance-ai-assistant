"""
LangGraph wiring: knowledge retrieval + reasoning run, then a conditional
branch on confidence sends the turn either to a direct response or to
handover-summary generation. This is the "orchestrator" as a graph — the
Orchestrator Agent's routing/memory logic lives in agents/orchestrator.py and
is called before/after this graph runs (see main.py).
"""
from typing import TypedDict, Optional
from langgraph.graph import StateGraph, END

from app.agents import knowledge_agent, reasoning_agent
from app import confidence as confidence_module
from app import handover as handover_module


class GraphState(TypedDict):
    question: str
    facts_text: str
    history_text: str
    kb_chunks: list
    retrieval_confidence: float
    answer: str
    self_confidence: float
    justification: str
    used_calculator: bool
    overall_confidence: float
    consecutive_failed_turns: int
    will_handover: bool
    handover_summary: Optional[str]


async def node_retrieve_knowledge(state: GraphState) -> dict:
    result = knowledge_agent.retrieve(state["question"])
    return {"kb_chunks": result["chunks"], "retrieval_confidence": result["retrieval_confidence"]}


async def node_reason(state: GraphState) -> dict:
    kb_context = "\n\n".join(f"[{c['source']}] {c['text']}" for c in state["kb_chunks"])
    result = await reasoning_agent.synthesize_answer(
        question=state["question"],
        kb_context=kb_context,
        facts_text=state["facts_text"],
        history_text=state["history_text"],
    )
    used_calculator = result.get("used_calculator", False)
    overall = confidence_module.compute_overall_confidence(
        state["retrieval_confidence"], result["self_confidence"], used_calculator=used_calculator
    )
    return {
        "answer": result["answer"],
        "self_confidence": result["self_confidence"],
        "justification": result["justification"],
        "used_calculator": used_calculator,
        "overall_confidence": overall,
    }


async def node_decide_handover(state: GraphState) -> dict:
    will_handover = confidence_module.should_handover(
        state["overall_confidence"], state["consecutive_failed_turns"], state["question"]
    )
    return {"will_handover": will_handover}


async def node_generate_handover_summary(state: GraphState) -> dict:
    reason = (
        "explicit user request or repeated low confidence"
        if state["overall_confidence"] < confidence_module.HANDOVER_THRESHOLD
        else "user requested a human"
    )
    summary = await handover_module.generate_handover_summary(
        state["history_text"], state["facts_text"], reason
    )
    return {"handover_summary": summary}


def route_after_decision(state: GraphState) -> str:
    return "handover" if state["will_handover"] else "respond"


def build_graph():
    graph = StateGraph(GraphState)

    graph.add_node("retrieve_knowledge", node_retrieve_knowledge)
    graph.add_node("reason", node_reason)
    graph.add_node("decide_handover", node_decide_handover)
    graph.add_node("handover", node_generate_handover_summary)
    graph.add_node("respond", lambda state: {"answer": state["answer"]})  # no-op, but must write something

    graph.set_entry_point("retrieve_knowledge")
    graph.add_edge("retrieve_knowledge", "reason")
    graph.add_edge("reason", "decide_handover")
    graph.add_conditional_edges(
        "decide_handover", route_after_decision, {"handover": "handover", "respond": "respond"}
    )
    graph.add_edge("handover", END)
    graph.add_edge("respond", END)

    return graph.compile()


compiled_graph = build_graph()
