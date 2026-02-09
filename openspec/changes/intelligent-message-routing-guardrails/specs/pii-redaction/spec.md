# PII redaction

## ADDED Requirements

### Requirement: Redact before external call
The system SHALL redact sensitive tokens (account numbers, sort codes, phone/email, UK postcodes) before any call to a non-local model or service. Use configurable patterns (e.g. from `pii_patterns.yaml`).
#### Scenario: Redaction before external call
Given a message containing PII, when sending to an external or non-local service, then all configured PII patterns are redacted first.

### Requirement: Redaction test
The system SHALL prove redaction with a simple test.
#### Scenario: Redaction test
Given a test message with known PII, when redaction is applied, then the output contains no raw PII and tests pass.

**Implementation (code sync):** `app/redact.py` loads `pii_patterns.yaml`, applies regex/pattern replacement; pipeline calls redact before classify/draft. Tests in `tests/`.
