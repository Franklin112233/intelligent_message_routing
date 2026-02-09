"""PII redaction: load patterns from YAML, replace matches with placeholders."""

import re
from pathlib import Path
from typing import Any

import yaml


def load_patterns(path: Path) -> list[dict[str, Any]]:
    """Load PII patterns from pii_patterns.yaml. Returns list of {name, regex, mask}."""
    if not path.exists():
        return []
    with open(path, encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}
    patterns = data.get("patterns", [])
    out = []
    for p in patterns:
        if "regex" not in p or "mask" not in p:
            continue
        out.append(
            {
                **p,
                "regex": str(p["regex"]).strip(),
                "mask": str(p.get("mask", "[REDACTED]")).strip(),
            }
        )
    return out


def redact(text: str, patterns: list[dict[str, Any]]) -> str:
    """Apply each pattern: replace regex matches with pattern['mask']. Returns redacted text."""
    out = text
    for p in patterns:
        try:
            out = re.sub(p["regex"], p.get("mask", "[REDACTED]"), out)
        except re.error:
            continue
    return out


def redact_with_config(text: str, config_path: Path) -> str:
    """Load patterns from config_path and redact text. Convenience for pipeline."""
    patterns = load_patterns(config_path)
    return redact(text, patterns)
