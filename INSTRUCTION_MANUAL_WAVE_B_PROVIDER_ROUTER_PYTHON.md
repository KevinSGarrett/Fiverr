# INSTRUCTION MANUAL — WAVE B PROVIDER ROUTER PYTHON

## Purpose
This manual defines the Provider Router V7 Wave-B backend module contracts used by Agent B:

- `automation/provider_task_classifier.py`
- `automation/provider_health.py`
- `automation/provider_usage_ledger.py`
- `automation/cost_guard.py`
- `automation/schemas/*.schema.json` for provider artifacts

## Provider Task Classifier Structure

`TASK_CLASSES` must contain exactly nine canonical task types and each entry must include:

- `requires_file_edit: bool`
- `official_pm_review: bool`
- `risk_level: str`
- `primary_route: str`

### Canonical Task Types (9)

1. `implementation`
2. `repair`
3. `test_generation`
4. `docs_agent_work`
5. `prompt_lint`
6. `json_classification`
7. `official_post_cycle_review`
8. `merge_gate`
9. `jira_transition`

`classify(task_type)` must never raise and unknown values must route to `BLOCK`.

## Health and Budget Rules

- Health status is authoritative for route eligibility.
- Non-READY health states propagate to `BLOCKED`.
- Editing providers require `full_size_prompt_smoke == PASS`.
- OpenAI API is the only metered provider subject to hard budget caps.
- Hard caps: `$10` daily, `$150` monthly. Soft warning: `$5` daily.

## Prompt Factory Contracts

- Prompt contract schema enforces cycle/agent identity and Jira scope structure.
- Prompt renderer must output a complete prompt with at least 55 tasks.
- Prompt output must terminate with `END OF PROMPT`.
