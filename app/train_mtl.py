"""Train MTL model from messages.csv and save to models/mtl_model.joblib."""

import argparse
from pathlib import Path

from app.config import DEFAULT_DATA_DIR
from app.mtl import train


def main() -> None:
    p = argparse.ArgumentParser(description="Train MTL classifier on messages.csv")
    p.add_argument(
        "--data-dir",
        type=Path,
        default=DEFAULT_DATA_DIR,
        help="Directory containing messages.csv",
    )
    p.add_argument(
        "--model-path",
        type=Path,
        default=None,
        help="Output model path (default: models/mtl_model.joblib)",
    )
    args = p.parse_args()
    messages_path = args.data_dir / "messages.csv"
    train(messages_path, model_path=args.model_path)
    out = args.model_path or Path("models/mtl_model.joblib")
    print(f"Model saved to {out}")


if __name__ == "__main__":
    main()
