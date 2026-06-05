# CYCLE 065 - AGENT F HANDOFF

Date: 2026-06-04  
Branch: `cycle/065/integration`

## F Scope

F zone is limited to `tests/` plus F report output.

## Coverage / Test Targets

- `src/pricing/pricing_export.py` coverage target: >= 85%
- Overall coverage gate target: >= 90%
- Add/verify >= 25 unit tests for pricing export behavior

## Required Edge Cases

- Empty database / no rows
- Partial pricing data across tables
- Unsupported export format request
- LLM pricing strategy absent in `recommendations.raw_json`
- Output path safety / deterministic file generation expectations

## Regression Expectations

- Keep regression pack baseline green
- Keep golden parity unchanged
- No secret/token leakage in generated artifacts
