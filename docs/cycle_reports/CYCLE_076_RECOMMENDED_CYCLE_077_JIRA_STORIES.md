# Recommended Cycle 077 Jira Stories

These stories should be created in Jira (SCRUM project) before Cycle 077 plan-cycle --live.

| Summary | Type | Epic | Acceptance Criteria | Size |
|---|---|---|---|---|
| Execute V-1 live Fiverr collection (1 keyword) and archive evidence | Story | TierD-2 Validation | 1) collect-live runs for 1 keyword without error; 2) data/evidence/v1_payload_*.json created and non-empty; 3) live_validation_evidence.json shows v1_status=PASS; 4) targeted tests pass | XL |
| Execute V-2 live parsing validation on V-1 payload | Story | TierD-2 Validation | 1) V-1 must PASS first; 2) V-1 payload passes all schema validators without violations; 3) live_validation_evidence.json shows v2_status=PASS | L |
| Execute V-3 full live scoring pass and compare against golden anchor | Story | TierD-2 Validation | 1) V-2 must PASS first; 2) scoring pipeline runs on live data; 3) key score dimensions within 10% of golden anchor kw=110 at 62.7; 4) deviation logged | XL |
| Merge cycle/075/integration PR and verify CI pass | Story | Go-Live Pipeline | 1) PR CI status is all green; 2) merge gate --dry-run returns PASS; 3) Kevin approves and merges; 4) develop HEAD updated | L |
| Execute Stage 2: docs-only assisted Agent D test on test branch | Story | Go-Live Pipeline | 1) PR merged to develop first; 2) create test/stage2 branch; 3) dispatch Agent D with docs-only prompt; 4) Agent D writes docs, commits, AGENT_COMPLETE present | XL |
| Raise combined automation+src coverage to >=90% (complete Agent F work) | Story | Quality Gates | 1) pytest --cov=automation --cov=src --cov-fail-under=90 passes; 2) no regressions introduced; 3) coverage report shows all automation/ modules >=90% | XXL |
| Add Jira Done transitions for all Cycle 076 stories after PR merge | Story | Jira Sync | 1) PR merged to develop; 2) CI passes on merged commit; 3) all in-scope stories transitioned to Done via jira_client; 4) JIRA_SYNC_SUMMARY updated | L |
| Update TierD-2 tracker with V-1/V-2 evidence (after V-1/V-2 complete) | Story | TierD-2 Validation | 1) V-1 and V-2 both PASS; 2) CYCLE_077_TIERD2_TRACKER.json shows V-1=EARNED, V-2=EARNED; 3) Score 2 recalculated with new multiplier; 4) PM_Pack PRODUCTION_READINESS_SCORECARD updated | L |
| Add GitHub branch protection evidence capture (fix 401 from Cycle 075 Agent A) | Bug | Runner Governance | 1) gh api /repos/.../branches/develop/protection returns 200 (not 401); 2) evidence written to docs/governance/BRANCH_PROTECTION_EVIDENCE.md; 3) gh auth status shows correct token | M |
| Stabilize automation-only full-suite coverage capture in runner environment | Story | Quality Gates | 1) tests/unit --cov=automation run completes without truncation; 2) coverage artifacts are saved deterministically; 3) CI/local parity documented | M |
