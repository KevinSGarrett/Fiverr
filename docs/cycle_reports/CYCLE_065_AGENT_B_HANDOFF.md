# CYCLE 065 - AGENT B HANDOFF

Date: 2026-06-04  
Branch: `cycle/065/integration`  
Base SHA reference in prompt: `5d58d43` (note: current `origin/develop` is newer: `e59ba6e`)

## Scope

Wave 9 Phase 4 S6.8 Pricing Export implementation (export-only, no schema changes):

- 6.8.1 format support: CSV, JSON, Excel, Markdown
- 6.8.2 content validation: complete/safe payload assembly from existing pricing tables
- 6.8.3 export tests: content, formatting, sparse-data behavior

## Files

### Create

- `src/pricing/pricing_export.py`
- `tests/unit/test_pricing_export.py` (target: >= 25 tests)

### Modify

- `src/pricing/__init__.py` (add S6.8 exports)
- `run.py` (or existing CLI wiring location) to add pricing-export mode

## Required Function Signatures

- `export_pricing_csv(keyword_id, db, output_path) -> str`
- `export_pricing_json(keyword_id, db, output_path) -> str`
- `export_pricing_excel(keyword_ids, db, output_path) -> str`
- `export_pricing_markdown(keyword_id, db, output_path) -> str`
- `export_all_pricing(keyword_ids, db, output_dir, formats) -> dict[str, str]`
- `build_pricing_export_payload(keyword_id, db) -> dict`

## Source-Task Mapping (SCRUM-194)

- `build_pricing_export_payload` -> 6.8.2 content validation
- `export_pricing_csv/json/excel/markdown` -> 6.8.1 format support
- `export_all_pricing` -> 6.8.1 orchestration + 6.8.3 testable multi-format behavior

## Export Data Sources (All Required)

Use all five pricing tables:

- `price_analysis` (53 columns)
- `niche_price_analysis` (19 columns)
- `pricing_snapshots` (21 columns)
- `price_ladder_snapshots` (16 columns)
- `revenue_gate_records` (12 columns)

LLM pricing output availability:

- `recommendations` table exists
- no `pricing_strategy` column
- no `output_json` column
- use `recommendations.raw_json` payload pattern for pricing strategy extraction when present

## Pricing Table Headers (Baseline Columns)

- `price_analysis`: `id`, `keyword_id`, `niche_id`, `run_id`, `basic_n`, `basic_median`, `basic_mean`, `basic_mode`, ... , `extras_price_range`, `analyzed_at`
- `niche_price_analysis`: `id`, `niche_id`, `run_id`, `keywords_analyzed`, `basic_median`, ... , `avg_price_review_correlation`, `moat_strength`, `analyzed_at`
- `pricing_snapshots`: `id`, `keyword_id`, `niche_id`, `run_id`, `entry_basic`, ... , `market_type`, `confidence`, `created_at`
- `price_ladder_snapshots`: `id`, `keyword_id`, `niche_id`, `run_id`, `recorded_at`, ... , `price_delta_pct`, `on_track`, `tolerance`
- `revenue_gate_records`: `id`, `keyword_id`, `niche_id`, `run_id`, `recorded_at`, ... , `monthly_orders_estimate`, `gate_alert_text`

## Existing Export Pattern to Follow

From current codebase:

- deterministic export builders under `src/exports/` for CSV/JSON/Markdown
- path safety checks for relative output dirs
- sparse-data warnings instead of hard-fail where possible
- CLI export commands in `run.py` (`export`, `export-recommendation`, `export-all-recommendations`)

Pricing export should align with this pattern and avoid introducing a separate style.

## Dependency / Output Path Baseline

- `requirements.txt` already includes `openpyxl==3.1.5`
- `requirements.txt` already includes `pandas==2.3.3`
- `.gitignore` already includes `data/exports/`

No dependency addition is required unless implementation needs a new package.

## CLI Guidance

- Existing generic export mode: `run.py export --format ...`
- Existing recommendation export modes: `export-recommendation`, `export-all-recommendations`
- Add a dedicated pricing-export command/mode that fits the same click-command style and writes under `data/exports/pricing` (or equivalent subdir under `data/exports`)

## Guardrails

- No new tables
- No migrations
- No scoring mutations (read-only export)
- No secrets/raw unsafe payload leakage in output artifacts

## Validation Targets

- Preserve golden parity (`kw=110 -> 62.7 / 1.0 / CONDITIONAL_GO`)
- Keep full suite green baseline (`4303 passed` at branch start)
- Include sparse-data and unsupported-format tests
