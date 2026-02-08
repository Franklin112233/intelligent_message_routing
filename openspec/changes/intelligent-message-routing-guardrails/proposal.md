## Why

Retail banks receive thousands of secure customer messages daily (fraud, disputes, limits, complaints). Slow or incorrect routing leads to poor customer experience, higher handling times, and missed economic-crime signals. We need a minimal, production-minded system to triage messages, redact PII before any non-local processing, route by intent, and generate policy-grounded draft responses with clear guardrails and fallbacks.

## What Changes

- **PII redaction**: Redact sensitive tokens (account numbers, sort codes, phone/email, UK postcodes) before any call to a non-local model or service; prove with a simple test.
- **Intent classification**: Classify messages and route to the correct queue (e.g. Fraud/Economic Crime, Disputes, General Banking, Credit/Risk), via **traditional ML (e.g. multi-task learning)**, LLM few-shot, or a **hybrid (LLM orchestrator calling MTL for prediction)**; document when to prefer each (latency, cost, accuracy, security).
- **Draft response (≥2 intents)**: For at least two intents (e.g. card lost/stolen, suspected fraud), generate a first-draft response grounded in `kb/` policy snippets, with citations; provide a no-LLM fallback and confidence-based escalation.
- **Evaluation and guardrails**: Basic classification metrics; redaction unit tests; at least one automated check on drafts (e.g. masking present, policy citation present, basic safety rule).
- **Explainability and risk**: Surface features (traditional ML) or rationales/quotes (LLM); state residual risks (hallucination, prompt-leak, data exfiltration, bias, abuse).

## Traditional ML (e.g. multi-task learning) vs LLM

We support both a **traditional ML** path (e.g. **multi-task learning**, MTL, for intent + queue + related labels from one model) and an **LLM** path (e.g. few-shot or zero-shot). Decision rationale:

| Dimension | Traditional ML (e.g. MTL) | LLM (few-shot / API) |
|-----------|---------------------------|------------------------|
| **Accuracy** | Strong on narrow, well-defined intents with enough labelled data; can overfit on small or imbalanced sets. MTL can help by sharing representations across related tasks (e.g. intent + queue + sensitivity). | Good zero/few-shot generalisation; can handle edge phrasing and new intents with minimal examples. Risk of over-interpreting or misclassifying under distribution shift. |
| **Latency** | Typically low (ms), runs on CPU or small GPU; predictable. | Higher and more variable (hundreds of ms–seconds for API calls); local/small models reduce but don’t remove this. |
| **Cost** | One-time train + cheap inference; no per-token API cost. | Per-token or per-request cost for managed APIs; local models trade cost for infra and ops. |
| **Security & sensitive data** | Model and data can stay fully on-prem; no raw text sent to third parties. PII can be redacted only for logging/eval, not for inference. | Sending text to external APIs creates data exfiltration and prompt-leak risk; **requires PII redaction (or full on-prem LLM)** before any external call. |
| **Handling sensitive info** | Inference on redacted or original text is possible entirely in-house; easier to enforce data residency and access controls. | Must redact before external calls; with local LLM, similar to traditional ML; with API, provider may log or train on inputs unless contractually excluded. |
| **Explainability** | Features, weights, and (for MTL) shared vs task-specific representations are inspectable; good for audits and dispute resolution. | Rationales and quotes are human-readable but can be wrong or fabricated; need guardrails and citation checks. |
| **When to prefer** | High volume, strict latency/cost/data-residency requirements, and sufficient labelled data. | Fast iteration, few labels, or need for open-ended drafting; acceptable to redact and/or use local LLM. |

For this project, **multi-task learning** is an allowed and recommended traditional ML option: a single model can predict intent, suggested queue, and (optionally) sensitivity or other auxiliary labels, sharing representation across tasks and often improving sample efficiency.

### Hybrid: LLM orchestrator + MTL for prediction

Yes — we can use **both** in one pipeline: an **LLM orchestrates** (redaction, security, tool calls, workflow) and **calls an ML model (MTL)** for classification. Roles:

- **LLM (orchestrator)**  
  - Runs first on raw or partially sanitised input (or after deterministic redaction).  
  - Decides when to call tools, applies security/safety checks, and may perform redaction (e.g. deciding what to mask or which PII patterns to apply) or delegate to a redaction service.  
  - Calls the **MTL model** as a tool: sends (redacted) text → receives intent/queue/scores.  
  - Uses MTL outputs to choose policy snippets, trigger draft response, or escalate.  
  - Handles tool-call semantics, retries, and fallbacks (e.g. if MTL is unavailable, fall back to LLM-based classification or a safe default).

- **MTL model (prediction)**  
  - Focuses only on **accuracy**: intent classification, suggested queue, and optional auxiliary outputs (e.g. sensitivity flag).  
  - Runs locally or in a controlled service; receives already-redacted or safe text from the orchestrator.  
  - Low latency, no per-token LLM cost for the classification step; explainability via model weights and shared representations.

This hybrid gives: **LLM for flexibility** (redaction policy, security rules, tool use, drafting) and **MTL for reliable, auditable prediction** where accuracy and cost matter. Design and specs should allow this pattern (LLM invokes MTL as a tool) alongside “LLM-only” and “MTL-only” options.

## Capabilities

### New Capabilities

- `pii-redaction`: Detect and redact PII using configurable patterns (e.g. from `pii_patterns.yaml`) before text is sent to external or non-local services; support tests that prove redaction works.
- `intent-classification`: Classify customer message intent and assign a suggested queue; support **traditional ML (e.g. MTL)**, LLM few-shot, or **hybrid (LLM orchestrator invokes MTL as a tool)**; document trade-offs (accuracy, latency, cost, security, sensitive-data handling, explainability) per the ML vs LLM comparison and hybrid option above.
- `draft-response`: Generate a first-draft reply for selected intents, grounded in policy snippets from `kb/`, with citations; include no-LLM fallback and confidence-based escalation.
- `evaluation-guardrails`: Classification metrics, redaction unit tests, and automated checks on draft responses (e.g. PII masking, policy citation, basic safety); support explainability and risk documentation.

### Modified Capabilities

- *(None — no existing specs in this repo.)*

## Impact

- **New codebase**: Runnable app or notebooks under this repo; README with setup, run, and what is implemented vs stubbed.
- **Data**: Ingress from `messages.csv` (or equivalent); all processing after PII redaction when using non-local models.
- **Dependencies**: Requirements file and one-command run entrypoint; prefer local/open models or mocked calls for the exercise; explicit cost and latency assumptions for any managed API.
- **Deliverables**: Code, README, and (out of scope for this proposal) slides for problem framing, architecture, guardrails, evaluation, and trade-offs.
