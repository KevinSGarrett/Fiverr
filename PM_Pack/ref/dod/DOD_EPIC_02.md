# DOD — EPIC 02: Collection Engine
# Fiverr Research System — Definitions of Done & Acceptance Criteria

---

## Story 2.1 — Playwright Session Manager

### Definition of Done
- [ ] Browser launches in persistent context with reusable cookies
- [ ] Auth detection correctly identifies logged-in vs. anonymous state
- [ ] Human-event simulation produces non-robotic browsing patterns
- [ ] Graceful shutdown saves browser state

### Acceptance Criteria
| AC ID | Criteria | Validation Method |
|---|---|---|
| AC-2.1.1 | `SessionManager.start()` launches Chromium and returns a Page object | Integration test |
| AC-2.1.2 | Second `start()` call reuses the same browser profile (cookies persist) | Check cookie file existence between calls |
| AC-2.1.3 | `is_authenticated()` returns True when logged in, False when anonymous | Manual test + mock test |
| AC-2.1.4 | Mouse movement events are injected between navigation actions | Playwright trace log inspection |
| AC-2.1.5 | `stop()` closes browser cleanly without orphan processes | Process check after stop |
| AC-2.1.6 | Request interception blocks analytics/font requests when configured | Network log test — blocked URLs not fetched |

---

## Story 2.2 — Fiverr Selectors

### Definition of Done
- [ ] All 30+ selectors are defined with primary + 2 fallback patterns each
- [ ] Selector validation script reports match rate against live Fiverr page

### Acceptance Criteria
| AC ID | Criteria | Validation Method |
|---|---|---|
| AC-2.2.1 | Each selector has at least 2 fallback patterns (comma-separated CSS) | Code review |
| AC-2.2.2 | Running selector validation against a live search results page matches ≥ 80% of selectors | Manual integration test (quarterly) |
| AC-2.2.3 | Selectors are organized into named groups: SEARCH, GIG_DETAIL, SELLER_PROFILE, VISUAL | Code structure review |

---

## Story 2.3 — Pacing Manager

### Definition of Done
- [ ] Delays fall within specified ranges for each source
- [ ] Adaptive escalation triggers on 429/timeout responses
- [ ] Jitter varies delays by ±20%
- [ ] Cooldown pauses after 50 requests

### Acceptance Criteria
| AC ID | Criteria | Validation Method |
|---|---|---|
| AC-2.3.1 | 100 Fiverr search delays: mean between 3.0-5.0s, all between 2.4-6.0s (±20% jitter) | Statistical test on delay samples |
| AC-2.3.2 | After simulated 429, next delay is ≥ 1.5x previous delay | Unit test with mock |
| AC-2.3.3 | After 3 consecutive Google Trends 429s, job moves to DEAD_LETTER | State machine test |
| AC-2.3.4 | After 50 requests to same source, a pause of 30-60s occurs | Counter + delay measurement test |

---

## Stories 2.4–2.5 — Queue Processor & Checkpoint System

### Definition of Done
- [ ] Jobs process in priority order (HIGH > STANDARD > LOW)
- [ ] Failed jobs retry up to 3 times then dead-letter
- [ ] Checkpoint saves atomically every 50 records
- [ ] Resume from checkpoint skips already-completed jobs

### Acceptance Criteria
| AC ID | Criteria | Validation Method |
|---|---|---|
| AC-2.4.1 | 3 HIGH + 3 LOW jobs: all HIGH process before any LOW | Order tracking test |
| AC-2.4.2 | Job that fails 3 times: status becomes DEAD_LETTER with error_message populated | Failure injection test |
| AC-2.4.3 | Checkpoint file written at records 50, 100, 150 during a 150-record collection | File timestamp test |
| AC-2.4.4 | Kill process at record 75, resume → processing starts at record 51 (last checkpoint) | Integration test with signal |
| AC-2.4.5 | Checkpoint file is valid JSON after simulated crash during write (atomic rename) | Corruption test |
| AC-2.4.6 | Checkpoint file is deleted after successful run completion | Cleanup test |

---

## Stories 2.7–2.13 — All Collection Workflows

### Definition of Done (per workflow)
- [ ] Workflow produces correct data for all fields specified in SCHEMA.md
- [ ] Pacing delays are respected between requests
- [ ] Errors are caught, logged, and don't crash the pipeline
- [ ] Checkpoint is triggered at configured interval
- [ ] Data is UPSERT-ed (update existing, insert new)

### Acceptance Criteria — Workflow-Specific
| AC ID | Workflow | Criteria | Validation Method |
|---|---|---|---|
| AC-2.7.1 | Keyword Expansion | Autocomplete returns 5+ suggestions for "AI SaaS" keyword | Integration test |
| AC-2.7.2 | Keyword Expansion | Duplicate keywords (Jaccard > 0.65) are not inserted | Dedup test |
| AC-2.8.1 | Fiverr Search | Search for "python automation" returns ≥ 1 gig card | Integration test |
| AC-2.8.2 | Fiverr Search | Pagination follows ≤ max_pages links | Page count assertion |
| AC-2.8.3 | Fiverr Search | total_result_count is parsed as integer from header text | Regex test |
| AC-2.9.1 | Gig Detail | Package extraction returns 3 tiers with price, deliverables, delivery_days | Data completeness test |
| AC-2.9.2 | Gig Detail | FAQ extraction returns list of {question, answer} dicts | Structure test |
| AC-2.9.3 | Gig Detail | Gallery count matches visible gallery items | Count test |
| AC-2.10.1 | Seller Profile | Bio text extracted with > 0 characters for active sellers | Non-empty test |
| AC-2.10.2 | Seller Profile | Response time parsed as numeric hours value | Type test |
| AC-2.10.3 | Seller Profile | Same seller appearing in multiple keywords creates ONE seller row | Dedup test |
| AC-2.11.1 | Google Trends | 12-month data returned with ≥ 10 data points | Array length test |
| AC-2.11.2 | Google Trends | Slope classified as RISING/STABLE/DECLINING correctly | Threshold test |
| AC-2.11.3 | Google Trends | 3-strike escalation delays measured at 10s, 15s, 22.5s | Delay measurement test |
| AC-2.12.1 | Reddit Signals | Search returns post count for relevant subreddits | Non-zero count for known active subreddits |
| AC-2.12.2 | Reddit Signals | Intent phrases ("looking for", "need someone") detected in sample posts | Pattern match test |
| AC-2.13.1 | Autocomplete | Position 1-10 recorded for keywords present in autocomplete | Range test |

---

## Story 2.14 — Stage Orchestration Wiring

### Acceptance Criteria
| AC ID | Criteria | Validation Method |
|---|---|---|
| AC-2.14.1 | `--mode full` executes Stages 2, 3, 4, 5, 6 in order | Log order inspection |
| AC-2.14.2 | `--mode collect-only` executes Stages 2-6 and stops (no scoring) | Stage count assertion |
| AC-2.14.3 | Each stage's duration_seconds is recorded in run_log | DB assertion |
| AC-2.14.4 | Stage 4 failure does not prevent Stage 5 from running | Error injection test |

---

## Story 2.16 — End-to-End Collection Smoke Test

### Acceptance Criteria
| AC ID | Criteria | Validation Method |
|---|---|---|
| AC-2.16.1 | After full collection on 1 niche (2 keywords): keywords table has ≥ 10 rows, gigs table has ≥ 5 rows, sellers table has ≥ 3 rows | DB count assertions |
| AC-2.16.2 | external_signals table has Google Trends and Reddit entries for the test niche | DB filter test |
| AC-2.16.3 | No request was made faster than the minimum pacing delay | Timestamp log analysis |
| AC-2.16.4 | Checkpoint file was created and cleaned up | File lifecycle test |

---

## Epic 02 — Overall Definition of Done

The Collection Engine epic is DONE when:

1. ✅ `python run.py --mode collect-only` runs Stages 2-6 for all 9 niches without crashing
2. ✅ keywords, gigs, sellers, search_results, external_signals tables are populated
3. ✅ Pacing is respected (no burst requests, adaptive escalation works)
4. ✅ Checkpoint + resume works after simulated crash
5. ✅ All 15 collection workflow tests pass
6. ✅ Dead letter queue captures permanently failed jobs with error details
