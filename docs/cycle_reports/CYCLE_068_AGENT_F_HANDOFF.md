# CYCLE 068 — AGENT F HANDOFF (EDGE-CASE TESTS)

Date: 2026-06-06  
Branch: `cycle/068/integration`

## F Scope

- Add edge-case test coverage for S7.4 only.
- Primary file: `tests/unit/test_gap_exploit_hypotheses.py`.
- F zone: tests + `CYCLE_068_AGENT_F.md` only.

## Required F Cases

- All-below-threshold => no candidates.
- All-above-threshold => all accepted under low gate.
- Empty `keyword_scores` => `[]`.
- Deduplication against `existing_hypotheses`.
- Confidence precision checks.
- `demand_weight + opportunity_weight` semantics (`~= 1.0`).
- Parametrized threshold coverage: at least 9 combinations.

## Regression Guardrails

- S7.2 and S7.3 behavior must remain unchanged.
- No `src/` changes by F unless explicitly re-scoped by user.
- Keep rationale strings and accepted/rejected audit behavior visible in tests.
