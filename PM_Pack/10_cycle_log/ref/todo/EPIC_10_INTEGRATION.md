# EPIC 10 — Integration, Testing & Launch
# Fiverr Research System — Implementation To-Do

**Source Specs:** All Waves (cross-cutting)
**Depends On:** Epics 01-09 (all system components)
**Priority:** P0 — Final gate before production use
**Estimated Stories:** 12 | **Estimated Tasks:** 56

---

## Story 10.1 — End-to-End Pipeline Integration

| ID | Task | Type | Description |
|---|---|---|---|
| 10.1.1 | Wire all 16 stages into RunOrchestrator | TASK | Verify complete stage chain: 1(config) → 2(expand) → 3(search) → 4(gig) → 5(seller) → 6(external) → 7(quality) → 8(competitor) → 9(cluster) → 10(score) → 10.5(pricing) → 11(rank) → 12(tags) → 13(recommend) → 14(playbook) → 15(export) → 16(discovery) |
| 10.1.2 | Implement stage dependency validation | TASK | On startup, verify each stage's input tables have data from prerequisite stages |
| 10.1.3 | Implement run mode stage mapping | TASK | full=1-16, collect-only=1-6, analyze-only=7-9, score-only=10-12, recommendations-only=13, discovery-only=16, discovery-collect=16+2-6+7-12, resume=checkpoint-based |
| 10.1.4 | Implement graceful degradation | TASK | If Stage X fails: log error, mark COMPLETED_WITH_ERRORS, continue to Stage X+1 if independent |
| 10.1.5 | Implement run summary generation | TASK | After run: total keywords, scored, STRONG GO count, CONDITIONAL GO count, recommendations generated, cost, duration |
| 10.1.6 | Create end-to-end integration test | TASK | Full pipeline run against 1 niche (2 seed keywords), verify all 28 tables populated |

---

## Story 10.2 — Data Integrity Validation

| ID | Task | Type | Description |
|---|---|---|---|
| 10.2.1 | Create data integrity checker | TASK | `src/utils/integrity.py` — Post-run validation that all expected relationships exist |
| 10.2.2 | Implement orphan detection | TASK | Find keywords without scores, gigs without keywords, sellers without gigs |
| 10.2.3 | Implement score range validation | TASK | All scores 0-100, confidence 0-1, no NaN values |
| 10.2.4 | Implement recommendation completeness check | TASK | All STRONG GO keywords have recommendations with completeness_ratio ≥ 0.70 |
| 10.2.5 | Implement cross-table consistency | TASK | Keyword.cluster_id references existing ClusterAnalysis, OpportunityRanking.keyword_id references existing Keyword |
| 10.2.6 | Create integrity test suite | TASK | Test each integrity check with clean data and deliberately corrupted data |

---

## Story 10.3 — Performance Testing

| ID | Task | Type | Description |
|---|---|---|---|
| 10.3.1 | Create performance benchmark script | TASK | `tests/performance/benchmark.py` — Measure stage durations, LLM costs, memory usage |
| 10.3.2 | Benchmark full pipeline on 9 niches | TASK | Record: total duration, per-stage duration, peak memory, total LLM cost, total API calls |
| 10.3.3 | Benchmark dashboard page loads | TASK | Measure each of 7 pages with 100, 500, 1000 keywords in database |
| 10.3.4 | Benchmark LLM cache performance | TASK | Measure cache hit rate, cache lookup time, cache size growth |
| 10.3.5 | Create performance regression test | TASK | Fail if any page load > 3 seconds or full run cost exceeds budget by > 20% |

---

## Story 10.4 — Resilience Testing

| ID | Task | Type | Description |
|---|---|---|---|
| 10.4.1 | Test Fiverr selector breakage | TASK | Simulate selector changes (rename CSS classes) → verify fallback selectors activate |
| 10.4.2 | Test API rate limiting | TASK | Simulate OpenAI 429 responses → verify retry with backoff |
| 10.4.3 | Test Google Trends blocking | TASK | Simulate consecutive 429s → verify 3-strike escalation → dead letter |
| 10.4.4 | Test network timeout | TASK | Simulate Playwright timeout → verify retry and checkpoint save |
| 10.4.5 | Test database corruption recovery | TASK | Corrupt checkpoint file → verify clean restart from last valid state |
| 10.4.6 | Test mid-run crash recovery | TASK | Kill process at random stage → resume → verify data consistency |
| 10.4.7 | Test LLM malformed response | TASK | Mock LLM returning invalid JSON → verify self-correction retry |
| 10.4.8 | Create resilience test suite | TASK | Aggregate all resilience tests into a single test runner |

---

## Story 10.5 — Unit Test Coverage

| ID | Task | Type | Description |
|---|---|---|---|
| 10.5.1 | Achieve ≥ 80% unit test coverage | TASK | Run pytest --cov, identify uncovered modules, write missing tests |
| 10.5.2 | Create test fixtures | TASK | `tests/fixtures/` — Sample config, mock DB session, sample keywords, mock LLM responses, mock Playwright pages |
| 10.5.3 | Create conftest.py | TASK | Shared pytest fixtures: db_session, config, mock_llm_client, sample_keywords |
| 10.5.4 | Create mock data generators | TASK | Functions that generate realistic test data: fake gigs, fake sellers, fake scores |
| 10.5.5 | Document test strategy | TASK | `tests/README.md` — How to run tests, fixture descriptions, mocking strategy |

---

## Story 10.6 — Configuration Validation for All 9 Niches

| ID | Task | Type | Description |
|---|---|---|---|
| 10.6.1 | Validate all 9 niche configs | TASK | Each niche has: niche_id, name, depth, category_path, seed_keywords (6-8), pricing (ascending tiers) |
| 10.6.2 | Validate Tier 1 depth settings | TASK | PRD=full, Support-KB=keyword_only, Gumloop=keyword_only, MCP=feasibility |
| 10.6.3 | Validate Tier 2 depth settings | TASK | All start at keyword_only or standard, auto-promote available |
| 10.6.4 | Validate pricing across all niches | TASK | All prices positive, basic < standard < premium, within market ranges |
| 10.6.5 | Validate scoring profile weights | TASK | All 4 profiles: 11 weights sum to 1.0 |

---

## Story 10.7 — Logging and Monitoring

| ID | Task | Type | Description |
|---|---|---|---|
| 10.7.1 | Implement structured logging | TASK | Every log message includes: run_id, stage, module, timestamp |
| 10.7.2 | Implement log rotation | TASK | Daily rotation, keep 30 days, max 100MB per file |
| 10.7.3 | Implement error summary | TASK | After run: list all errors with stage, message, traceback location |
| 10.7.4 | Implement cost tracking dashboard data | TASK | Running cost total visible during long runs |

---

## Story 10.8 — Documentation

| ID | Task | Type | Description |
|---|---|---|---|
| 10.8.1 | Write comprehensive README.md | TASK | Project overview, architecture diagram, setup, configuration guide, run modes, dashboard guide |
| 10.8.2 | Write config.yaml reference | TASK | Document every config field with type, default, description, valid values |
| 10.8.3 | Write troubleshooting guide | TASK | Common errors: selector changes, API key issues, Playwright install, proxy setup |
| 10.8.4 | Write first-run checklist | TASK | Step-by-step: install → configure → init-db → first run → review results |
| 10.8.5 | Write maintenance guide | TASK | Regular tasks: update selectors, review dead letters, update pricing, add niches |

---

## Story 10.9 — First Run Validation

| ID | Task | Type | Description |
|---|---|---|---|
| 10.9.1 | Execute first full run against PRD niche | TASK | `python run.py --mode full` with only PRD niche enabled. Record all metrics |
| 10.9.2 | Validate keyword expansion | TASK | Verify ≥ 20 keywords after expansion from 6-8 seeds |
| 10.9.3 | Validate gig collection | TASK | Verify ≥ 50 gigs collected across expanded keywords |
| 10.9.4 | Validate scoring output | TASK | Verify all keywords have scores, tags assigned, rankings computed |
| 10.9.5 | Validate recommendation quality | TASK | Review 3 STRONG GO recommendations: are titles compelling? Packages sensible? Pricing realistic? |
| 10.9.6 | Validate export output | TASK | Check Excel, Markdown, JSON exports contain correct data |
| 10.9.7 | Validate dashboard rendering | TASK | Load all 7 pages, verify no errors, data displays correctly |

---

## Story 10.10 — Full 9-Niche Validation Run

| ID | Task | Type | Description |
|---|---|---|---|
| 10.10.1 | Execute full run with all 9 niches | TASK | `python run.py --mode full` with all niches. Expected: 3-6 hours |
| 10.10.2 | Record cost metrics | TASK | Total LLM cost, cache hit rate, cost per keyword, cost per niche |
| 10.10.3 | Record performance metrics | TASK | Total duration, per-stage durations, peak memory |
| 10.10.4 | Validate cross-niche consistency | TASK | Verify scoring is comparable across niches, no systematic bias |
| 10.10.5 | Review recommendations for all STRONG GO | TASK | Manual quality review of every STRONG GO recommendation |

---

## Story 10.11 — Security and Data Hygiene

| ID | Task | Type | Description |
|---|---|---|---|
| 10.11.1 | Verify no API keys in committed files | TASK | Scan codebase for leaked secrets: OPENAI_API_KEY, any passwords |
| 10.11.2 | Verify .env is gitignored | TASK | Confirm .env never committed |
| 10.11.3 | Verify data/ is gitignored | TASK | Confirm scraped data, screenshots, database not committed |
| 10.11.4 | Implement database backup script | TASK | `scripts/backup_db.py` — Copy database to timestamped backup file |

---

## Story 10.12 — Launch Readiness Checklist

| ID | Task | Type | Description |
|---|---|---|---|
| 10.12.1 | All 28 database tables created and tested | TASK | Schema validation |
| 10.12.2 | All 16 pipeline stages wired and tested | TASK | Stage chain validation |
| 10.12.3 | All 11 score calculators producing valid output | TASK | Score range validation |
| 10.12.4 | All 14 recommendation LLM tasks producing output | TASK | Task completion validation |
| 10.12.5 | All 7 dashboard pages rendering | TASK | Page load validation |
| 10.12.6 | All 5 export formats generating valid files | TASK | Export validation |
| 10.12.7 | All 8 alert types generating correctly | TASK | Alert type validation |
| 10.12.8 | Discovery engine executing cycles | TASK | Discovery validation |
| 10.12.9 | Pricing engine computing entry prices | TASK | Pricing validation |
| 10.12.10 | Playbook PDF generating | TASK | PDF generation validation |
| 10.12.11 | Checkpoint + resume working | TASK | Resilience validation |
| 10.12.12 | ≥ 80% test coverage | TASK | Coverage report |
| 10.12.13 | README and documentation complete | TASK | Documentation review |
| 10.12.14 | First full 9-niche run completed successfully | TASK | Run log review |

---

## Epic 10 Summary: 12 Stories, 56 Tasks
