# CYCLE 069 — AGENT F HANDOFF (S7.5 EDGE-CASE TESTS)

Date: 2026-06-07  
Branch: `cycle/069/integration`

## F Scope

- Add edge-case test coverage for S7.5 only.
- Primary file: `tests/unit/test_trend_chase_hypotheses.py`.
- F zone: `tests/` + `docs/cycle_reports/CYCLE_069_AGENT_F.md` only.

## Required F Cases

- All candidates below trend thresholds -> no accepted candidates.
- All candidates above thresholds -> accepted up to `max_hypotheses`.
- Empty `keyword_trends` -> `[]`.
- Dedup against `existing_hypotheses`.
- Confidence precision checks with `0.55/0.45` weights.
- Inclusive boundary checks (`trend_score == 0.60`, `trend_velocity == 0.40`).
- High velocity semantic checks (accelerating trend behavior).

## Regression Guardrails

- S7.2/S7.3/S7.4 behavior unchanged.
- No `src/` edits by F unless re-scoped by user.
- Keep accepted/rejected rationale visibility in tests.

## Suggested Extra Cases

- Missing keys default to `0.0`.
- Missing keyword text rows safely skipped.
- Confidence clamped to `[0,1]` for extreme malformed values.
