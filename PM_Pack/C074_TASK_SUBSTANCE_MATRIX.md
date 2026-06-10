# C074_TASK_SUBSTANCE_MATRIX

## Header
- Cycle: C074
- Agent: B
- Total tasks: 55
- Expected LARGE+ count: 55

Scoring dimensions:
- Production Outcome
- Complexity
- Integration Depth
- Evidence Strength
- Novelty
- E2E Readiness

Scale: 1-5 each, total max 30.

| Task ID | Task | Production Outcome | Complexity | Integration Depth | Evidence Strength | Novelty | E2E Readiness | Total | Size |
|---|---|---:|---:|---:|---:|---:|---:|---:|---|
| B-01 | Implement pilot_logger.py module | 5 | 4 | 5 | 4 | 5 | 4 | 27 | XLARGE |
| B-02 | Implement live_pilot.py orchestration | 5 | 4 | 4 | 5 | 5 | 5 | 28 | XLARGE |
| B-03 | Add collect-live CLI command | 5 | 5 | 4 | 4 | 5 | 5 | 28 | XLARGE |
| B-04 | Add live-validate CLI command | 5 | 4 | 4 | 5 | 5 | 5 | 28 | XLARGE |
| B-05 | Add recommendations-only --live flag | 5 | 4 | 5 | 4 | 5 | 5 | 28 | XLARGE |
| B-06 | Add playbook CLI command | 5 | 5 | 5 | 4 | 5 | 4 | 28 | XLARGE |
| B-07 | Create playbook generator.py | 5 | 4 | 4 | 4 | 5 | 4 | 26 | LARGE |
| B-08 | Create playbook HTML template | 5 | 4 | 4 | 4 | 5 | 4 | 26 | LARGE |
| B-09 | Extend RecommendationOutput fields | 5 | 5 | 4 | 4 | 5 | 4 | 27 | XLARGE |
| B-10 | Add scrapfly-sdk requirement | 5 | 4 | 5 | 4 | 5 | 4 | 27 | XLARGE |
| B-11 | Add pilot artifacts to gitignore | 5 | 4 | 5 | 4 | 5 | 4 | 27 | XLARGE |
| B-12 | Write test_live_pilot.py | 5 | 5 | 4 | 5 | 5 | 4 | 28 | XLARGE |
| B-13 | Write test_playbook_generator.py | 5 | 4 | 4 | 5 | 5 | 4 | 27 | XLARGE |
| B-14 | Wire runtime scrapfly override | 5 | 4 | 4 | 4 | 5 | 4 | 26 | LARGE |
| B-15 | Seed pilot niche helper | 5 | 5 | 5 | 4 | 5 | 4 | 28 | XLARGE |
| B-16 | Implement evidence bundle always-write | 5 | 4 | 5 | 5 | 5 | 5 | 29 | XXLARGE |
| B-17 | Implement stop_reason mapping | 5 | 4 | 4 | 4 | 5 | 4 | 26 | LARGE |
| B-18 | Implement session preflight | 5 | 5 | 4 | 4 | 5 | 4 | 27 | XLARGE |
| B-19 | Implement DB validation helper | 5 | 4 | 4 | 4 | 5 | 5 | 27 | XLARGE |
| B-20 | Implement live recommendations helper | 5 | 4 | 5 | 4 | 5 | 5 | 28 | XLARGE |
| B-21 | Implement playbook live helper | 5 | 5 | 5 | 4 | 4 | 5 | 28 | XLARGE |
| B-22 | Implement export stage recording | 5 | 4 | 4 | 4 | 4 | 4 | 25 | LARGE |
| B-23 | Implement staged evidence structure | 5 | 4 | 4 | 4 | 4 | 4 | 25 | LARGE |
| B-24 | Preserve config guard false | 5 | 5 | 4 | 4 | 4 | 4 | 26 | LARGE |
| B-25 | Implement pilot DB isolation default | 4 | 4 | 5 | 4 | 4 | 4 | 25 | LARGE |
| B-26 | Implement URL truncation in logs | 4 | 4 | 5 | 4 | 4 | 4 | 25 | LARGE |
| B-27 | Implement requests_by_stage rollup | 4 | 5 | 4 | 4 | 4 | 4 | 25 | LARGE |
| B-28 | Implement error_rate threshold | 4 | 4 | 4 | 4 | 4 | 4 | 24 | LARGE |
| B-29 | Implement block_rate threshold | 4 | 4 | 4 | 4 | 4 | 4 | 24 | LARGE |
| B-30 | Implement credits aggregation | 4 | 5 | 5 | 4 | 4 | 4 | 26 | LARGE |
| B-31 | Implement CLI success output contract | 4 | 4 | 5 | 4 | 4 | 4 | 25 | LARGE |
| B-32 | Implement CLI stderr stop_reason contract | 4 | 4 | 4 | 4 | 4 | 4 | 24 | LARGE |
| B-33 | Add collect-live help text | 4 | 5 | 4 | 4 | 4 | 4 | 25 | LARGE |
| B-34 | Add live-validate help text | 4 | 4 | 4 | 4 | 4 | 4 | 24 | LARGE |
| B-35 | Add post-stop evidence persistence | 4 | 4 | 5 | 4 | 4 | 4 | 25 | LARGE |
| B-36 | Add fallback dry_run handling | 4 | 5 | 5 | 4 | 4 | 4 | 26 | LARGE |
| B-37 | Add build_llm_client fallback path | 4 | 4 | 4 | 4 | 4 | 4 | 24 | LARGE |
| B-38 | Add one-niche filtering | 4 | 4 | 4 | 4 | 4 | 4 | 24 | LARGE |
| B-39 | Add run_id generation for pilot | 4 | 5 | 4 | 4 | 4 | 4 | 25 | LARGE |
| B-40 | Add session cleanup guarantees | 4 | 4 | 5 | 4 | 4 | 4 | 25 | LARGE |
| B-41 | Add recommendation dry_run output | 4 | 4 | 5 | 4 | 4 | 4 | 25 | LARGE |
| B-42 | Add playbook markdown exporter | 4 | 5 | 4 | 4 | 4 | 4 | 25 | LARGE |
| B-43 | Add playbook pdf exporter guard | 4 | 4 | 4 | 4 | 4 | 4 | 24 | LARGE |
| B-44 | Add playbook section ordering | 4 | 4 | 4 | 4 | 4 | 4 | 24 | LARGE |
| B-45 | Add niche display-name mapping | 4 | 5 | 5 | 4 | 4 | 4 | 26 | LARGE |
| B-46 | Add section builder account setup | 4 | 4 | 5 | 4 | 4 | 4 | 25 | LARGE |
| B-47 | Add section builder gig creation | 4 | 4 | 4 | 4 | 4 | 4 | 24 | LARGE |
| B-48 | Add section builder first orders | 4 | 5 | 4 | 4 | 4 | 4 | 25 | LARGE |
| B-49 | Add section builder review | 4 | 4 | 4 | 4 | 4 | 4 | 24 | LARGE |
| B-50 | Add section builder optimization | 4 | 4 | 5 | 4 | 4 | 4 | 25 | LARGE |
| B-51 | Add no-migration assurance checks | 4 | 5 | 5 | 4 | 4 | 4 | 26 | LARGE |
| B-52 | Add baseline untouched checks | 4 | 4 | 4 | 4 | 4 | 4 | 24 | LARGE |
| B-53 | Add wave 9+10 integrity checks | 4 | 4 | 4 | 4 | 4 | 4 | 24 | LARGE |
| B-54 | Add TierD-2 acceptance docs linkage | 4 | 5 | 4 | 4 | 4 | 4 | 25 | LARGE |
| B-55 | Add post-merge pilot instructions | 4 | 4 | 5 | 4 | 4 | 4 | 25 | LARGE |

## Interpretation
- XXLARGE: total >= 29
- XLARGE: total 27-28
- LARGE: total <= 26

This matrix is the production evidence model for C074 task substance validation.
