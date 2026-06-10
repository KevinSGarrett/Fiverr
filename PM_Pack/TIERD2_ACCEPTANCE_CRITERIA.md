# TIERD2_ACCEPTANCE_CRITERIA

## Condition A: One Niche Scope
- AC-1 config scoped to exactly one niche.
- AC-2 runtime niche id matches CLI input.
- AC-3 missing `--niche` fails fast.
- Named test: `test_tierd2_condition_a_one_niche_scope`.

## Condition B: Credit Ceiling
- AC-1 `cost_budget_credits` set from CLI budget.
- AC-2 `ScrapFlyRateLimitError` raised when exceeded.
- AC-3 stop reason is `budget_exceeded`.
- Named test: `test_tierd2_condition_b_budget_ceiling`.

## Condition C: Persistent Logging
- AC-1 `PilotLogger` instantiated in live pilot flow.
- AC-2 JSONL file created on first request.
- AC-3 N requests => N JSON lines.
- Named test: `test_tierd2_condition_c_request_logging`.

## Condition D: Stop Controls
- AC-1 `stop_conditions_triggered` when block rate > 0.5.
- AC-2 `stop_conditions_triggered` when error rate > 0.3.
- AC-3 evidence always written.
- Named test: `test_tierd2_condition_d_stop_controls`.

## Condition E: Pilot DB Isolation
- AC-1 pilot db url != baseline production db url.
- AC-2 pilot db url includes niche id.
- AC-3 baseline mtime unchanged.
- Named test: `test_tierd2_condition_e_db_isolation`.

## Condition F: Committed Config Guard
- AC-1 `config.yaml` keeps `scrapfly.enabled: false`.
- AC-2 runtime override only in pilot path.
- AC-3 no commit with persisted true state.
- Named test: `test_tierd2_condition_f_config_guard`.

## Condition G: Session Control
- AC-1 `ensure_session` called before live collection.
- AC-2 session failure maps to `session_expired` stop reason.
- AC-3 session resources closed in finally/cleanup.
- Named test: `test_tierd2_condition_g_session_gate`.

## Condition H: Evidence Persistence
- AC-1 evidence written on successful run.
- AC-2 evidence written on failed run.
- AC-3 required evidence keys all present.
- Named test: `test_tierd2_condition_h_evidence_persistence`.

## Condition I: Threshold Logic
- AC-1 block rate > 0.5 toggles stop flag.
- AC-2 error rate > 0.3 toggles stop flag.
- AC-3 thresholds are deterministic and tested.
- Named test: `test_tierd2_condition_i_thresholds`.

## Condition J: Runtime-Only Enablement
- AC-1 disk config remains false.
- AC-2 runtime payload can set true during pilot only.
- AC-3 C gates verify no persistent enablement drift.
- Named test: `test_tierd2_condition_j_runtime_override_only`.

## Production Readiness Link
All A-J conditions protect TierD-2 V-3 live validation credit.
