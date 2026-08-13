"""
Combines the Knowledge Agent's retrieval confidence with the Reasoning Agent's
self-reported confidence into one overall score, and decides whether the
answer is trustworthy enough to show the user directly or should trigger
handover. Tune the weights/threshold once you see real demo behavior.
"""

RETRIEVAL_WEIGHT = 0.4
REASONING_WEIGHT = 0.6
HANDOVER_THRESHOLD = 0.45          # below this -> flag for handover consideration
CONSECUTIVE_FAILURES_FOR_HANDOVER = 2  # repeated low-confidence turns -> handover


def compute_overall_confidence(retrieval_confidence: float, self_confidence: float, used_calculator: bool = False) -> float:
    """
    When the answer came from an exact calculator (used_calculator=True), the
    KB retrieval score is irrelevant — the retrieval agent may have returned
    weak matches simply because the question didn't need the KB at all, not
    because the answer is untrustworthy. In that case, self_confidence alone
    (from the reasoning agent, already floored high for calculator answers)
    is the overall confidence.

    Otherwise, blend retrieval + reasoning confidence as before.
    """
    if used_calculator:
        return round(self_confidence, 3)
    return round(RETRIEVAL_WEIGHT * retrieval_confidence + REASONING_WEIGHT * self_confidence, 3)


def is_confident_enough(overall_confidence: float) -> bool:
    return overall_confidence >= HANDOVER_THRESHOLD


def should_handover(overall_confidence: float, consecutive_failed_turns: int, message: str) -> bool:
    """Handover triggers on: low confidence, repeated failures, or explicit
    user request / frustration signal — matches the brief's listed triggers
    (complex issues, sensitive topics, repeated misunderstanding, explicit request)."""
    explicit_request = any(
        phrase in message.lower()
        for phrase in ["talk to a human", "speak to someone", "real person", "human agent"]
    )
    frustration_signal = any(
        phrase in message.lower()
        for phrase in ["this isn't working", "you don't understand", "useless", "not helping"]
    )

    if explicit_request:
        return True
    if consecutive_failed_turns >= CONSECUTIVE_FAILURES_FOR_HANDOVER:
        return True
    if not is_confident_enough(overall_confidence) and frustration_signal:
        return True
    return not is_confident_enough(overall_confidence) and consecutive_failed_turns >= 1
