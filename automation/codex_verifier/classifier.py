"""
classifier.py -- Item classification heuristics.

ICV-CLASS-1..5: Classifies unmet checklist items as
FIXABLE_IN_SCOPE / OUT_OF_SCOPE / BLOCKED_EXTERNAL / NON_ISSUE / AMBIGUOUS.
"""
from __future__ import annotations

from automation.codex_verifier.schemas import (
    ChecklistItem,
    ChecklistStatus,
    ItemClassification,
)

# Patterns that indicate an item is NOT fixable by the agent in its lane
_OUT_OF_SCOPE_SIGNALS = (
    "secret", "token", "key", "credential", "password",
    "merge", "push", "deploy", "production",
    "permission", "access", "admin",
)

_BLOCKED_EXTERNAL_SIGNALS = (
    "ci", "github action", "pipeline", "codecov",
    "jira transition", "third-party", "external api",
)

_NON_ISSUE_SIGNALS = (
    "informational", "note:", "see ", "reference",
)


def classify_item(item: ChecklistItem, agent_lanes: list[str] | None = None) -> ChecklistItem:
    """
    Classify a checklist item based on heuristics.
    Returns a new item with classification set (never modifies in place).
    """
    item = ChecklistItem(**vars(item))

    if item.status == ChecklistStatus.SATISFIED:
        return item  # already satisfied — no classification needed

    desc_lower = item.description.lower()
    evidence_lower = (item.evidence or "").lower()
    combined = desc_lower + " " + evidence_lower

    # Out-of-scope: requires secrets/permissions/merge authority
    if any(sig in combined for sig in _OUT_OF_SCOPE_SIGNALS):
        item.classification = ItemClassification.OUT_OF_SCOPE
        return item

    # Blocked external: depends on CI, Jira, or external service
    if any(sig in combined for sig in _BLOCKED_EXTERNAL_SIGNALS):
        item.classification = ItemClassification.BLOCKED_EXTERNAL
        return item

    # Non-issue: informational/reference items
    if any(sig in combined for sig in _NON_ISSUE_SIGNALS):
        item.classification = ItemClassification.NON_ISSUE
        return item

    # File/command items that ARE in the agent's lane -> fixable
    if item.id.startswith("VCMD-") or item.id.startswith("FILE-"):
        item.classification = ItemClassification.FIXABLE_IN_SCOPE
        return item

    # AC/DOD items that aren't satisfied -> potentially fixable if evidence points to missing work
    if item.id.startswith(("AC-", "DOD-", "TASK-")) and item.status != ChecklistStatus.UNVERIFIABLE:
        item.classification = ItemClassification.FIXABLE_IN_SCOPE
        return item

    # Default: ambiguous (LLM will further classify)
    item.classification = ItemClassification.AMBIGUOUS
    return item


def classify_all(
    items: list[ChecklistItem], agent_lanes: list[str] | None = None
) -> list[ChecklistItem]:
    return [classify_item(i, agent_lanes) for i in items]
