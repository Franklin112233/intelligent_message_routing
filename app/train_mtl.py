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
    p.add_argument(
        "--train-ratio",
        type=float,
        default=1.0,
        metavar="R",
        help="Use R of data for training (0 < R <= 1). 0.8 = 80%% train / 20%% holdout (default: 1.0)",
    )
    args = p.parse_args()
    messages_path = args.data_dir / "messages.csv"
    train(
        messages_path,
        model_path=args.model_path,
        train_ratio=args.train_ratio,
    )
    out = args.model_path or Path("models/mtl_model.joblib")
    print(f"Model saved to {out}")


if __name__ == "__main__":
    main()
