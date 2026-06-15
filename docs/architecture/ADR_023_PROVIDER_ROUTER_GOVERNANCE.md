# ADR 023: Provider Router Governance

- Status: Accepted
- Date: 2026-06-15
- Owners: Cycle 079 Agent A governance lane

## Context

The system now operates as a six-lane architecture (A/B/E/C/F/D) with mixed deterministic and provider-assisted execution paths. Governance requires a single policy authority for provider routing, usage control, and fail-closed safety behavior.

Provider routing must remain auditable and bounded across:

- policy definitions in `PM_Pack/automation/provider_policy.yml`
- controller command checks in `automation/ai_cycle_controller.py`
- fail-closed consistency checks in `automation/pm_pack_consistency_audit.py`
- future runtime dispatching in `automation/provider_router.py` (CYCLE_079_AGENT_C)

## Decision

`PM_Pack/automation/provider_policy.yml` is the master governance authority for Provider Router V7.

All provider dispatch paths must enforce these five non-negotiable rules:

1. Controller owns git/jira/merge actions; providers cannot directly commit/push.
2. Every provider decision emits a decision artifact (`PM_Pack/automation/provider_decisions/`).
3. Every provider usage event writes a usage ledger entry (`C:\AI_Runner\reports\provider_usage\`).
4. Budget-capped providers must honor hard/soft limits before execution.
5. Malformed provider policy is fail-closed for audit flows when the policy file exists.

## Consequences

- Deterministic controller remains merge authority.
- Official PM review remains bound to subscription-only review provider policy.
- Advisory-only routing is enabled for Stage 1 rollout.
- Missing provider policy is a warning in Stage 1, while malformed policy is blocking.
- Decision artifacts and usage ledgers are required for post-cycle traceability.

## Implementation Phases

- Stage 1 (Cycle 079): advisory-only provider routing, policy + audit wiring.
- Stage 2-4: decision artifact/usage ledger hard enforcement.
- Stage 5-6: provider health and adapter routing operationalization.
- Stage 7: deferred secondary coder enablement gate.

## Path References

- `PM_Pack/automation/provider_policy.yml`
- `C:\AI_Runner\config\provider_router.yaml` (CYCLE_079_AGENT_C)
- `C:\AI_Runner\state\provider_health.json` (CYCLE_079_AGENT_C)
- `automation/provider_router.py` (CYCLE_079_AGENT_C)
