# PROMPT RULES — Six-Lane Governance Baseline

Version: Cycle 079 governance alignment

---

## Minimum Requirements Per Cursor-Agent Prompt

| Metric | Minimum | Target | Maximum |
|---|---:|---:|---:|
| Total word count per agent prompt | 6,000 | 8,000-12,000 | No hard cap if organized |
| Substantive tasks per prompt | 55 | 55-70 | No hard cap with quality |
| Words per substantive task | 100 | 250-500 | No hard cap |
| Tests/validation expectations per task | 1 | 2-4 | As needed |
| Jira keys per task | 1 | 1-3 | As needed |
| AC/DoD references per task | 1 | 1-3 | As needed |
| Files listed | Every file touched | Every file touched | Required |

## TASK FLOOR REQUIREMENT

Every agent prompt MUST contain a minimum of 55 substantive, numbered tasks.
Tasks must be individually actionable.
`prompt_validator.py` enforces this floor at runtime.
Prompts with fewer than 55 tasks are REJECTED.

## Binding Prompt-Quality Rules

A prompt is rejected if:

1. it contains fewer than 55 substantive tasks;
2. it fails to include exact Jira keys;
3. it fails to embed exact AC/DoD bullets in each task;
4. it omits file ownership boundaries;
5. it omits explicit validation commands;
6. it omits final report requirements and path;
7. it lacks stop conditions;
8. it relies on vague instructions such as "continue" or "as needed";
9. it plans from Git/PR deltas before Jira board issue selection.

## Required Structure for Every Agent Prompt

1. Mission.
2. Branch and repo context.
3. Model policy statement.
4. File ownership boundaries.
5. Non-overlap constraints.
6. 55+ numbered substantive tasks.
7. Validation commands.
8. Final report path.
9. Stop conditions.
10. Done criteria.
