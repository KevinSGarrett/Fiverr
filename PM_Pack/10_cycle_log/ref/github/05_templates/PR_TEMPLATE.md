# Pull Request Template
# Fiverr Research System — Standard PR Body Template

---

## Purpose

This template is used for EVERY pull request. It is placed at `.github/PULL_REQUEST_TEMPLATE.md` in the repo. When an agent creates a PR, GitHub auto-populates the body with this template. The agent fills in each section.

---

## Template Content

```markdown
## What
<!-- 1-2 sentences: what does this PR do? -->


## Why
<!-- Link to the issue/story this implements. Use "Closes #XX" to auto-close. -->
Closes #

## How
<!-- Key implementation decisions, approach, or patterns used. -->


## Testing
<!-- What tests were added or modified? How was this verified? -->
- [ ] Unit tests added for new functionality
- [ ] Existing tests still pass
- [ ] Manual verification performed (describe if applicable)

## Screenshots / Logs
<!-- If this changes UI or produces output, paste screenshots or log snippets. -->
N/A

## Checklist
<!-- All items must be checked before merge. -->
- [ ] PR title follows conventional format: `type(scope): description`
- [ ] All required labels applied (type, priority, scope, risk)
- [ ] Code follows project style (Ruff passes)
- [ ] Type annotations added (Mypy passes)
- [ ] Tests added with ≥80% coverage maintained
- [ ] No secrets, API keys, or sensitive data in diff
- [ ] Spec compliance verified against project-pack/ docs
- [ ] No unrelated changes included

## Risk Assessment
<!-- Which risk tier does this PR fall into? See 06_risk_management/RISK_TIERS.md -->
- [ ] `risk:low` — Tests, docs, config, minor fixes
- [ ] `risk:medium` — New feature within established patterns
- [ ] `risk:high` — New workflow, scoring formula, LLM prompt
- [ ] `risk:critical` — Schema migration, orchestrator, security

## Agent
<!-- Which agent created this PR? -->
- [ ] Agent 1 — Infrastructure
- [ ] Agent 2 — Collection
- [ ] Agent 3 — Analysis/Scoring
- [ ] Agent 4 — Dashboard/UX
```

---

## Template Rules

### Required Sections (CI enforces)
| Section | Min Content | Validation |
|---|---|---|
| What | ≥ 10 characters | pr-checks workflow |
| Why | Must contain `#` (issue link) OR explanation | pr-checks workflow |
| Checklist | At least 4 items checked | Convention (not enforced) |

### Section-Specific Guidance

**What:** Be precise. "Implements DemandScoreCalculator" not "Added stuff."

**Why:** Always link the issue. Use `Closes #47` for auto-close, or `Relates to #47` if the PR is part of a larger story.

**How:** Explain non-obvious decisions. If you chose a specific algorithm, data structure, or pattern — say why. This section helps future agents understand intent.

**Testing:** List specific test files and what they cover. "Added 12 tests in test_scoring.py" not just "Tests added."

**Screenshots / Logs:** Required for dashboard/UI PRs. Optional for backend-only PRs. Include Streamlit screenshots, CLI output, or log snippets.

---

## Examples

### Good PR Body (Feature)
```markdown
## What
Implements the DemandScoreCalculator (Story 4.1) with all 4 components:
log-scaled Fiverr count, autocomplete position, Google Trends slope, and Reddit intent.

## Why
Closes #47 — Part of Epic 04 (Scoring Engine). Demand score is the first
of 11 calculators required before the composite final score can be computed.

## How
- Used log10 scaling for Fiverr result count (handles range 0–50,000+)
- Autocomplete position maps linearly: position 1=100, 10=10, absent=0
- Trend slope thresholds from DEMAND_SCORE.md spec (>0.5=100, <-0.5=0)
- Reddit signal normalized to 0-100 from raw intent count
- All weights configurable via weight profiles (spec Section 5)

## Testing
- 12 unit tests in tests/unit/test_scoring.py::TestDemandScore
- Each component tested independently
- Composite score tested with all components present
- Edge cases: null inputs, zero results, maximum results, missing trend data
- Coverage: demand.py at 94%

## Screenshots / Logs
N/A (backend scoring — no UI)

## Checklist
- [x] PR title follows conventional format
- [x] All required labels applied
- [x] Code follows project style (Ruff passes)
- [x] Type annotations added (Mypy passes)
- [x] Tests added with ≥80% coverage maintained
- [x] No secrets or sensitive data
- [x] Spec compliance: project-pack/05_scoring/DEMAND_SCORE.md
- [x] No unrelated changes

## Risk Assessment
- [x] `risk:high` — New scoring formula with 4 mathematical components

## Agent
- [x] Agent 3 — Analysis/Scoring
```

### Good PR Body (Fix)
```markdown
## What
Fixes null pointer crash when gig has no package pricing data.

## Why
Closes #63 — GigDetail workflow crashes when Fiverr returns a gig page
without the standard 3-tier package section (happens for ~2% of gigs).

## How
- Added null check in gig_detail.py before accessing packages array
- Returns empty PackageList with is_custom=True flag when no packages found
- Existing downstream code already handles empty PackageList gracefully

## Testing
- Added 3 tests for null/empty package scenarios
- Verified against 5 real gig URLs that trigger this edge case

## Checklist
- [x] PR title follows conventional format
- [x] All required labels applied
- [x] Ruff passes
- [x] Mypy passes
- [x] Tests added
- [x] No secrets
- [x] No unrelated changes

## Risk Assessment
- [x] `risk:medium` — Touches collection workflow but change is defensive

## Agent
- [x] Agent 2 — Collection
```
