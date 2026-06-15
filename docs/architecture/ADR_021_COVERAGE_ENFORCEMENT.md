# ADR 021: Coverage Enforcement

## Status
Accepted

## Context
Cycle 078 requires a fail-closed coverage gate with a minimum threshold of 90% and explicit test ownership for new automation modules.

## Decision
- CI must enforce `--cov-fail-under=90` on unit tests.
- New automation modules must include at least one dedicated unit test file under `tests/unit/`.
- Coverage verification for Agent F lane modules is performed with targeted module-level runs in addition to full-suite attempts.

## Consequences
- Pull requests that regress tested coverage below policy threshold fail early in CI.
- Newly introduced files such as `automation/export_sanitizer_verify.py` must ship with tests (`tests/unit/test_export_sanitizer_verify.py`).
- Repository-wide full-suite coverage remains sensitive to environment-level long-session interruptions and should use batched execution and evidence reports until the interruption root cause is removed.
