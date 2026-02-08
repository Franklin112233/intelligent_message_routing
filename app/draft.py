"""Draft response: policy-grounded with citations, fallback, confidence escalation."""

from typing import Optional

from app.classify import ClassificationResult
from app.kb import get_snippet
from app.llm import is_available, generate_draft

# Supported intents for draft generation (≥2 per spec)
DRAFT_INTENTS = {
    "card_lost_stolen",
    "suspected_fraud",
    "fraud",
    "card_lost",
    "lost_card",
    "stolen_card",
}

CONFIDENCE_THRESHOLD = 0.7


def _intent_eligible_for_draft(intent: str) -> bool:
    return intent.strip().lower() in DRAFT_INTENTS or intent.strip().lower().replace(
        " ", "_"
    ) in {"card_lost_stolen", "suspected_fraud"}


def _template_draft(snippet: str, kb_key: str) -> str:
    """Template-based draft (no LLM)."""
    intro = "Thank you for contacting us. Based on our policy"
    body = snippet[:500].strip()
    closing = "If you have further questions, please reply or call us."
    return f"{intro} [kb: {kb_key}]:\n\n{body}\n\n{closing}"


def draft_from_policy(
    classification: ClassificationResult,
    kb: dict[str, str],
    use_llm: bool = False,
    redacted_message: Optional[str] = None,
) -> tuple[str, bool]:
    """
    Generate draft response for supported intents. Returns (response_text, used_fallback).
    use_llm=False: use template only. use_llm=True: call GPT-4o-mini when OPENAI_API_KEY is set and redacted_message provided; else template.
    """
    intent = classification.intent
    confidence = classification.confidence or 0.0
    used_fallback = False

    if not _intent_eligible_for_draft(intent):
        return (
            "Thank you for your message. A colleague will respond shortly. [Escalated: intent not in draft scope]",
            True,
        )

    snippet = get_snippet(kb, intent)
    if not snippet:
        return (
            "We are sorry, we need to escalate your request. An agent will contact you shortly. [Escalated: no policy snippet]",
            True,
        )
    kb_key = (
        "suspected_fraud"
        if intent in ("fraud", "suspected_fraud")
        else "card_lost_stolen"
    )
    template_text = _template_draft(snippet, kb_key)

    if confidence < CONFIDENCE_THRESHOLD:
        return (template_text + " [No-LLM fallback]", True)
    if not use_llm or not is_available() or not (redacted_message or "").strip():
        return (template_text + " [No-LLM fallback]", True)
    # Call LLM (e.g. GPT-4o-mini)
    llm_text = generate_draft(
        customer_message=redacted_message.strip(),
        policy_snippet=snippet,
        kb_key=kb_key,
    )
    if llm_text:
        return (llm_text, False)
    return (template_text + " [No-LLM fallback]", True)
