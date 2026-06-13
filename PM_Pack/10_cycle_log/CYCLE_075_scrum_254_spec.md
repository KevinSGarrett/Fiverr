# CYCLE 075 EXECUTABLE SPEC - SCRUM-254

## Objective
SCRUM-254 governs stale-document registration for Cycle 077. The objective is to append newly observed stale-doc findings that materially affect execution quality, or explicitly document that no new stale findings were identified. The output must be actionable, scoped, and linked to remediation ownership so governance can be audited and closed.

## Component Boundaries
- In scope: `PM_Pack/STALE_DOCUMENT_REGISTER.md` append-only updates.
- In scope: stale finding entries related to Cycle 077 governance and planning.
- Out of scope: rewriting old stale findings unless correcting factual errors.
- Out of scope: runtime code analysis, CI pipeline internals, and feature implementation.

## Data Flow
1. Read stale document register current entries and status categories.
2. Compare current governance changes against existing stale items.
3. Identify net-new stale findings relevant to Cycle 077 scope.
4. Append findings with fields: file, stale statement, correct value, status, owner.
5. If no net-new findings exist, append explicit "none observed in Cycle 077 pass."

## Error Handling
- Missing stale register file: create with standard sections and metadata.
- Duplicate stale finding: update existing row status instead of adding duplicate.
- Unverifiable stale claim: mark as "needs evidence" and do not classify as critical.
- File path ambiguity: use repository-relative canonical path only.

## API Contract (Governance Interfaces)
```python
def detect_stale_doc_findings(scope_paths: list[str], baseline_register: str) -> list[dict]: ...
def append_stale_findings(register_path: str, findings: list[dict]) -> None: ...
def mark_no_new_findings(register_path: str, cycle_id: str) -> None: ...
def deduplicate_findings(findings: list[dict]) -> list[dict]: ...
```

## Validation Strategy
- Evidence check: every new finding must include a correct-value statement.
- Scope check: findings must be relevant to Cycle 077 governance changes.
- Duplication check: no repeated file+stale-statement pair.
- Explicitness check: if no new findings, explicit statement must exist.

## Required Tests
1. `test_scrum_254_appends_new_stale_findings_with_evidence`
2. `test_scrum_254_writes_explicit_none_when_no_new_findings`
3. `test_scrum_254_deduplicates_same_finding_signature`
4. `test_scrum_254_rejects_findings_without_correct_value`

## AC / DoD Mapping
| AC | Implementation Signal | DoD Evidence |
|---|---|---|
| AC-1: Stale register updated | File append committed | New Cycle 077 entry |
| AC-2: Findings are actionable | Correct value + owner noted | Table row fields |
| AC-3: No duplicate findings | Dedupe rules applied | Unique signatures |
| AC-4: None-case supported | Explicit none statement | Markdown note present |

## Architecture Decision and Tradeoff Notes
Decision: use append-only stale register updates to preserve traceability. Tradeoff: file length increases over time, but change history remains reviewer-visible without external tooling. Decision: classify only evidence-backed stale findings as critical. Tradeoff: may delay classification of uncertain items, but reduces false-positive governance debt. Decision: include owner field in stale entries. Tradeoff: additional maintenance burden, but improves closure accountability and cycle planning precision.
