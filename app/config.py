"""Config and data paths."""

from pathlib import Path

# Project root (parent of app/)
ROOT = Path(__file__).resolve().parent.parent
DEFAULT_DATA_DIR = ROOT / "assignment" / "data"

MESSAGES_CSV = "messages.csv"
PII_PATTERNS_YAML = "pii_patterns.yaml"
KB_DIR = "kb"
