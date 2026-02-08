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
