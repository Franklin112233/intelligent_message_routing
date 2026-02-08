"""Guardrails: at least one automated check on draft output (citation, PII mask, or safety)."""

import re


def check_draft_citation_present(draft: str) -> bool:
    """Return True if draft contains a policy citation (e.g. [kb: ...])."""
    return bool(re.search(r"\[kb:\s*\w+\]", draft, re.IGNORECASE))


def check_draft_no_raw_pii(draft: str) -> bool:
    """Return True if draft does not contain obvious raw PII (simplified: no 16-digit card run)."""
    # Simple heuristic: 16 consecutive digits or 4 groups of 4
    if re.search(r"\d{16}", draft):
        return False
    if re.search(r"\d{4}\s*\d{4}\s*\d{4}\s*\d{4}", draft):
        return False
    return True


def run_draft_checks(draft: str) -> tuple[bool, list[str]]:
    """
    Run at least one automated check. Returns (all_passed, list of failure reasons).
    """
    failures = []
    if not check_draft_citation_present(draft):
        failures.append("citation_missing")
    if not check_draft_no_raw_pii(draft):
        failures.append("possible_pii_in_draft")
    return (len(failures) == 0, failures)
