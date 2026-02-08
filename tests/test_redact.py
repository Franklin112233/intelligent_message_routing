"""Unit tests for PII redaction."""

import pytest
from pathlib import Path

from app.redact import load_patterns, redact, redact_with_config

# Use project data path
DATA_DIR = Path(__file__).resolve().parent.parent / "assignment" / "data"
PII_YAML = DATA_DIR / "pii_patterns.yaml"


def test_redact_with_inline_patterns():
    """Redact using inline patterns (no YAML): fixture with known PII → no raw PII in output."""
    patterns = [
        {"regex": r"\d{4}[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{4}", "mask": "[CARD]"},
        {"regex": r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+", "mask": "[EMAIL]"},
    ]
    text = "My card is 4791-5741-2307-4814 and email is joe@example.com."
    out = redact(text, patterns)
    assert "4791" not in out and "4814" not in out
    assert "joe@example.com" not in out
    assert "[CARD]" in out
    assert "[EMAIL]" in out


def test_redact_removes_known_pii():
    """Fixture with known PII → output contains no raw PII (placeholders only)."""
    patterns = load_patterns(PII_YAML)
    assert len(patterns) >= 1, "Need at least one pattern from pii_patterns.yaml"

    text = "My card is 4791 5741 2307 4814 and email is joe@example.com. Sort code 12-34-56."
    out = redact(text, patterns)
    assert "4791" not in out and "4814" not in out
    assert "joe@example.com" not in out
    assert "12-34-56" not in out
    # Should contain mask placeholders
    assert "[CARD]" in out or "[EMAIL]" in out or "[SC]" in out or "[REDACTED]" in out


def test_redact_with_config():
    """redact_with_config loads from file and redacts."""
    if not PII_YAML.exists():
        pytest.skip("assignment/data/pii_patterns.yaml not found")
    text = "Contact me at alice@test.co.uk"
    out = redact_with_config(text, PII_YAML)
    assert "alice@test.co.uk" not in out
    assert "[EMAIL]" in out or "[REDACTED]" in out


def test_load_patterns_returns_list():
    """load_patterns returns a list of pattern dicts with regex and mask."""
    if not PII_YAML.exists():
        pytest.skip("assignment/data/pii_patterns.yaml not found")
    patterns = load_patterns(PII_YAML)
    for p in patterns:
        assert "regex" in p
        assert "mask" in p
