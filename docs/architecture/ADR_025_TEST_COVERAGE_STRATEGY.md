# ADR 025: Provider Router V7 Test Coverage Strategy

## Status

Accepted

## Context

Cycle 080 adds Provider Router V7 modules for classification, routing, health checks, budget checks,
prompt rendering, and provider adapters. These modules control dispatch safety and must be regression
protected with deterministic tests.

## Decision

- **Test pyramid**
  - Unit tests cover module logic and error paths.
  - Integration tests cover cross-module routing and artifact behavior.
  - Stage 2-7 E2E remains a downstream orchestration concern.
- **Mock strategy**
  - No real AI provider calls in unit/integration tests.
  - Mock Claude subprocess boundaries.
  - Mock OpenAI SDK calls and budget outcomes.
- **Fixture patterns**
  - Use `tmp_path` for writable state/artifact paths.
  - Use `monkeypatch` for env/path redirection (`PROVIDER_HEALTH_PATH`, ledger paths, policy path).
  - Keep tests hermetic and avoid mutation of real runner state.
- **Coverage targets**
  - Minimum >80% per new Provider Router V7 module.
  - Focused coverage gate stays >=90% where configured.
- **Known hanger exclusions**
  - `tests/unit/test_queue_processor.py`
  - `tests/unit/test_collection_orchestrator.py`
  - `tests/unit/test_cycle062_smoke_aliases.py`
  - `tests/unit/test_post_cycle_review_coverage.py`
- **Integration scope**
  - Validate classify -> health -> policy -> decision artifact flow.
  - Validate advisory-only behavior and budget hard-block flow.
  - Do not perform external network/subprocess provider calls.

## Consequences

- Provider-routing regressions are caught earlier with deterministic, hermetic checks.
- Safety gates move from policy text into executable assertions.
- CI remains stable by excluding known hanging tests from standard regression commands.
