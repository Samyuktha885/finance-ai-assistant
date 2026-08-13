"""
Orchestrator Agent: the entry point for each turn. Extracts durable business
facts from the user's message (e.g. "we make 5 lakh a month" -> monthly_revenue:
500000), updates session memory, then hands the question + context to the
Knowledge and Reasoning agents (via graph.py) and assembles the final response.

Fact extraction is intentionally simple (regex-based for common patterns) —
swap for an LLM extraction call if you want it to generalize further, but for
demo purposes a few concrete patterns retained across turns already satisfies
"remembering important user-provided information" and "avoiding repetitive
questions" from the brief.
"""
import re
from app import memory


GREETING_PATTERN = re.compile(
    r"^\s*(hi|hii+|hello+|hey+|good\s*(morning|afternoon|evening)|yo|sup|what'?s\s*up)\s*[!.?]*\s*$",
    re.IGNORECASE,
)

GREETING_REPLY = (
    "Hi! I'm Ledgr, your AI business finance advisor. I can help with cash flow, "
    "business loans, break-even analysis, working capital, GST basics, and more. "
    "What's on your mind?"
)

QUESTION_STARTERS = (
    "what", "how", "why", "when", "where", "who", "which",
    "should", "can", "could", "would", "will",
    "is", "are", "does", "do", "did",
    "help", "tell", "explain", "calculate",
)


def looks_like_question(message: str) -> bool:
    """Distinguishes an actual question/request from a plain statement of fact
    (e.g. 'our revenue is 800000' with no question). Used so that stating facts
    doesn't trigger unsolicited advice — instead the assistant acknowledges
    what it learned and asks what the person wants help with."""
    stripped = message.strip()
    if "?" in stripped:
        return True
    first_word = stripped.split()[0].lower() if stripped.split() else ""
    return first_word in QUESTION_STARTERS


def is_greeting(message: str) -> bool:
    """Detects simple greetings/small talk so they get a warm reply instead of
    being routed through the finance KB/calculator pipeline, which would
    otherwise (correctly, but unhelpfully) say 'I don't have enough information'."""
    return bool(GREETING_PATTERN.match(message.strip()))


FACT_PATTERNS = {
    "monthly_revenue": re.compile(r"(?:revenue|turnover|make|earn)[^\d]{0,15}(\d[\d,]*)", re.IGNORECASE),
    "employee_count": re.compile(r"(\d+)\s*(?:employees|staff|people)", re.IGNORECASE),
    "industry": re.compile(
        r"\b(retail|manufacturing|restaurant|consulting|software|construction|e-commerce|healthcare|logistics)\b",
        re.IGNORECASE,
    ),
}


def extract_facts(message: str) -> dict:
    facts = {}
    revenue_match = FACT_PATTERNS["monthly_revenue"].search(message)
    if revenue_match:
        facts["monthly_revenue"] = int(revenue_match.group(1).replace(",", ""))

    employee_match = FACT_PATTERNS["employee_count"].search(message)
    if employee_match:
        facts["employee_count"] = int(employee_match.group(1))

    industry_match = FACT_PATTERNS["industry"].search(message)
    if industry_match:
        facts["industry"] = industry_match.group(1).lower()

    return facts


def prepare_turn_context(session_id: str, message: str) -> dict:
    """Called at the start of each turn: extract + store facts, log the user
    turn, and return the context the rest of the graph needs."""
    new_facts = extract_facts(message)
    if new_facts:
        memory.update_facts(session_id, new_facts)
    memory.add_turn(session_id, "user", message)

    return {
        "facts_text": memory.facts_as_text(session_id),
        "history_text": memory.history_as_text(session_id),
    }


def finalize_turn(session_id: str, reply: str, was_confident: bool) -> None:
    memory.add_turn(session_id, "assistant", reply)
    memory.record_turn_outcome(session_id, was_confident)