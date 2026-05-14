# Cycle 006 - Agent C Report

## Scope and ownership

- Agent C scope: `src/analysis/`, analysis/LLM tests, and Codex defect disposition evidence.
- This cycle fixed the valid Codex finding in `src/analysis/orchestrator.py` around null intent keyword handling.
- No GitHub Actions or Codecov files were modified.

## Bug summary

- Defect: when `payload["intent"]["keyword_text"]` existed but was `null`, orchestrator used `str(None)` and passed `"None"` into intent classification.
- Impact: silently degraded intent analysis quality by classifying a synthetic literal instead of a meaningful fallback keyword.
- Severity for Cycle 006: blocker, because it affects core analysis signal quality and confidence.

## Root cause

- In the intent stage, the prior branch treated presence of `intent.keyword_text` as authoritative and coerced the value with `str(...)`.
- For `None`, this produced `"None"` instead of treating the value as absent and continuing fallback resolution.
- Fallback logic also only used first keyword entry directly and did not skip blank/null-ish values in priority order.

## Fix summary

### Orchestrator changes

- Added `_non_empty_text_or_none` helper to consistently treat `None`, empty string, and whitespace-only values as absent.
- Added `_resolve_intent_keyword_text` helper to enforce fallback priority:
  1. non-empty `intent.keyword_text`
  2. non-empty top-level `payload.keyword_text`
  3. first non-empty value from `payload.keywords`
  4. `source_id`
- Updated `source_id` initialization to avoid blank/null-ish values defaulting to invalid text.
- Kept valid non-empty `intent.keyword_text` behavior intact (still highest priority and passed through unchanged).
- Preserved `title_phrases` routing from `intent` section when present.

### Product-rule note for literal `"None"` / `"null"`

- Task C1 requirement is enforced literally: final keyword text cannot be `"None"`, `"null"`, or blank when `source_id` exists.
- This implementation treats case-insensitive `"none"` / `"null"` keyword text as absent and continues fallback resolution.
- Operationally, that means even user-provided literal `"None"`/`"null"` is sanitized to fallback candidates.

## Regression tests added

Added/updated tests in `tests/unit/test_analysis.py`:

- Intent keyword fallback and null handling:
  - prefers valid `intent.keyword_text`
  - `intent.keyword_text is None` -> fallback to `payload.keyword_text`
  - `intent.keyword_text == ""` -> fallback to `payload.keyword_text`
  - `intent.keyword_text` whitespace-only -> fallback to `payload.keyword_text`
  - missing `intent.keyword_text` -> fallback to `payload.keyword_text`
  - fallback to first non-empty keyword in `payload.keywords`
  - fallback to `source_id` when all keyword sources are absent/nullish
- Title phrase regression:
  - `intent.keyword_text` null + `intent.title_phrases` present still forwards title phrases to classifier input.
- `"None"` guard:
  - verifies `"None"` is not generated from Python `None`.
  - verifies literal `"None"` and `"null"` are treated as absent and resolve to fallback.
- Coverage-adjacent orchestrator tests (Task C5):
  - non-dict intent section uses top-level `title_phrases`
  - non-string keyword entry coercion path
  - intent-stage validation error branch
  - run status `FAILED` when no stages execute
- Updated prior test expectation:
  - blank intent keyword now falls back to `source_id` and yields successful intent stage, so run status is `SUCCESS` rather than `FAILED`.

## Validation commands and results

- `python -m pytest tests/unit/test_analysis.py -q`
  - Passed: `41 passed`
- `python -m ruff check src/analysis tests/unit/test_analysis.py`
  - Passed: `All checks passed!`
- `python -m mypy src/analysis`
  - Passed: `Success: no issues found in 11 source files`
- `python -m pytest -q --cov=src --cov-report=xml --cov-report=term-missing --cov-fail-under=90`
  - Passed: `265 passed`
  - Coverage gate passed: `Required test coverage of 90% reached. Total coverage: 92.77%`

## Coverage impact

- `src/analysis/orchestrator.py` improved from `87%` to `93%` in this cycle.
- Overall repository coverage increased to `92.77%` while keeping the global `>=90%` gate green.

## Suggested PR/Codex thread reply for Agent D

```text
Codex disposition: VALID_FIXED

Root cause:
- In src/analysis/orchestrator.py intent stage, intent.keyword_text was coerced via str(...).
- When intent.keyword_text existed but was null, str(None) produced literal "None", which was sent to intent classification.

Fix:
- Added explicit null/blank handling helper and deterministic fallback resolver.
- Fallback order is now:
  1) non-empty intent.keyword_text
  2) non-empty payload.keyword_text
  3) first non-empty payload.keywords entry
  4) source_id
- This prevents null-derived "None"/blank keywords from reaching classifier input.
- title_phrases forwarding behavior is preserved.

Regression evidence:
- tests/unit/test_analysis.py includes explicit cases for:
  - intent.keyword_text = None, "", whitespace, and missing
  - payload.keyword_text fallback
  - first keyword fallback
  - source_id fallback
  - title_phrases preservation when intent keyword is null
  - guard proving "None" is not generated from null

Validation:
- python -m pytest tests/unit/test_analysis.py -q
- python -m ruff check src/analysis tests/unit/test_analysis.py
- python -m mypy src/analysis
- python -m pytest -q --cov=src --cov-report=xml --cov-report=term-missing --cov-fail-under=90
```
