# CYCLE 062 — AGENT E HANDOFF

Post-merge placeholder (do not replace until D finalizes squash): `[C062_SQUASH_SHA]`

## Mission and Zone (Strict)

- E job is docs-only validation reporting.
- E must commit only `docs/cycle_reports/CYCLE_062_AGENT_E.md`.
- E must never edit `src/`, `tests/`, `config.yaml`, migrations, or model files.

If implementation gaps are found in code, record them for B in the report; do not patch code.

## Live Validation Objective

Validate that DL-207 URL fix behavior yields real `search_result` rows in a throwaway DB run.

- Required throwaway DB: `data/cycle062_e2e.db`
- Prohibited DB: `data/cycle037_live.db`
- ScrapFly toggle behavior must remain compliant with controlled live-run process.

## ScrapFly Runtime Setup

- Load credentials through `.env` with `load_dotenv()`.
- Do not use direct `$env:` mutation as the primary method in report instructions.
- Keep all write activity in throwaway DB only.

## RSV Target Band

- Goal: LIVE band evidence
- Minimum requirement: at least one row in `result_set_validations` with `result_set_relevance_score >= 0.78`.
- If no live signal due to credit constraints, use exact fallback marker:
  - `[SEED — no live signal]`
- Never fabricate live evidence.

## TC-1 External Signal Validation

After any live attempt, verify `external_signals` includes:
- `raw_value`
- `relevance_score`
- `trend_direction`

Capture exact query outputs in E report.

## Parallel Execution Context

E runs in parallel with B. Pricing module changes may not be present when E executes.

- If `src/pricing` or migration_12 work is incomplete at E runtime, document as "parallel timing visibility gap".
- Do not wait indefinitely for B to finish.
- Do not alter B-owned files.

## Report Quality Rule

No pad lines allowed. Every line in E report must carry evidence, command output interpretation, or actionable finding.

Forbidden filler format includes:
- `floor-line-NNN: retained for floor compliance`

## Required E Report Sections

- Execution context (branch, db target, live/seed mode)
- ScrapFly readiness and budget status
- Live run evidence or explicit blocked fallback
- RSV table evidence with score band outcome
- TC-1 field integrity evidence
- Gaps for B (if any) with file/function specificity
- Final verdict: `LIVE`, `SEED`, or `BLOCKED`
