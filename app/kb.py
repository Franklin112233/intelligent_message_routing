"""Knowledge base: in-memory load of kb/*.md keyed by intent/filename."""

from pathlib import Path


def load_kb(kb_dir: Path) -> dict[str, str]:
    """Load all .md files in kb_dir into a dict: stem (e.g. card_lost_stolen) -> content."""
    if not kb_dir.exists() or not kb_dir.is_dir():
        return {}
    out: dict[str, str] = {}
    for f in kb_dir.iterdir():
        if f.suffix.lower() == ".md":
            out[f.stem] = f.read_text(encoding="utf-8").strip()
    return out


def get_snippet(kb: dict[str, str], intent: str) -> str:
    """Return policy snippet(s) for the given intent. Intent mapped to kb key (e.g. fraud -> suspected_fraud)."""
    # Normalize intent to kb filename stem
    mapping = {
        "fraud": "suspected_fraud",
        "card_lost": "card_lost_stolen",
        "card_lost_stolen": "card_lost_stolen",
        "lost_card": "card_lost_stolen",
        "stolen_card": "card_lost_stolen",
        "dispute": "dispute_timelines",
        "disputes": "dispute_timelines",
        "credit": "credit_limit_policy",
        "general": "general_servicing",
        "auth": "auth_safety",
    }
    key = mapping.get(intent.strip().lower(), intent.strip().lower().replace(" ", "_"))
    if key in kb:
        return kb[key]
    # Try direct key
    if intent.strip().lower() in kb:
        return kb[intent.strip().lower()]
    return ""
