.PHONY: help install train run test eval

# Default data path (override with DATA_DIR=...)
DATA_DIR ?= assignment/data

# Default target: show all run-related commands
help:
	@echo "Intelligent message routing – Makefile targets"
	@echo ""
	@echo "  make install   – Install dependencies (uv sync). Run first."
	@echo "  make train    – Train MTL model; writes models/mtl_model.joblib. Run once before using MTL."
	@echo "  make run      – Run pipeline (redact → classify → draft → check). Uses MTL if model exists."
	@echo "  make test     – Run unit tests (pytest)."
	@echo "  make eval     – Run evaluation (classification metrics + draft checks). DATA_DIR=$(DATA_DIR)"
	@echo ""
	@echo "Environment: Put OPENAI_API_KEY and USE_LLM=1 in .env to enable LLM draft (see README)."

install:
	uv sync

train:
	uv run python -m app.train_mtl --data-dir $(DATA_DIR)

run:
	uv run python -m app

test:
	uv run pytest tests -v

eval:
	uv run python -m app.eval --data-dir $(DATA_DIR)
