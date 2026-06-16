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

## Cycle 081 Test Additions

- advisory_confirm mode coverage in `test_provider_router.py`:
  - `test_advisory_confirm_cursor_dispatches`
  - `test_advisory_confirm_claude_blocked`
  - `test_advisory_confirm_deterministic_unchanged`
  - `test_route_dry_run_advisory_confirm_mode`
- stage2 readiness command coverage in `test_stage2_readiness.py` (4 tests).
- catalog schema coverage in `test_catalog_schemas.py` (6 tests, including invalid payload fail case).
- provider module extension coverage:
  - `test_provider_health.py`: update/refresh status transitions and repeated error blocking.
  - `test_provider_usage_ledger.py`: weekly spend and ledger summary structure/sums.
  - `test_cost_guard.py`: `update_spend()` and policy-loaded limits.
  - `test_prompt_renderer.py`: `render_with_overrides()` and empty `jira_scope`.
  - `test_provider_router_integration.py`: advisory-confirm dispatch integration path.
- checklist completion coverage:
  - `test_export_sanitizer_verify.py`: 5 tests (EXPORT-001).
  - `test_notification_router.py`: 3 tests (STATE-010).
  - `test_cursor_adapter.py`: 2 tests (DISPATCH-013).
  - `test_run_agent_lifecycle.py`: 3 tests (DISPATCH-017/020).
  - `test_post_cycle_review.py`: 4 tests (BRAIN-021).
  - `test_pm_pack_consistency_audit.py`: +1 FC-8 coverage test for post-cycle advisory dispatch block, file now at 8 tests total.
- cycle-level suite snapshot after Agent F changes:
  - Collected tests: 5704.
  - Full suite: 5704 passed, 0 failed (2 warnings).
