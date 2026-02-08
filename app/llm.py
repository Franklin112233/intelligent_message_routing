"""
LLM integration for draft generation (e.g. OpenAI GPT-4o-mini).

Loads OPENAI_API_KEY from environment or from .env in the project root.
On missing key or API error, callers should fall back to template.
"""

import os
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv

# Load .env from project root (parent of app/)
_env_path = Path(__file__).resolve().parent.parent / ".env"
load_dotenv(_env_path)

# Model used for draft generation (cost-effective, low latency)
DEFAULT_MODEL = "gpt-4o-mini"


def _client():
    """Lazy import to avoid import error when openai not installed."""
    from openai import OpenAI

    return OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))


def is_available() -> bool:
    """Return True if OPENAI_API_KEY is set and non-empty."""
    return bool(os.environ.get("OPENAI_API_KEY", "").strip())


def generate_draft(
    customer_message: str,
    policy_snippet: str,
    kb_key: str,
    model: str = DEFAULT_MODEL,
) -> Optional[str]:
    """
    Ask the LLM to generate a short, policy-grounded draft reply.

    - customer_message: redacted customer text (no PII).
    - policy_snippet: relevant kb content to ground the reply.
    - kb_key: e.g. suspected_fraud, card_lost_stolen (for citation).
    Returns generated text, or None on missing key / API error (caller should use template fallback).
    """
    if not is_available():
        return None
    system = (
        "You are a helpful banking assistant. Reply in 2–4 short sentences. "
        "Use ONLY the policy below; do not invent steps. "
        f"Include exactly one citation in this format: [kb: {kb_key}]"
    )
    user = (
        f"Policy:\n{policy_snippet}\n\n"
        f"Customer message:\n{customer_message}\n\n"
        "Draft reply (cite policy with [kb: ...]):"
    )
    try:
        client = _client()
        resp = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            max_tokens=300,
            temperature=0.3,
        )
        if resp.choices and resp.choices[0].message.content:
            return resp.choices[0].message.content.strip()
        return None
    except Exception:
        return None
