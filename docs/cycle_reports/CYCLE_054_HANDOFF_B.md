# Handoff A -> B (Implementer)

## Ownership and boundaries

- You own all `src/` changes for Cycle 054.
- You may add/adjust unit tests for implemented calculators.
- Keep all behavior additive and toggle-gated.
- Do not introduce new modules for R4.

## Core invariants

1. **DL-209 no-compound rule**: TRC adjustment must be one consolidated multiplier, never chained products.
2. **Backward compatibility**: missing/None new signal must not penalize by default.
3. **Parity**: toggle OFF paths remain legacy-identical.
4. **Null handling**: `NULL = unknown = include`.

## Story implementation map

### B1 / SCRUM-613 - demand TRC reliability

Primary file: `src/scoring/demand_score.py`

Add:

- `_compute_trc_reliability(rsv_relevance: float | None, sponsored_fraction: float | None, strictness: str | None, weights: dict | None = None) -> float`
- return one factor in `[0,1]`
- any `None` component -> `1.0`
- use MIN factor composition (no product chain)

Toggle:

- `scoring.demand.use_trc_reliability` (default false)

Call-site rule:

- replace stacked TRC multipliers with one consolidated path when toggle ON
- preserve legacy branch when OFF

### B2 / SCRUM-614 - signal qualifiers

Primary file: `src/scoring/demand_score.py`

Add:

- `_classify_autocomplete_state(suggestions: list[str] | None) -> str` (`present|emerging|absent`)
- `_trends_platform_qualifier(trends_signal: dict | None) -> float`

Toggle:

- `scoring.demand.use_signal_qualifiers` (default false)

Behavior:

- emerging and absent must be distinguished
- trends qualifier only affects demand when toggle ON

### B3 / SCRUM-615 - profile source selection

Primary file: `src/scoring/competition_score.py`

Add:

- `_select_competitor_profile(per_keyword: CompetitorProfile | None, per_niche: CompetitorProfile | None) -> CompetitorProfile | None`

Toggle:

- `scoring.competition.use_per_keyword_profile` (default false)

Behavior:

- prefer per-keyword when present/non-empty, else per-niche
- record selected source for integrity output (`per_keyword|per_niche`)

### B4 / SCRUM-813 - contamination exclusion

Files:

- `src/scoring/competition_score.py`
- competitor profile builder path used by scoring

Add:

- `_exclude_contaminated_competitors(profile: CompetitorProfile, contaminated_keyword_ids: set[int]) -> CompetitorProfile`

Toggle:

- `scoring.competition.exclude_contaminated` (default false)

Behavior:

- remove contaminated-keyword competitors from aggregate profile when ON

### B5 / SCRUM-616 - IQR outlier exclusion

Files:

- `src/scoring/competition_score.py`
- `src/scoring/profitability.py`

Add shared helper:

- `_exclude_price_outliers_iqr(prices: list[float]) -> tuple[list[float], int]`
- IQR fence method
- if `len(prices) < 4` -> unchanged + zero excluded

Toggle:

- `scoring.exclude_price_outliers` (default false)

Behavior:

- both competition and profitability price stats must use kept set when ON
- capture excluded count for integrity output

### B6 / SCRUM-617 - clean-gig feasibility

Primary file: `src/scoring/feasibility.py`

Add:

- `_clean_gig_set(gigs: list[Gig]) -> list[Gig]`
- clean = relevant AND not sponsored AND not zombie

Toggle:

- `scoring.feasibility.use_clean_gig_set` (default false)

Behavior:

- level ratio and organic review barrier use clean set only when ON
- OFF remains legacy full set

### B7 / SCRUM-618 - opportunity qualifier + intent + integrity columns

Files:

- `src/scoring/intent.py`
- opportunity calculation path
- `src/models` (`KeywordScore`)

Add:

- `_opportunity_relevance_qualifier(rsv_relevance: float | None) -> float` (`None -> 1.0`)
- intent alignment integration notes/logic

Toggle:

- `scoring.opportunity.qualify_by_relevance` (default false)

KeywordScore additive nullable columns:

- `trc_reliability` (float)
- `opportunity_relevance_factor` (float)
- `price_outliers_excluded` (int)
- `clean_gig_count` (int)
- `competitor_profile_source` (str)

### B8 / SCRUM-619 - calculator-level unit tests

- add/extend per-calculator unit tests for B1-B7 behavior
- keep all unit tests network-free (mock clients/fetchers)
- F owns coverage backfill + permanent REG seating

## Config contract

B adds the following toggles under `scoring` with default false (committed):

- `scoring.demand.use_trc_reliability: false`
- `scoring.demand.use_signal_qualifiers: false`
- `scoring.competition.use_per_keyword_profile: false`
- `scoring.competition.exclude_contaminated: false`
- `scoring.exclude_price_outliers: false`
- `scoring.feasibility.use_clean_gig_set: false`
- `scoring.opportunity.qualify_by_relevance: false`

## Worked invariant examples

### EX-1 (required)

- Input component factors: `0.60`, `0.70`, `1.00`
- Correct consolidated factor: `min(...) = 0.60`
- Correct result: `100 * 0.60 = 60.0`
- Incorrect forbidden chain: `100 * 0.60 * 0.70 * 1.00 = 42.0`

### EX-2 (required)

- prices `[5, 8, 10, 11, 12, 12, 13, 15, 400]`
- `400` excluded by IQR fence
- kept set length = `8`
- `price_outliers_excluded = 1`

### EX-3 (required)

- opportunity raw `80.0`, RSV `0.75`
- qualified opportunity `60.0`
- factor recorded `0.75`

## Acceptance checklist for your exit

- [ ] all seven toggles implemented with default false
- [ ] OFF paths are legacy-identical
- [ ] no new modules added
- [ ] integrity columns additive + nullable only
- [ ] no live network in tests
- [ ] local parity sanity (OFF) passes

## Commit discipline

- commit prefixes: `feat(scoring):` or `fix(scoring):`
- pre-push:
  - `git pull --rebase`
  - ensure diff constrained to `src/` + relevant tests

