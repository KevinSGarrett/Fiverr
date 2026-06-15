# ADR 024: Cost Governance for Provider Routing

## Status
Accepted

## Context
Provider Router V7 can route tasks across subscription and API-backed providers. Subscription providers
(`cursorcli`, `claude_subscription`) do not incur per-request marginal billing in this runtime, while
`openai_api` is usage-metered and can create unbounded spend without controls.

## Decision
Introduce `automation/cost_guard.py` as the deterministic budget gate used before metered calls.

- Hard limits for `openai_api`:
  - Daily hard limit: **$10**
  - Monthly hard limit: **$150**
- Soft warning threshold:
  - Daily soft warn: **$5**
- Metering source of truth:
  - `automation/provider_usage_ledger.py` daily and lifetime ledger entries

When a projected call would breach daily or monthly hard limits, `CostGuard.check_budget()` returns
`HARDBLOCK`. Execution must stop and require human intervention before any additional metered calls.

## Rationale
- Keeps API usage within explicit cycle-level budget constraints.
- Prevents silent runaway spend from repeated retries or large prompt payloads.
- Preserves deterministic behavior by applying a simple preflight decision gate.
- Avoids false budget pressure on subscription providers that are not billed per API request.

## Consequences
- `openai_api` traffic is strictly budget-governed and can be blocked during a cycle.
- Subscription providers remain outside hard budget enforcement by design.
- Operations must monitor and reset budgets as calendar boundaries change.
- Human override or policy update is required after hard-cap events.
