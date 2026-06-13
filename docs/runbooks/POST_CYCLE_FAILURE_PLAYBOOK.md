# Post-Cycle Failure Playbook

This runbook defines the six mandatory post-cycle failure modes and exact recovery actions. Do not use vague directives. Every recovery path must produce explicit evidence and leave an audit trail.

## A) Missing Source Prompt

Failure: `PM_Pack/01_pm_instructions/POST_CYCLE_PM_REVIEW_v4.md` is missing.

Recovery:

```powershell
Set-Location C:\Fiverr\Fiverr
git log --all -- PM_Pack/01_pm_instructions/POST_CYCLE_PM_REVIEW_v4.md
git checkout <SHA> -- PM_Pack/01_pm_instructions/POST_CYCLE_PM_REVIEW_v4.md
```

Validation: file exists and is readable. Never skip this prompt.

## B) Model Unverified

Failure: Claude Sonnet 4.6 subscription state not confirmed.

Recovery:

1. Run subscription preflight.
2. Re-run `verify_subscription_preflight()`.
3. Confirm API billing is not used.

Validation: model state shows verified subscription path and freshness window.

## C) Agent Reports Missing

Failure: one or more reports for A/B/E/C/F/D absent.

Recovery:

1. Identify missing report file(s).
2. Dispatch docs-only repair prompt for missing agent.
3. Wait for report creation before official post-cycle review.

Validation: all required agent reports present and parseable.

## D) Score Cap Violation

Failure: Score 2 exceeds Score 1 or violates TierD-2 cap logic.

Recovery:

1. Open `PM_Pack/PRODUCTION_READINESS_SCORECARD.md`.
2. Re-apply cap logic based on TierD-2 and gate evidence.
3. Record discrepancy and correction in cycle report.

Validation: Score 2 <= Score 1 and cap rationale documented.

## E) Prompt Quality Failure

Failure: next cycle prompts fail validation.

Recovery:

```powershell
Set-Location C:\Fiverr\Fiverr
python automation/ai_cycle_controller.py plan-cycle --live --cycle <NNN>
python automation/ai_cycle_controller.py validate-prompts --cycle <NNN>
```

Review `PLANNING_INCOMPLETE_CYCLE_NNN.md`; usually insufficient Jira story volume. Add stories, then re-run planning and validation.

Validation: all generated prompts pass validation, with no unsafe dispatch.

## F) PMPack Contradiction

Failure: `pm-pack-audit` returns BLOCKED or contradiction warnings.

Recovery:

```powershell
Set-Location C:\Fiverr\Fiverr
python automation/ai_cycle_controller.py pm-pack-audit
```

Update stale files to match `HYDRATION_HEADER.md` authority, then rerun audit until PASS.

Validation: audit PASS and no unresolved contradiction.

## Completion Criteria

Post-cycle review is restored only when all six checks either pass directly or have documented, completed recovery actions. Every failure handling action must be timestamped in the cycle report to preserve traceability.

## Evidence Package Requirements

For any recovered failure mode, collect and retain:

1. failing command output
2. remediation command output
3. affected file list
4. validation rerun output
5. final state confirmation

Example evidence commands:

```powershell
Set-Location C:\Fiverr\Fiverr
git status --short
python automation/ai_cycle_controller.py pm-pack-audit
python automation/ai_cycle_controller.py brain-check
```

## Failure Interaction Rules

Some failures can appear together. Use this order:

1. resolve model verification first
2. restore missing source prompts/reports
3. fix PMPack contradictions
4. rerun planning validation
5. rerun post-cycle review

Do not attempt final closure while any upstream blocker remains unresolved.

## Quality Bar for Recovery Notes

Recovery notes must explain:

- what failed
- why it failed
- exactly what command/action fixed it
- what objective checks confirmed success

Statements such as "fixed issue" or "resolved manually" are insufficient. Recovery text must be concrete enough for another operator to replay the same fix without additional context.

## Handover Requirement

If recovery is performed by one operator and reviewed by another, include a handover block in the cycle report listing unresolved assumptions, follow-up checks, and confidence level. This prevents hidden state from leaking into the next cycle.

