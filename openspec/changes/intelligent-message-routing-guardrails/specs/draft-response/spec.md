# Draft response

## ADDED Requirements

### Requirement: Policy-grounded draft
For at least two intents (e.g. card lost/stolen, suspected fraud), the system SHALL generate a first-draft response grounded in `kb/` policy snippets, with citations. Draft MAY be produced by template or by LLM (e.g. GPT-4o-mini in app/llm.py when USE_LLM=1 and OPENAI_API_KEY set); both paths SHALL output real text with [kb: ...] citation.
#### Scenario: Policy-grounded draft
Given a message of a supported intent and relevant kb snippets, when draft is generated, then the response cites policy and is grounded in snippets.

### Requirement: Fallback and escalation
The system SHALL provide a no-LLM fallback and confidence-based escalation.
#### Scenario: Fallback and escalation
Given low confidence or LLM unavailable, then a no-LLM fallback response or escalation path is used.
