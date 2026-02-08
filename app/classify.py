"""Intent classification: interface and backends (stub, MTL, LLM pluggable)."""

from dataclasses import dataclass
from pathlib import Path
from typing import Optional

import pandas as pd


@dataclass
class ClassificationResult:
    """Output of classifier: intent, suggested_queue, optional confidence."""

    intent: str
    suggested_queue: str
    confidence: Optional[float] = None


def classify_stub_from_labels(
    text: str,
    messages_path: Path,
    message_id: Optional[str] = None,
) -> ClassificationResult:
    """
    Stub backend: look up by message_id in messages.csv and return label/suggested_queue.
    If message_id not provided or not found, return a default (general / General Banking).
    """
    if not messages_path.exists():
        return ClassificationResult(
            intent="general",
            suggested_queue="General Banking",
            confidence=0.0,
        )
    df = pd.read_csv(messages_path)
    if (
        message_id
        and "message_id" in df.columns
        and "label" in df.columns
        and "suggested_queue" in df.columns
    ):
        row = df[df["message_id"] == message_id]
        if not row.empty:
            return ClassificationResult(
                intent=str(row["label"].iloc[0]).strip().lower(),
                suggested_queue=str(row["suggested_queue"].iloc[0]).strip(),
                confidence=1.0,
            )
    return ClassificationResult(
        intent="general",
        suggested_queue="General Banking",
        confidence=0.0,
    )


def classify(
    redacted_text: str,
    messages_path: Path,
    message_id: Optional[str] = None,
    backend: str = "stub",
    model_path: Optional[Path] = None,
) -> ClassificationResult:
    """
    Classifier interface: input redacted text → output intent, suggested_queue, confidence.
    backend: "stub" (from labels), "mtl" (multi-task learning in app/mtl.py), "llm" (future).
    """
    if backend == "stub":
        return classify_stub_from_labels(redacted_text, messages_path, message_id)
    if backend == "mtl":
        try:
            from app.mtl import load_or_train

            clf = load_or_train(messages_path, model_path=model_path)
            return clf.predict(redacted_text)
        except Exception:
            return classify_stub_from_labels(redacted_text, messages_path, message_id)
    return classify_stub_from_labels(redacted_text, messages_path, message_id)
