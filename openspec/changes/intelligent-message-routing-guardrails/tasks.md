## 1. Setup

- [x] 1.1 Create project structure (e.g. `src/` or `app/`, `tests/`, assignment data paths)
- [x] 1.2 Add UV with project.toml with minimal dependencies (and versions)
- [x] 1.3 Add single entrypoint (e.g. `python -m app.run` or runnable notebook)
- [x] 1.4 Add makefile for commands run and add README with setup

## 2. PII redaction

- [x] 2.1 Load PII patterns from `pii_patterns.yaml` (or equivalent config)
- [x] 2.2 Implement redaction function: apply patterns, replace matches with placeholder (e.g. `[REDACTED]`)
- [x] 2.3 Ensure redaction runs before any call to non-local model or external service in pipeline
- [x] 2.4 Add unit test: fixture with known PII → assert output has no raw PII

## 3. Intent classification

- [x] 3.1 Define classifier interface: input redacted text → output intent, suggested_queue, optional confidence
- [x] 3.2 Implement one backend (MTL, LLM few-shot, or stub that reads from labels/file)
- [x] 3.3 Document in README when to prefer MTL vs LLM vs hybrid (per proposal comparison)
- [x] 3.4 Implement MTL in app/mtl.py (train + predict, real script); wire in classify.py and run/eval

## 4. Knowledge base (policy store)

- [x] 4.1 Load all `kb/*.md` into in-memory dict keyed by intent or filename
- [x] 4.2 Expose lookup: given intent, return relevant policy snippet(s) for draft grounding

## 5. Draft response

- [x] 5.1 For ≥2 intents (e.g. card lost/stolen, suspected fraud), generate draft using kb snippets and citations (e.g. `[kb: card_lost_stolen]`)
- [x] 5.2 Implement no-LLM fallback (e.g. predefined template or “escalate to agent”)
- [x] 5.3 Add confidence-based escalation (e.g. below threshold or LLM unavailable → fallback or escalate)
- [x] 5.4 Replace draft LLM placeholder with real template-based output (no placeholder text)
- [x] 5.5 Optional LLM draft: integrate GPT-4o-mini (app/llm.py), OPENAI_API_KEY from env or .env, USE_LLM=1 to enable; template fallback when unavailable

## 6. Guardrails and draft checks

- [x] 6.1 Implement at least one automated check on draft output (PII masking present, OR policy citation present, OR basic safety rule)
- [x] 6.2 Wire check into pipeline; escalate or flag when check fails (per design)

## 7. Evaluation

- [x] 7.1 Compute basic classification metrics (e.g. precision/recall) on labelled messages
- [x] 7.2 Redaction unit tests (covered in 2.4; ensure they run in test suite)
- [x] 7.3 At least one automated test/check for draft responses (masking, citation, or safety) in eval path

## 8. Pipeline and entrypoint

- [x] 8.1 Wire pipeline: ingress (e.g. read messages.csv) → redact → classify → draft (for supported intents) → logging/eval
- [x] 8.2 Command runner with makefile commands for run, test, and eval (and runs eval if applicable)

## 9. README and docs

- [x] 9.1 README: setup (install deps, data paths), how to run, what is implemented vs stubbed
- [x] 9.2 README: assumptions, security considerations, cost/latency notes for any LLM or external call
- [x] 9.3 README: trade-offs between ML and LLM, hybrid options, and when to prefer each
- [x] 9.4 README: explainability and risk documentation
- [x] 9.5 README: system architecture diagram with mermaid

