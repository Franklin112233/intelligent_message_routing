# Evaluation and guardrails

## ADDED Requirements

### Requirement: Classification metrics
The system SHALL produce basic classification metrics.
#### Scenario: Classification metrics
Given labelled messages, when evaluation runs, then classification metrics (e.g. precision/recall) are produced.

### Requirement: Redaction unit tests
The system SHALL include redaction unit tests that prove PII is redacted.
#### Scenario: Redaction tests
Given redaction logic, when unit tests run, then they verify configured PII patterns are redacted.

### Requirement: Draft checks
The system SHALL run at least one automated check on draft responses (e.g. masking present, policy citation present, basic safety rule).
#### Scenario: Draft checks
Given a draft response, when checks run, then at least one of: PII masking present, policy citation present, or basic safety rule is verified.
