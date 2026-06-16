# ADR 023: Provider Router Governance

## Status
Accepted — In Implementation

## Context
Provider selection and execution policy is centralized in `PM_Pack/automation/provider_policy.yml`.
Cycle 079 established governance-level policy artifacts and route ownership. Cycle 080 continues by
aligning runner-side state/config and preparing implementation modules.

## Decision
- Keep deterministic controller ownership for merge/jira transitions.
- Keep `advisory_only_provider_routing: true` through Stage 1.
- Require provider decision artifacts and usage ledger entries for provider actions.
- Keep Claude subscription lane blocked for direct implementation and repair work.

## Consequences
- Router and adapter implementations can proceed with stable policy contracts.
- Governance can validate provider dispatch intent before hard-routing is enabled.
- Stage 2 can flip advisory mode only after route validation and adapter health checks pass.

## Cycle 080 Implementation Status
- Wave A complete: `provider_policy.yml` route governance and runner config/state files are in place.
- Wave B/C in Cycle 080: Python modules and adapters are pending (`provider_router.py`, adapter classes).
- `advisory_only_provider_routing=true` remains active until Stage 2 validation is complete.

## Cycle 081 Update
- `advisory_confirm_mode=true` replaces `advisory_only_provider_routing=true` as the default governance posture in Cycle 081.
- `cursor_cli` can dispatch in advisory-confirm mode for implementation/repair/test/docs execution lanes.
- Claude subscription and OpenAI API routes still require explicit human confirmation (`ADVISORYCONFIRMREQUIRED`) before dispatch.
- This change advances the system toward Stage 2 real dispatch readiness while preserving strict review controls.
