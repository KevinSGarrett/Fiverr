# State Snapshot - Cycle 045

Updated: 2026-05-27 | Agent A setup complete

## Verified Repository State

- Canonical working directory: `C:\Fiverr\Fiverr`
- Active branch: `cycle/045/integration`
- Tests: `3008` | Coverage: `95.61%` | PR #51: MERGED (merge SHA `483611c8d437f8649f5fdfb1a8a99d5e5190a180`)
- Current local `tests/unit` baseline: `3008 passed`
- Config safety: `collection.scrapfly.enabled=false` (verified)
- Worktrees: `1` entry only
- Jira kickoff: `SCRUM-543` (Task, In Progress), `SCRUM-544` (Story, In Progress)

## Score Baseline

Source: `sqlite:///data/cycle037_live.db`.

- Canonical cycle target baseline: `kw=96 final~=42`, `composite~=54.2`, `CM=0.775`
- Current DB probe output (best row): `kw=96 final=44.22`, `composite contributions~=46.53`
- Current profile projection probe (latest kw=96 row): `aggressive_new_seller final~=43.03` (`composite~=45.29`, `CM=0.95`)
- Tags: `PASS=2152`, `CAUTION=259`, `MONITOR=6`

## weakness.py Findings

- Primary query path: `Keyword`, top-10 `SearchResult` rows (run-scoped when possible), linked `Gig`, optional `GigVisualAnalysis`, optional `GigQualityAnalysis`, legacy `GigQualityScore`.
- Core formula: weighted average of available weakness signals, clamped `0..100`:
  - LLM-inverted quality features (description, thumbnail, FAQ, package differentiation, niche specificity)
  - Weakness count normalization (`raw_count * 10`)
  - Weakness flag penalty from normalized flags (`NO_VIDEO`, `NO_PORTFOLIO`, `THIN_DESCRIPTION`, `NO_FAQ`)
  - Video/portfolio absence rates from collected gig evidence
- Why values like ~49 can occur even with many gigs:
  - Score reflects exploitable competitor weaknesses, not gig volume.
  - If top gigs have low absence rates and modest weakness flags, normalized weakness remains mid-range.
  - Missing LLM signals fallback to stubs (`None`), reducing available high-leverage upside components.
- To push above `70`:
  - Increase observed weakness evidence in top gigs (`weakness_flags_by_gig`, especially high-penalty flags).
  - Improve availability of structured weakness inputs across top results.
  - Enable/populate LLM weakness dimensions with non-null values.

## profitability.py Findings

- Primary query path: top-10 run-scoped `SearchResult` joined to `Gig` (with keyword-level fallback), using `Gig.starting_price` and `Gig.metadata_json`.
- Required fields/signals:
  - `avg_starting_price_top10`
  - `avg_premium_package_price_top10` from `premium_price` / `premium_package_price`
  - `typical_delivery_days` from `delivery_time_days` / `typical_delivery_days`
  - extras coverage via `gig_extras` / `extras` and extras pricing (`avg_extras_price` / `extras_price`)
  - optional `llm_upsell_potential_assessment` (currently stubbed, confidence deduction applies)
- Why low outcomes can persist despite visible prices:
  - Universe normalization can compress scores when prices are near lower bounds.
  - Missing premium/extras/delivery metadata weakens weighted_sum coverage.
  - LLM upsell component is absent by default (stub returns `None`) and applies a confidence penalty.
- To push above `50`:
  - Raise premium package and extras pricing coverage in metadata for top gigs.
  - Ensure delivery-time signals and extras presence are consistently populated.
  - Add non-null upsell potential input (or implement LLM path) to unlock remaining weight.

## Scoring Profile Analysis

- Active profile: `aggressive_new_seller`
- Available profiles:
  - `default`
  - `aggressive_new_seller`
  - `profitability_focus`
  - `trend_chaser`
- Weight distributions recorded from `config.yaml` and validated via `ConfigLoader`.
- Key check: `profitability_focus` does assign higher profitability weight (`0.25`) versus `default` (`0.10`) and `aggressive_new_seller` (`0.05`).
