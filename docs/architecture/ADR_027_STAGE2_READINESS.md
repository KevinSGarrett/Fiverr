# ADR 027: Stage 2 Real Dispatch Readiness

## Status
Accepted

## Context
Cycle 081 introduces the Stage 2 gate where provider routing moves from advisory-only checks to an advisory-confirm loop that supports a real Cursor worker dispatch proof. Stage 2 must demonstrate that a full-size prompt run can complete and write `AGENT_COMPLETE` while preserving governance gates and rollback safety.

## Decision
- Stage 2 is defined as a single-agent real Cursor dispatch proof that delivers a full-size prompt and writes `AGENT_COMPLETE` to the cycle report artifact.
- Stage 2 dispatch may only proceed when all prerequisites are green:
  - PR `#98` is merged to `develop`.
  - `MODEL_GATE` is PASS.
  - `pm-pack-audit` is PASS.
  - `validate-prompts` is PASS for the active cycle.
  - `prompt_package_manifest.json` status is `READY`.
- Provider routing remains controlled by advisory-confirm governance: Cursor worker may execute, while Claude/OpenAI flows remain confirmation-gated.
- Post-dispatch success criteria include `ruff`, `mypy`, and required tests all green for the dispatched change set.

## Risks
- Cursor runtime can hang or stall under long prompt payloads.
- Wrong model/effort selection can invalidate model gate assumptions.
- Prompt size limits or malformed prompt payloads can fail dispatch before execution starts.

## Success Criteria
- `AGENT_COMPLETE` appears in the generated cycle report for the Stage 2 proof run.
- Provider decision artifact is recorded before dispatch.
- Validation gates (`ruff`, `mypy`, targeted tests) pass after the run.
- Controller state remains internally consistent through `brain-check` and `pm-pack-audit`.

## Rollback Plan
- Stop dispatch loop immediately on gate failure or blocked lifecycle status.
- Use safe git recovery (`git stash` or targeted `git revert`) to unwind local changes if needed.
- Do not use force-push for rollback under Stage 2 governance.
