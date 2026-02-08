"""Main pipeline: ingress → redact → classify → draft (supported intents) → guardrails/eval."""

import os
from pathlib import Path

from app.config import DEFAULT_DATA_DIR
from app.redact import load_patterns, redact, redact_with_config
from app.classify import classify
from app.kb import load_kb
from app.draft import draft_from_policy
from app.guardrails import run_draft_checks
from app.mtl import DEFAULT_MODEL_DIR, MODEL_FILE


def run_pipeline(
    messages_path: Path,
    data_dir: Path,
    limit: int | None = 5,
) -> None:
    """
    Wire pipeline: redaction runs before any non-local model or external service.
    Ingress (messages.csv) → redact → classify → draft (for supported intents) → check.
    """
    import pandas as pd

    if not messages_path.exists():
        print("messages.csv not found at", messages_path)
        return
    df = pd.read_csv(messages_path)
    if limit:
        df = df.head(limit)
    pii_path = data_dir / "pii_patterns.yaml"
    kb = load_kb(data_dir / "kb")
    patterns = load_patterns(pii_path)
    model_path = Path(__file__).resolve().parent.parent / DEFAULT_MODEL_DIR / MODEL_FILE
    backend = "mtl" if model_path.exists() else "stub"
    use_llm = os.environ.get("USE_LLM", "").strip().lower() in ("1", "true", "yes")
    print(
        f"Backend: {backend}. Draft: {'LLM (GPT-4o-mini)' if use_llm else 'template'}. "
        f"Processed {len(df)} messages (redact → classify → draft → check)\n"
    )
    for _, row in df.iterrows():
        msg_id = row.get("message_id", "")
        text = str(row.get("text", ""))
        # 2.3: Redaction runs before any call to non-local model or external service
        redacted = redact(text, patterns)
        res = classify(
            redacted,
            messages_path,
            message_id=str(msg_id),
            backend=backend,
            model_path=model_path if backend == "mtl" else None,
        )
        draft, used_fallback = draft_from_policy(
            res, kb, use_llm=use_llm, redacted_message=redacted
        )
        ok, failures = run_draft_checks(draft)
        status = "OK" if ok else f"FAIL:{','.join(failures)}"
        print(
            f"  {msg_id} intent={res.intent} queue={res.suggested_queue} fallback={used_fallback} checks={status}"
        )


def main() -> None:
    base = Path(__file__).resolve().parent.parent
    data_dir = base / "assignment" / "data"
    messages_path = data_dir / "messages.csv"
    print("Intelligent message routing")
    print(f"Data directory: {data_dir}\n")
    run_pipeline(messages_path, data_dir, limit=5)


if __name__ == "__main__":
    main()
