"""
Multi-task learning for intent classification and suggested queue.

Shared representation (TF-IDF) with two heads: intent (label) and suggested_queue.
Trained on messages.csv; model persisted to disk for inference.
"""

from pathlib import Path
from typing import Optional

import joblib
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline

from app.classify import ClassificationResult

# Label and queue values from messages.csv
INTENTS = ("general", "fraud", "credit", "dispute")
QUEUES = (
    "General Banking",
    "Fraud/Economic Crime Prevention",
    "Credit/Risk",
    "Disputes/Chargebacks",
)

DEFAULT_MODEL_DIR = Path(__file__).resolve().parent.parent / "models"
MODEL_FILE = "mtl_model.joblib"


def _label_to_intent(label: str) -> str:
    s = str(label).strip().lower()
    return s if s in INTENTS else "general"


def _queue_normalize(q: str) -> str:
    s = str(q).strip()
    if s in QUEUES:
        return s
    for candidate in QUEUES:
        if candidate.lower() in s.lower():
            return candidate
    return "General Banking"


# Fixed seed for reproducible train/test split (must match eval.py)
SPLIT_RANDOM_STATE = 42


def train(
    messages_path: Path,
    model_path: Optional[Path] = None,
    train_ratio: float = 1.0,
) -> "MTLClassifier":
    """
    Train MTL model on messages.csv (text → intent, suggested_queue).
    If train_ratio < 1.0, use only that fraction for training (same split as eval --test-ratio).
    Saves pipeline to model_path.
    """
    if not messages_path.exists():
        raise FileNotFoundError(f"Messages file not found: {messages_path}")
    df = pd.read_csv(messages_path)
    if (
        "text" not in df.columns
        or "label" not in df.columns
        or "suggested_queue" not in df.columns
    ):
        raise ValueError("messages.csv must have columns: text, label, suggested_queue")

    if train_ratio < 1.0 and train_ratio > 0:
        try:
            train_df, _ = train_test_split(
                df,
                train_size=train_ratio,
                random_state=SPLIT_RANDOM_STATE,
                stratify=df["label"],
            )
        except ValueError:
            train_df, _ = train_test_split(
                df, train_size=train_ratio, random_state=SPLIT_RANDOM_STATE
            )
        df = train_df

    X = df["text"].astype(str).fillna("")
    y_intent = df["label"].apply(_label_to_intent)
    y_queue = df["suggested_queue"].apply(_queue_normalize)

    vectorizer = TfidfVectorizer(max_features=5000, ngram_range=(1, 2), min_df=2)
    X_vec = vectorizer.fit_transform(X)

    clf_intent = LogisticRegression(max_iter=500, random_state=42)
    clf_queue = LogisticRegression(max_iter=500, random_state=42)
    clf_intent.fit(X_vec, y_intent)
    clf_queue.fit(X_vec, y_queue)

    pipeline = {
        "vectorizer": vectorizer,
        "clf_intent": clf_intent,
        "clf_queue": clf_queue,
    }

    if model_path is None:
        model_path = DEFAULT_MODEL_DIR / MODEL_FILE
    model_path = Path(model_path)
    model_path.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(pipeline, model_path)

    return MTLClassifier(model_path=model_path, pipeline=pipeline)


class MTLClassifier:
    """Load and run MTL model: redacted text → intent, suggested_queue, confidence."""

    def __init__(
        self, model_path: Optional[Path] = None, pipeline: Optional[dict] = None
    ):
        if pipeline is not None:
            self._vectorizer = pipeline["vectorizer"]
            self._clf_intent = pipeline["clf_intent"]
            self._clf_queue = pipeline["clf_queue"]
            self._model_path = model_path
            return
        path = model_path or DEFAULT_MODEL_DIR / MODEL_FILE
        path = Path(path)
        if not path.exists():
            raise FileNotFoundError(
                f"Model not found: {path}. Run train() first or use backend='stub'."
            )
        data = joblib.load(path)
        self._vectorizer = data["vectorizer"]
        self._clf_intent = data["clf_intent"]
        self._clf_queue = data["clf_queue"]
        self._model_path = path

    def predict(self, redacted_text: str) -> ClassificationResult:
        """Predict intent and suggested_queue; confidence from max probability."""
        X = self._vectorizer.transform([redacted_text])
        intent = self._clf_intent.predict(X)[0]
        queue = self._clf_queue.predict(X)[0]
        prob_intent = self._clf_intent.predict_proba(X).max()
        prob_queue = self._clf_queue.predict_proba(X).max()
        confidence = float(min(prob_intent, prob_queue))
        return ClassificationResult(
            intent=str(intent),
            suggested_queue=str(queue),
            confidence=confidence,
        )


def load_or_train(
    messages_path: Path, model_path: Optional[Path] = None
) -> MTLClassifier:
    """Load existing model from model_path; if missing, train and save."""
    path = model_path or DEFAULT_MODEL_DIR / MODEL_FILE
    path = Path(path)
    if path.exists():
        return MTLClassifier(model_path=path)
    return train(messages_path, model_path=path)
