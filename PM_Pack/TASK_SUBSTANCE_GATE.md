# TASK_SUBSTANCE_GATE.md
# Fiverr Research System — Task Substance Gate
# Created: 2026-06-09 (PM Governance Correction)
# MANDATORY: Every task in every agent prompt must pass this gate before inclusion.

---

## PURPOSE

This gate exists because the PM has been generating hundreds of tasks per cycle that
are numerically large but do not advance production readiness. The gate prevents:
- filler tasks counted as LARGE/XLARGE/XXLARGE
- repeated verification tasks stacked across agents
- documentation updates counted as implementation
- smoke checks called XXLARGE
- tasks that exist only to meet line/task floor counts

---

## SECTION 1: CLASSIFICATION MATRIX

Every task receives a score from 0–5 in six categories.

### Category 1: Production Outcome Score
| Score | Meaning |
|---|---|
| 0 | No production outcome — purely administrative |
| 1 | Indirect admin/support only (file move, rename) |
| 2 | Minor support (update hydration, add comment) |
| 3 | Useful but not production-moving (unit test for existing behavior) |
| 4 | Direct production capability or blocker reduction |
| 5 | Direct end-to-end production-grade advancement |

### Category 2: Complexity / Substance Score
| Score | Meaning |
|---|---|
| 0 | Filler (repetition, placeholder text, line padding) |
| 1 | Trivial (1–3 line check, single import verify) |
| 2 | Small (4–8 line check with a real assertion) |
| 3 | Medium (10–20 lines implementing or verifying one behavior) |
| 4 | Large (20–40 lines implementing meaningful behavior) |
| 5 | XLARGE/XXLARGE (40+ lines with real integration or E2E flow) |

### Category 3: Integration Depth Score
| Score | Meaning |
|---|---|
| 0 | Isolated note or document only |
| 1 | Isolated file (no imports, no dependencies) |
| 2 | One module only (no cross-module connections) |
| 3 | Module + tests (implements + verifies) |
| 4 | Multi-module integration (connects two subsystems) |
| 5 | End-to-end workflow integration |

### Category 4: Evidence Strength Score
| Score | Meaning |
|---|---|
| 0 | No evidence (assertion only, no artifact) |
| 1 | Statement only (says it works, no proof) |
| 2 | File changed only (code changed but untested) |
| 3 | Test/command evidence (test passes or command succeeds) |
| 4 | Integration evidence (two systems connected and verified) |
| 5 | Live/E2E evidence (real data through real pipeline) |

### Category 5: Novelty / Non-Duplication Score
| Score | Meaning |
|---|---|
| 0 | Duplicate (identical or near-identical to another task in this cycle) |
| 1 | Repeated check (same type of check as prior task in this prompt) |
| 2 | Minor variation (similar logic, slightly different assertion) |
| 3 | Related but useful (same domain, different behavior tested) |
| 4 | New meaningful work (new function, new behavior, new integration) |
| 5 | New critical production work (new E2E capability) |

### Category 6: End-to-End Readiness Score
| Score | Meaning |
|---|---|
| 0 | No impact on E2E production readiness |
| 1 | Very indirect (may help someday) |
| 2 | Minor readiness support (prerequisite of a prerequisite) |
| 3 | Prerequisite readiness (directly needed before production) |
| 4 | Direct readiness advancement (closes or proves a production path) |
| 5 | Closes or proves a production-grade path with evidence |

---

## SECTION 2: CLASSIFICATION THRESHOLDS

### SMALL Task
Total score below 16 OR any core category below 3.
SMALL tasks may appear in prompts but must NOT be counted toward the 55 LARGE-XXLARGE minimum.

### MEDIUM Task
Total score 16–21.
MEDIUM tasks may appear in prompts but must NOT be counted toward the 55 LARGE-XXLARGE minimum
unless explicitly justified as supporting a LARGE task directly above.

### LARGE Task
ALL of the following must be true:
- Total score 22–25
- Production Outcome Score >= 4
- Evidence Strength Score >= 3
- End-to-End Readiness Score >= 3
- Not a duplicate of any other task in this prompt
- Has a durable artifact (code, test, migration, CLI behavior, etc.)
- Has explicit acceptance criteria

### XLARGE Task
ALL LARGE criteria PLUS at least two of:
- Touches multiple files or modules
- Integrates at least two subsystems
- Closes a full story acceptance criterion
- Adds meaningful tests across more than one behavior
- Produces user/operator-visible functionality
- Reduces a major blocker
- Converts a stubbed path into a working path

### XXLARGE Task
ALL XLARGE criteria PLUS at least one of:
- Proves a full end-to-end workflow
- Closes a major production gate (G-D, live collection, live data)
- Makes a major user-facing capability usable
- Enables a repeated unattended run
- Validates live data through downstream outputs
- Advances E2E production readiness score by a measurable amount

---

## SECTION 3: HARD REJECTION RULES

A task is AUTOMATICALLY REJECTED from LARGE/XLARGE/XXLARGE classification if ANY of these are true:

- Production Outcome Score < 4
- Evidence Strength Score < 3
- End-to-End Readiness Score < 3
- It is a duplicate of another task in the same prompt
- It has no durable artifact
- It has no explicit acceptance criteria
- It exists primarily to satisfy task count or line count

---

## SECTION 4: TASK TYPES THAT ARE NOT LARGE BY DEFAULT

The following task types require extra justification to be classified LARGE:
(they may qualify if they close a major gate, but usually they do not)

| Task type | Default classification | Allowed to be LARGE if... |
|---|---|---|
| Verify file exists | SMALL | Never — use as part of a larger task |
| Check import | SMALL | Only if first-time integration proof |
| Run smoke test | SMALL | Only if it proves a new E2E path |
| Update hydration header | SMALL | Only if it corrects an active governance blocker |
| Post Jira note | SMALL | Never alone |
| Confirm no migration | SMALL | As part of a larger gate |
| Check line count | SMALL | Never |
| Confirm config value | SMALL | As part of a larger gate |
| Repeat golden parity | SMALL/MEDIUM | Only first time per session |
| Run full test suite | SMALL/MEDIUM | Only after major new additions |
| Write summary text | SMALL | Never |
| Update placeholder | SMALL | Only if it closes an active cycle log blocker |
| Confirm branch | SMALL | Never alone |
| Add governance note | SMALL | Never alone |
| Add comment to Jira | SMALL | Never alone |

---

## SECTION 5: REQUIRED TASK MINIMUM MIX

For any cycle claiming 55 LARGE-XXLARGE tasks per agent (330+ total):

| Task type | Required minimum |
|---|---|
| Direct production implementation | >= 70% of all tasks |
| Verification-only tasks | <= 15% of all tasks |
| Documentation/governance-only | <= 10% of all tasks |
| Integration, E2E, live validation, or production acceptance | >= 20% of all tasks |
| Tasks targeting the biggest current production blockers | >= 10% of all tasks |

If a cycle cannot meet this mix, the PM must not claim the 55 LARGE-XXLARGE minimum is satisfied.

---

## SECTION 6: REQUIRED TASK MATRIX IN EVERY PROMPT

Every prompt must include a Task Substance Matrix header block with:

```
TASK SUBSTANCE MATRIX
| ID | Title | Claimed Size | Prod Outcome | Complexity | Integration | Evidence | Novelty | E2E | Total | Accepted Size | Artifact | Acceptance Criteria |
```

No task may appear in the prompt without an accepted size from this matrix.

---

## SECTION 7: ACCEPTED EXAMPLES

### LARGE (passes)
- Implement generate_playbook() that consumes a scored Recommendation ORM object and produces
  a 5-section structured dict. Tests for empty-state, full-data, and error-state. 35 lines.
  [Production: 4, Complexity: 4, Integration: 4, Evidence: 3, Novelty: 4, E2E: 3 = 22 PASS]

- Add run.py playbook command that calls generate_playbook(), exports Markdown to stdout,
  and exports PDF to file. End-to-end CLI path. 25 lines + 5 test cases.
  [Production: 4, Complexity: 4, Integration: 4, Evidence: 4, Novelty: 4, E2E: 4 = 24 PASS]

### XLARGE (passes)
- Build playbook generation from Recommendation row → Playbook object → Markdown/PDF export
  with full round-trip tests (empty-state, STRONG_GO, CONDITIONAL_GO). 80 lines, 2 modules.
  [Production: 4, Complexity: 5, Integration: 4, Evidence: 4, Novelty: 4, E2E: 4 = 25 XLARGE]

### XXLARGE (passes)
- Validate first live collection run for one niche: live Fiverr scrape → DB persistence →
  scoring trigger → recommendation generated → playbook output → dashboard shows live data.
  End-to-end with evidence artifact. Closes live data path.
  [Production: 5, Complexity: 5, Integration: 5, Evidence: 5, Novelty: 5, E2E: 5 = 30 XXLARGE]

### REJECTED (fails)
- "Verify playbook.html exists" → SMALL [Production: 1, Evidence: 1, E2E: 0] REJECTED
- "Run golden parity check" (3rd time this cycle) → SMALL [Novelty: 0] REJECTED
- "Update HYDRATION_HEADER.md with C074 state" → SMALL alone [Production: 2] REJECTED
- "Check that scrapfly=false" (repeated from 5 prior tasks) → SMALL [Novelty: 0] REJECTED
- "Write A.md report" → SMALL [Production: 1, Evidence: 1, E2E: 0] REJECTED
