# Intent classification

## ADDED Requirements

### Requirement: Classify and route
The system SHALL classify customer message intent and assign a suggested queue (e.g. Fraud/Economic Crime, Disputes, General Banking, Credit/Risk). Support traditional ML (e.g. MTL implemented in app/mtl.py), LLM few-shot, or hybrid (LLM orchestrator invokes MTL as a tool).
#### Scenario: Classification output
Given a message, when the classifier runs, then intent and suggested_queue are returned.

### Requirement: Trade-off documentation
The system SHALL document when to prefer each approach (latency, cost, accuracy, security).
#### Scenario: Trade-off documentation
Given the system supports multiple backends, then README or design documents the trade-offs per the proposal comparison.

**Implementation (code sync):** `app/classify.py` (interface); `app/mtl.py` (MTL: shared TF-IDF + two LogisticRegression heads for intent and suggested_queue, trained on `messages.csv`, persisted to `models/mtl_model.joblib`). Pipeline uses MTL when model file exists, else stub (label lookup from data).
