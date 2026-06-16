# ADR 029: Restriction Removal for Autonomous Routing

## Status
Accepted ? Cycle 082

## Context
Routing restrictions (`advisory_confirm_mode` and related pauses) were introduced as early-development safeguards while controller, routing policy, and governance checks were maturing.

## Decision
Restrictions are removed for production autonomy in Cycle 082 because cycles 075-081 demonstrated stable controller behavior and policy gates, matching the intended manual Claude PM + PM_Pack + Cursor loop.

### Removed
- `advisory_confirm_mode`
- `advisory_only_provider_routing` dispatch blocking behavior
- human confirmation pauses in provider dispatch path

### Retained Hard Safety Limits
- no force-push to `main`
- no secret material in commits
- no billing account access through automation tasks

## Consequences
Dispatch path is now fully autonomous and evidence-driven. Safety remains enforced by deterministic governance and policy guardrails, not human confirmation prompts.
