# CYCLE 067 - AGENT F HANDOFF

## F Zone

Allowed:

- `tests/`
- F report file(s) in `docs/cycle_reports/`

Primary target:

- Expand and harden S7.3 test suite for adjacent niche mode.

## Coverage and Quality Targets

- `src/discovery/hypothesis.py` coverage target: >=80% (higher than S7.2 bar due added S7.3 functions).
- Keep total suite healthy and do not regress baseline gate expectations.

## Required Edge Case Matrix

- Empty `seed_keywords` handling.
- Duplicate `existing_niches` filtering.
- `min_confidence` boundary behavior at and around `0.50`.
- All 9 niche IDs as parameterized `source_niche_id` tests.
- Unknown niche id returns empty candidate set.
- Candidate deduplication across repeated/overlapping seed inputs.

## Minimum Test Structure

Create/extend `tests/unit/test_adjacent_niche_hypotheses.py` to include >=30 tests:

- `TestBuildAdjacentNicheCandidates` (~6 tests)
- `TestScoreNicheCandidateConfidence` (~5 tests)
- `TestGenerateAdjacentNicheHypotheses` (>=19 tests)

Use explicit Arrange/Act/Assert structure and mirror S7.2 class organization where appropriate.

## Regression Safety

Confirm no regressions for:

- existing adjacent keyword tests
- discovery core budget gate tests
- Wave 9 pricing import sanity

## Policy Context

- v4.3 active: 55 LARGE-XXLARGE tasks minimum.
- F floor target: 1000 lines.
