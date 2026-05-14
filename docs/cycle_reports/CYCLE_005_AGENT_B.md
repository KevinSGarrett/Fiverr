# Cycle 005 Agent B - Codex Fix Disposition

## Scope

- Agent: B (Collection Engineer)
- PR: #3
- Codex disposition status: `VALID_FIXED` for both reported items
- Primary fix commit hash: `44bda92a9287d931f5af87beb38a63f0ad60c45e`

## Codex Item 1 - Dry-run non-positive sample size forwarding

- Thread reference: `src/orchestrator.py` `run_collection_dry_run` forwarding path (`_resolve_collection_max_candidates` and call-site, approx. lines 114-159).
- Codex disposition: `VALID_FIXED`
- Root cause: non-positive `sample_size` values were intended to select all seed keywords but downstream keyword expansion still required a strictly positive `max_candidates`; previous cap was not robust enough for uncapped fixture runs with modifiers.
- Fix implemented:
  - Added `_resolve_collection_max_candidates(...)` in `src/orchestrator.py`.
  - Positive `sample_size` semantics are unchanged (exact cap preserved).
  - Non-positive `sample_size` now computes a safe strictly-positive cap using seed/modifier shape.
- Files changed:
  - `src/orchestrator.py`
  - `tests/unit/test_cli.py`
- Regression evidence added:
  - `test_collection_dry_run_cli_sample_size_zero_succeeds`
  - `test_orchestrator_collection_dry_run_negative_sample_size_uses_safe_candidate_cap`
  - `test_orchestrator_collection_dry_run_positive_sample_size_preserves_cap`

### Agent D PR reply draft (Codex Item 1)

```text
Codex disposition: VALID_FIXED

Root cause:
The non-positive sample-size branch selected all seeds, but dry-run candidate ceiling handling was not robust for uncapped fixture expansion paths.

What changed:
- Added explicit cap resolution in src/orchestrator.py via _resolve_collection_max_candidates(...).
- Preserved existing behavior for positive sample sizes.
- For sample_size <= 0, now compute a guaranteed strictly positive safe cap derived from seed/modifier inputs.

Regression tests:
- tests/unit/test_cli.py::test_collection_dry_run_cli_sample_size_zero_succeeds
- tests/unit/test_cli.py::test_orchestrator_collection_dry_run_negative_sample_size_uses_safe_candidate_cap
- tests/unit/test_cli.py::test_orchestrator_collection_dry_run_positive_sample_size_preserves_cap

Validation commands:
- python -m pytest tests/unit/test_collection.py tests/unit/test_cli.py -q
- python run.py phase2-smoke
- python -m ruff check src/collection src/orchestrator.py tests/unit/test_collection.py tests/unit/test_cli.py
- python -m mypy src/collection src/orchestrator.py

Resolve thread after push/checks: Yes
```

## Codex Item 2 - data-testid text extraction truncation with nested markup

- Thread reference: `src/collection/gig_detail.py` `_extract_text` nested markup handling (approx. lines 51-53).
- Codex disposition: `VALID_FIXED`
- Root cause: regex-based `data-testid` extraction can terminate on child element close tags and truncate parent text payload.
- Fix implemented:
  - Added parser-based helper `extract_data_testid_text(...)` in `src/collection/html_text.py` using `html.parser.HTMLParser` with depth tracking.
  - Updated `src/collection/gig_detail.py` to use parser helper.
  - Updated `src/collection/seller_profile.py` to reuse the same safe helper (targeted hardening with low risk).
- Files changed:
  - `src/collection/html_text.py` (new)
  - `src/collection/gig_detail.py`
  - `src/collection/seller_profile.py`
  - `tests/unit/test_collection.py`
- Regression evidence added:
  - `test_gig_detail_nested_inline_markup_preserves_full_description_text`
  - `test_extract_data_testid_text_returns_none_when_testid_missing`
  - `test_seller_profile_nested_markup_preserves_display_name_text`

### Agent D PR reply draft (Codex Item 2)

```text
Codex disposition: VALID_FIXED

Root cause:
Regex extraction for data-testid content can stop at nested child closings, truncating text instead of reading through the matched parent element.

What changed:
- Introduced a depth-aware HTMLParser helper in src/collection/html_text.py (extract_data_testid_text).
- Switched gig detail parser extraction to this helper.
- Also reused the same helper in seller profile parser to reduce parallel parser risk without widening scope beyond collection parsing.

Regression tests:
- tests/unit/test_collection.py::test_gig_detail_nested_inline_markup_preserves_full_description_text
- tests/unit/test_collection.py::test_extract_data_testid_text_returns_none_when_testid_missing
- tests/unit/test_collection.py::test_seller_profile_nested_markup_preserves_display_name_text

Validation commands:
- python -m pytest tests/unit/test_collection.py tests/unit/test_cli.py -q
- python run.py phase2-smoke
- python -m ruff check src/collection src/orchestrator.py tests/unit/test_collection.py tests/unit/test_cli.py
- python -m mypy src/collection src/orchestrator.py

Resolve thread after push/checks: Yes
```

## Command Log

- `python -m pytest tests/unit/test_collection.py tests/unit/test_cli.py -q`
- `python run.py phase2-smoke`
- `python -m ruff check src/collection src/orchestrator.py tests/unit/test_collection.py tests/unit/test_cli.py`
- `python -m mypy src/collection src/orchestrator.py`
