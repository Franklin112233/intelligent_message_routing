.PHONY: help install train run run-redact run-predict run-draft test eval

# Default data path (override with DATA_DIR=...)
DATA_DIR ?= assignment/data
# Holdout: train on 80%%, evaluate on 20%% (use make train TRAIN_RATIO=0.8 then make eval TEST_RATIO=0.2)
TRAIN_RATIO ?= 1.0
TEST_RATIO ?= 0

# Default target: show all run-related commands
help:
	@echo "Intelligent message routing – Makefile targets"
	@echo ""
	@echo "  make install   – Install dependencies (uv sync). Run first."
	@echo "  make train    – Train MTL model; writes models/mtl_model.joblib. Run once before using MTL."
	@echo "                 Optional: TRAIN_RATIO=0.8 to use 80%% for training (holdout 20%% for eval)."
	@echo "  make run      – Run pipeline (redact → classify → draft → check). Uses MTL if model exists."
	@echo "                 Without MSG: prompts for one message (Enter = run 5 from CSV). With MSG: use that message."
	@echo "  make run-redact   – Redact only (input → redacted). MSG=\"...\" or prompt."
	@echo "  make run-predict  – Model prediction only (input → intent, queue, confidence). MSG=\"...\" or prompt."
	@echo "  make run-draft    – Draft only (input → draft response). MSG=\"...\" or prompt."
	@echo "  make test     – Run unit tests (pytest)."
	@echo "  make eval     – Run evaluation (classification metrics + draft checks). DATA_DIR=$(DATA_DIR)"
	@echo "                 Optional: TEST_RATIO=0.2 to evaluate on 20%% holdout (use after train TRAIN_RATIO=0.8)."
	@echo ""
	@echo "Environment: Put OPENAI_API_KEY and USE_LLM=1 in .env to enable LLM draft (see README)."

install:
	uv sync

train:
	uv run python -m app.train_mtl --data-dir $(DATA_DIR) --train-ratio $(TRAIN_RATIO)

# Optional: MSG="your message" to run on a single message instead of messages.csv
run:
	MSG="$(MSG)" uv run python -m app

# Single-step runs (one input → pretty CLI output). Pass MSG="..." or you will be prompted.
run-redact:
	MSG="$(MSG)" uv run python -m app redact

run-predict:
	MSG="$(MSG)" uv run python -m app predict

run-draft:
	MSG="$(MSG)" uv run python -m app draft

test:
	uv run pytest tests -v

eval:
	uv run python -m app.eval --data-dir $(DATA_DIR) --test-ratio $(TEST_RATIO)
