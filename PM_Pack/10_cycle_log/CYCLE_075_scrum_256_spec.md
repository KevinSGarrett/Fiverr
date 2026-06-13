# CYCLE 075 EXECUTABLE SPEC - SCRUM-256

## Objective
SCRUM-256 establishes PR governance hardening for Cycle 077 by requiring explicit Jira key declaration in the PR template. The objective is to reduce merge risk caused by unscoped or partially scoped pull requests and to ensure reviewers can validate cycle intent quickly. This spec covers only template-level governance and does not change branch policy enforcement code.

## Component Boundaries
- In scope: `.github/pull_request_template.md` required Jira key field updates.
- In scope: reviewer checklist alignment with Cycle 077 scope keys.
- Out of scope: branch protection settings in GitHub UI.
- Out of scope: runtime code and test pipeline changes.

## Data Flow
1. Gather required Cycle 077 Jira keys from planning scope.
2. Update PR template with required Jira field and explicit key list.
3. Preserve existing sections (validation, no-main confirmation, merge gate).
4. Reviewer fills template and confirms listed keys are in scope.
5. Governance review checks template conformance before merge.

## Error Handling
- Template file path mismatch (case variance): update existing canonical file path in repo.
- Key list truncation: reject template update and regenerate complete key list.
- Duplicate key entry: normalize into unique ordered list.
- Missing required field marker: add mandatory checkbox/line in template.

## API Contract (Governance Interfaces)
```python
def inject_required_jira_field(template_text: str, required_keys: list[str]) -> str: ...
def normalize_key_list(keys: list[str]) -> list[str]: ...
def validate_template_has_required_keys(template_text: str, required_keys: list[str]) -> list[str]: ...
def assert_pr_template_sections_preserved(template_text: str) -> list[str]: ...
```

## Validation Strategy
- Presence check: template contains a "Required Jira Keys" field.
- Completeness check: all 20 keys are listed exactly once.
- Regression check: existing governance sections remain intact.
- Reviewer usability check: field format supports copy/paste from Jira.

## Required Tests
1. `test_scrum_256_pr_template_contains_required_jira_field`
2. `test_scrum_256_pr_template_contains_all_cycle_077_keys`
3. `test_scrum_256_preserves_existing_merge_and_validation_sections`
4. `test_scrum_256_key_list_is_unique_and_ordered`

## AC / DoD Mapping
| AC | Implementation Signal | DoD Evidence |
|---|---|---|
| AC-1: Required Jira field added | Template section exists | Updated PR template |
| AC-2: Full key list enforced | 20 keys present | Key validation result |
| AC-3: Existing governance retained | Legacy sections unchanged | Diff inspection |
| AC-4: Review ergonomics improved | Clear copyable format | Template text block |

## Architecture Decision and Tradeoff Notes
Decision: enforce key visibility in PR template instead of relying on PR title conventions. Tradeoff: slight author overhead, significantly improved review consistency. Decision: embed explicit key list for Cycle 077 rather than a generic phrase. Tradeoff: template needs cycle updates, but removes ambiguity for this governance window. Decision: keep template markdown-only and avoid custom PR bots. Tradeoff: less automation but zero integration risk and immediate maintainability.
