# DOD — EPIC 10: Integration, Testing & Launch
# Fiverr Research System — Definitions of Done & Acceptance Criteria

---

## Story 10.1 — End-to-End Pipeline Integration

### Definition of Done
- [ ] All 16 pipeline stages wire correctly in --mode full
- [ ] Stage sequence logged with timing
- [ ] Stage failure isolation: one stage failure doesn't crash independent stages

### Acceptance Criteria
| AC ID | Criteria | Validation Method |
|---|---|---|
| AC-10.1.1 | `--mode full` executes all 16 stages in correct order | Stage sequence log test |
| AC-10.1.2 | Stage dependency validation catches missing prerequisite data | Pre-run check test |
| AC-10.1.3 | Failure in Stage 7 does not prevent Stage 8 from running (independent stages) | Failure injection test |
| AC-10.1.4 | Run summary logs: keyword_count, scored_count, strong_go_count, cost, duration | Log content test |
| AC-10.1.5 | After full run: all 28 tables have ≥ 1 row (for niche with data) | Table population test |

---

## Story 10.2 — Data Integrity Validation

### Definition of Done
- [ ] Orphan detection finds 0 orphans after clean full run
- [ ] FK integrity validated after every run
- [ ] No NaN or out-of-range score values

### Acceptance Criteria
| AC ID | Criteria | Validation Method |
|---|---|---|
| AC-10.2.1 | Orphan detection finds 0 orphans after clean full run | Post-run integrity check |
| AC-10.2.2 | Deliberately orphaning a score row → orphan detected and reported | Corruption test |
| AC-10.2.3 | No score values are NaN or outside 0-100 range | Range scan test |
| AC-10.2.4 | All STRONG GO keywords have recommendation with completeness ≥ 0.70 | Completeness check |
| AC-10.2.5 | All foreign keys resolve (no dangling references) | FK validation query |

---

## Story 10.3 — Performance Testing

### Definition of Done
- [ ] Full pipeline (1 niche, 2 keywords) < 30 minutes
- [ ] All 7 dashboard pages load in < 3 seconds
- [ ] LLM cache hit rate ≥ 50% on second identical run

### Acceptance Criteria
| AC ID | Criteria | Validation Method |
|---|---|---|
| AC-10.3.1 | Full pipeline (1 niche, 2 keywords) completes in < 30 minutes | Timing test |
| AC-10.3.2 | All 7 dashboard pages load in < 3 seconds with 500 keywords | Performance benchmark |
| AC-10.3.3 | LLM cache hit rate ≥ 50% on second identical run | Cache metric test |
| AC-10.3.4 | Peak memory usage < 2GB during full pipeline run | Memory profiling |
| AC-10.3.5 | Full 9-niche run LLM cost within $2-5 range (with cache) | Cost tracking test |

---

## Story 10.4 — Resilience Testing

### Definition of Done
- [ ] Fallback selectors activate on primary selector failure
- [ ] Kill-and-resume works: resumes from correct checkpoint
- [ ] LLM invalid JSON triggers self-correction retry

### Acceptance Criteria
| AC ID | Criteria | Validation Method |
|---|---|---|
| AC-10.4.1 | Fallback selectors activate when primary selector fails | Selector failure injection |
| AC-10.4.2 | OpenAI 429 → retry with exponential backoff, succeeds on retry | Rate limit simulation |
| AC-10.4.3 | Google Trends 3x 429 → dead letter (no crash) | Escalation simulation |
| AC-10.4.4 | Playwright timeout → retry + checkpoint save | Timeout simulation |
| AC-10.4.5 | Kill at Stage 5 → resume continues from Stage 5 checkpoint | Signal kill + resume test |
| AC-10.4.6 | LLM returns invalid JSON → self-correction retry succeeds | Malformed response mock |
| AC-10.4.7 | Corrupted checkpoint → clean restart from Stage 1 with warning | Corruption test |

---

## Story 10.5 — Unit Test Coverage

### Definition of Done
- [ ] pytest --cov reports ≥ 80% overall coverage
- [ ] tests/README.md documents all fixtures
- [ ] All test fixtures documented and usable across modules

### Acceptance Criteria
| AC ID | Criteria | Validation Method |
|---|---|---|
| AC-10.5.1 | pytest --cov reports ≥ 80% overall coverage | Coverage report |
| AC-10.5.2 | All test fixtures documented in tests/README.md | Documentation review |
| AC-10.5.3 | Mock data generators produce realistic data that passes model validation | Generator output test |
| AC-10.5.4 | conftest.py provides shared fixtures usable across all test modules | Fixture availability test |

---

## Story 10.6 — Configuration Validation

### Definition of Done
- [ ] All 9 niches load without validation errors
- [ ] All 4 scoring profiles have weights summing to 1.0
- [ ] All 9 niches have correctly ordered pricing tiers

### Acceptance Criteria
| AC ID | Criteria | Validation Method |
|---|---|---|
| AC-10.6.1 | All 9 niches load without validation errors | Config load test |
| AC-10.6.2 | PRD niche has depth="full", Support-KB has depth="keyword_only" | Depth field test |
| AC-10.6.3 | All 9 niches: basic_price < standard_price < premium_price | Price order test |
| AC-10.6.4 | All 4 scoring profiles: weight sum = 1.0 ± 0.001 | Sum test |

---

## Story 10.7 — Logging and Monitoring

### Definition of Done
- [ ] Structured logging with run_id context in every log line
- [ ] Log rotation configured for long runs
- [ ] No unhandled exceptions propagate without logging

### Acceptance Criteria
| AC ID | Criteria | Validation Method |
|---|---|---|
| AC-10.7.1 | Every log line includes run_id, stage, module, timestamp | Log format test |
| AC-10.7.2 | Log files rotate daily, old logs cleaned after 30 days | Rotation config test |
| AC-10.7.3 | Error summary at run end lists all errors with stage + traceback | Error summary test |

---

## Story 10.8 — Documentation

### Definition of Done
- [ ] README.md updated with final setup instructions
- [ ] Architecture diagram reflects final system structure
- [ ] CHANGELOG.md updated for v0.1.0 release

### Acceptance Criteria
| AC ID | Criteria | Validation Method |
|---|---|---|
| AC-10.8.1 | README contains: overview, setup, config guide, run modes, dashboard guide | Section check |
| AC-10.8.2 | config.yaml reference documents every field with type + default + description | Completeness check against ConfigLoader |
| AC-10.8.3 | Troubleshooting guide covers ≥ 10 common issues | Issue count check |
| AC-10.8.4 | First-run checklist has ≤ 10 steps, all executable in order | Step-by-step walkthrough |

---

## Story 10.9 — First Run Validation (PRD Niche)

### Acceptance Criteria
| AC ID | Criteria | Validation Method |
|---|---|---|
| AC-10.9.1 | ≥ 20 keywords after expansion from 6-8 seeds | DB count check |
| AC-10.9.2 | ≥ 50 gigs collected across keywords | DB count check |
| AC-10.9.3 | All keywords have scores + tags + rankings | Null check |
| AC-10.9.4 | ≥ 1 STRONG GO recommendation with all 14 fields populated | Completeness check |
| AC-10.9.5 | Excel export has 6 worksheets with data | File structure check |
| AC-10.9.6 | All 7 dashboard pages render without errors | Page load check |

---

## Story 10.10 — Full 9-Niche Validation Run

### Acceptance Criteria
| AC ID | Criteria | Validation Method |
|---|---|---|
| AC-10.10.1 | Run completes with status COMPLETED or COMPLETED_WITH_ERRORS (not FAILED) | RunLog status check |
| AC-10.10.2 | LLM cost within expected range ($2-5) | Cost tracking check |
| AC-10.10.3 | Duration within expected range (3-6 hours) | Duration check |
| AC-10.10.4 | ≥ 3 STRONG GO keywords across all niches | Tag count check |
| AC-10.10.5 | Manual review of STRONG GO recommendations: all titles are compelling and specific | Human review |

---

## Story 10.11 — Security and Data Hygiene

### Acceptance Criteria
| AC ID | Criteria | Validation Method |
|---|---|---|
| AC-10.11.1 | `grep -r "sk-" src/` returns 0 results (no leaked API keys) | Secret scan |
| AC-10.11.2 | .gitignore includes .env, data/, __pycache__, *.pyc | File content check |
| AC-10.11.3 | backup_db.py creates timestamped backup in data/backups/ | Backup creation test |

---

## Story 10.12 — Launch Readiness Checklist

### Acceptance Criteria (ALL must pass for launch)
| AC ID | Criteria | Status |
|---|---|---|
| AC-10.12.1 | 28 tables created ✓ | |
| AC-10.12.2 | 16 stages wired ✓ | |
| AC-10.12.3 | 11 scores producing valid output ✓ | |
| AC-10.12.4 | 14 recommendation tasks producing output ✓ | |
| AC-10.12.5 | 7 dashboard pages rendering ✓ | |
| AC-10.12.6 | 5 export formats valid ✓ | |
| AC-10.12.7 | 8 alert types working ✓ | |
| AC-10.12.8 | Discovery engine cycling ✓ | |
| AC-10.12.9 | Pricing engine computing ✓ | |
| AC-10.12.10 | Playbook PDF generating ✓ | |
| AC-10.12.11 | Checkpoint + resume working ✓ | |
| AC-10.12.12 | ≥ 80% test coverage ✓ | |
| AC-10.12.13 | Documentation complete ✓ | |
| AC-10.12.14 | First 9-niche run successful ✓ | |

---

## Epic 10 — Overall Definition of Done

The entire Fiverr Research System is LAUNCH READY when:

1. ✅ All 14 items in the Launch Readiness Checklist pass
2. ✅ First full 9-niche run completes successfully with valid data in all tables
3. ✅ Dashboard renders all 7 pages with real data from the validation run
4. ✅ Manual review of STRONG GO recommendations confirms quality
5. ✅ All tests pass (unit + integration + performance + resilience)
6. ✅ Documentation is complete and accurate
7. ✅ No security issues (no leaked keys, data properly gitignored)
