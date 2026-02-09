"""Evaluation: classification metrics, redaction tests, draft checks."""

from pathlib import Path
from typing import Optional

import pandas as pd
from sklearn.model_selection import train_test_split

from app.classify import classify, classify_stub_from_labels
from app.redact import load_patterns, redact, redact_with_config
from app.kb import load_kb
from app.draft import draft_from_policy
from app.guardrails import run_draft_checks
from app.config import DEFAULT_DATA_DIR
from app.mtl import DEFAULT_MODEL_DIR, MODEL_FILE, SPLIT_RANDOM_STATE


def classification_metrics(
    messages_path: Path,
    data_dir: Path,
    backend: Optional[str] = None,
    df: Optional[pd.DataFrame] = None,
) -> dict:
    """Compute accuracy for suggested_queue. backend: 'stub' (labels), 'mtl' (model), or None=auto.
    If df is provided, evaluate on that DataFrame instead of loading from messages_path.
    """
    if df is None:
        if not messages_path.exists():
            return {"error": "messages.csv not found", "precision": 0, "recall": 0}
        df = pd.read_csv(messages_path)
    if (
        "label" not in df.columns
        or "suggested_queue" not in df.columns
        or "message_id" not in df.columns
    ):
        return {"error": "missing columns", "precision": 0, "recall": 0}
    if backend is None:
        model_path = (
            Path(__file__).resolve().parent.parent / DEFAULT_MODEL_DIR / MODEL_FILE
        )
        backend = "mtl" if model_path.exists() else "stub"
    model_path = (
        Path(__file__).resolve().parent.parent / DEFAULT_MODEL_DIR / MODEL_FILE
        if backend == "mtl"
        else None
    )
    correct = 0
    total = len(df)
    for _, row in df.iterrows():
        mid = row.get("message_id")
        text = str(row.get("text", ""))
        redacted = redact_with_config(text, data_dir / "pii_patterns.yaml")
        res = classify(
            redacted,
            messages_path,
            message_id=str(mid),
            backend=backend,
            model_path=model_path,
        )
        if res.suggested_queue == str(row["suggested_queue"]).strip():
            correct += 1
    acc = correct / total if total else 0
    return {
        "backend": backend,
        "accuracy": acc,
        "correct": correct,
        "total": total,
        "precision": acc,
        "recall": acc,
    }


def eval_draft_checks(data_dir: Path, limit: int = 20) -> dict:
    """Run draft checks on a sample of messages; return count passed/failed."""
    messages_path = data_dir / "messages.csv"
    kb_dir = data_dir / "kb"
    if not messages_path.exists():
        return {"error": "messages.csv not found", "passed": 0, "failed": 0}
    df = pd.read_csv(messages_path).head(limit)
    kb = load_kb(kb_dir)
    patterns = load_patterns(data_dir / "pii_patterns.yaml")
    passed = 0
    failed = 0
    for _, row in df.iterrows():
        text = str(row.get("text", ""))
        redacted = redact(text, patterns)
        res = classify_stub_from_labels(
            redacted, messages_path, str(row.get("message_id"))
        )
        draft, _ = draft_from_policy(res, kb, use_llm=False)
        ok, reasons = run_draft_checks(draft)
        if ok:
            passed += 1
        else:
            failed += 1
    return {"passed": passed, "failed": failed, "total": passed + failed}


def main(
    data_dir: Optional[Path] = None,
    test_ratio: float = 0.0,
) -> None:
    data_dir = data_dir or DEFAULT_DATA_DIR
    messages_path = data_dir / "messages.csv"
    print("Evaluation")
    print("=========")

    if test_ratio > 0 and test_ratio < 1:
        if not messages_path.exists():
            print("Classification: messages.csv not found")
        else:
            df = pd.read_csv(messages_path)
            if (
                "label" not in df.columns
                or "suggested_queue" not in df.columns
                or "message_id" not in df.columns
            ):
                print("Classification: missing columns in messages.csv")
            else:
                try:
                    train_df, test_df = train_test_split(
                        df,
                        test_size=test_ratio,
                        random_state=SPLIT_RANDOM_STATE,
                        stratify=df["label"],
                    )
                except ValueError:
                    train_df, test_df = train_test_split(
                        df,
                        test_size=test_ratio,
                        random_state=SPLIT_RANDOM_STATE,
                    )
                if test_ratio > 0.5:
                    print(
                        f"Note: test_ratio={test_ratio} means you're evaluating on {test_ratio:.0%} of data. "
                        "For 20%% holdout use TEST_RATIO=0.2."
                    )
                metrics = classification_metrics(
                    messages_path,
                    data_dir,
                    backend="mtl",
                    df=test_df,
                )
                metrics["eval_set"] = "holdout"
                metrics["train_size"] = len(train_df)
                metrics["test_size"] = len(test_df)
                print(
                    f"Classification (holdout: train n={len(train_df)}, test n={len(test_df)}, test_ratio={test_ratio}):",
                    metrics,
                )
    else:
        metrics = classification_metrics(messages_path, data_dir)
        print("Classification:", metrics)

    draft_res = eval_draft_checks(data_dir, limit=30)
    print("Draft checks (sample):", draft_res)


if __name__ == "__main__":
    import argparse

    p = argparse.ArgumentParser()
    p.add_argument("--data-dir", type=Path, default=DEFAULT_DATA_DIR)
    p.add_argument(
        "--test-ratio",
        type=float,
        default=0.0,
        metavar="R",
        help="Evaluate on R holdout (0 < R < 1). Use 0.2 with train-ratio 0.8 (default: 0)",
    )
    args = p.parse_args()
    main(args.data_dir, test_ratio=args.test_ratio)
