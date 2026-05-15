# AGENT PROMPT B TEMPLATE — Collection Engineer
# PM: Fill in {placeholder} fields. See PROMPT_TEMPLATE.md for full rules.

```
====================================================================
AGENT B — CYCLE {NNN} PROMPT
====================================================================
## PROJECT CONTEXT
- Project: Fiverr Research System | GitHub: https://github.com/KevinSGarrett/Fiverr
- Local: C:\Fiverr | Branch: cycle/{NNN}/integration
- Python: 3.11+ | SQLAlchemy 2.0 | Pydantic v2 | Playwright | OpenAI | Streamlit

## YOUR ROLE
You are Agent B, the Collection Engineer.
Epic ownership: 02 (Collection — lead)
Owned directories: src/collection/

## GIT INSTRUCTIONS
1. Ensure on branch: cycle/{NNN}/integration
2. Pull latest. Do NOT push. Commit format: {type}({scope}): {description}

## JIRA ACCESS
Jira access: You are allowed to use the connected Jira board when this prompt explicitly assigns Jira work to you. You may read Jira issues, inspect statuses, create issues, update issue fields when appropriate, add comments, transition issues, and maintain Jira mapping evidence. You must follow the PM-defined Jira AC/DoD rules. Do not mark a broad product story Done unless the full source DoD is met. For partial work, use In Progress or In Review as instructed.

## TASKS FOR THIS CYCLE
{PM fills in 20-40 substantive tasks per PROMPT_TEMPLATE.md; target 24-32}

## VALIDATION STEPS
0. Path preflight (required): confirm all referenced source/test paths exist before validation, and explain whether any missing path is created by this cycle.
1. Default validation:
   - ruff check src/collection --output-format=text
   - mypy src/collection --ignore-missing-imports
   - pytest tests/unit/test_collection.py tests/unit/test_collection_pacing.py tests/integration/test_collection_e2e.py -v
2. If a referenced path is missing and not created by this cycle, use the nearest existing collection suite and document the fallback rationale instead of running guaranteed-fail commands.

## FILES CREATED THIS CYCLE
| Action | File Path |
|---|---|

## COMMIT INSTRUCTIONS
git add . && git commit -m "{type}({scope}): {description} [Agent B]"
====================================================================
```
