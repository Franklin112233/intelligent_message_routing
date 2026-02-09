"""Config and data paths."""

from pathlib import Path

# Project root (parent of app/)
ROOT = Path(__file__).resolve().parent.parent
DEFAULT_DATA_DIR = ROOT / "assignment" / "data"
