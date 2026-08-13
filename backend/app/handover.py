"""
Generates a concise summary for a human agent when a conversation is handed
over — per the brief: "generate a concise summary that enables a human
representative to continue the interaction efficiently."
"""
from app.llm import chat_completion


async def generate_handover_summary(history_text: str, facts_text: str, reason: str) -> str:
    system_prompt = (
        "You write brief handover notes for human support agents taking over a "
        "personal finance chatbot conversation. Summarize in 3-5 sentences: what "
        "the user wants, what's already been established, and why the AI is "
        "handing off. Be concise and factual — no filler."
    )
    user_prompt = (
        f"Reason for handover: {reason}\n\n"
        f"Known user facts: {facts_text}\n\n"
        f"Conversation so far:\n{history_text}"
    )
    return await chat_completion(
        [{"role": "system", "content": system_prompt}, {"role": "user", "content": user_prompt}],
        temperature=0.2,
    )
