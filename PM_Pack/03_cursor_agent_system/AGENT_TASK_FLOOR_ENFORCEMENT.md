# AGENT TASK FLOOR ENFORCEMENT

## Canonical Floor
- Minimum tasks per agent prompt: **55**
- Applies to every cycle and every lane: `A, B, E, C, F, D`

## Enforcement Source
- Enforced by `automation/prompt_validator.py`
- Validation gate must run before dispatch

## Required Task Grammar
- Every task line must start with:
  - `### TASK NN — Description`

## Dispatch Rule
- No agent may receive a prompt with fewer than 55 tasks.
- If prompt validation fails, dispatch must stop with non-zero exit.
