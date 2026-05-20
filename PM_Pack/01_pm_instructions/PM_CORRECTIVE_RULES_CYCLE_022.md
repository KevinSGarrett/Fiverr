# PM CORRECTIVE RULES — CYCLE 022
# Date: 2026-05-18
# Issue: PRs #24 and #25 merged with codecov/patch failing.
#        Codex review threads not dispositioned or resolved.

---

## What Went Wrong

### Problem 1: codecov/patch treated as non-blocking

PR #24 and PR #25 were merged while codecov/patch showed FAIL. Agent D reports
described it as "non-blocking" — this was wrong. codecov/patch failing means new
code added in the PR has less than 90% coverage. This violates the stated coverage
gate of the project (PR_CHECKS_CODECOV_PROTOCOL.md).

### Problem 2: Codex review threads not dispositioned

Cycle 020 PR #24 and Cycle 019 PR #23 had Codex findings that were "fixed" but
the disposition reply + resolve protocol was not followed for non-VALID_FIXED threads.
Cycle 021 PR #25 had 0 Codex findings, which is acceptable — but the protocol for
what to do when 0 findings are present was also not clearly documented.

---

## New Mandatory Rules (Permanent, Cycle 022+)

### R-085: codecov/patch is a hard merge blocker

codecov/patch failing BLOCKS the merge. The agent must:
1. Run targeted coverage: python -m pytest --cov=[changed_files] --cov-report=term-missing
2. Add tests for every uncovered line in new code
3. Push the tests
4. Wait for codecov/patch to pass
5. Then merge

This rule overrides any previous language calling codecov/patch "non-blocking."

### R-086: Codex zero-findings must be explicitly confirmed

When 0 Codex threads exist on a PR, Agent D must still confirm this in their report:
"Codex review check: 0 threads found via gh api graphql reviewThreads query.
No disposition required."

This prevents agents from skipping the check entirely because they assume there are none.

### R-087: Codex disposition is mandatory for every thread found

For every Codex thread (if any found):
- Query: gh api graphql -f query='{ repository(owner:"KevinSGarrett",name:"Fiverr") {
    pullRequest(number:N) { reviewThreads(first:50) { nodes { id isResolved comments(first:5)
    { nodes { author { login } body } } } } } } }'
- Classify each thread using the 6 categories in CODEX_REVIEW_DISPOSITION_PROTOCOL.md
- VALID_FIXED: fix + test + push + CI recheck + reply + resolve
- All others: evidence reply + PM approval note + resolve
- No thread may be left unresolved at merge time

### R-088: Agent D final merge checklist is mandatory in every report

Agent D MUST include the complete checklist from GITHUB_RULES.md Rule G-004
in their report AND in the PR freeze comment. A PR cannot be recommended for
merge without this checklist filled in with explicit PASS/FAIL values.

### R-089: PM must verify codecov/patch status before issuing next cycle prompts

Before issuing new cycle prompts, the PM must check if any prior-cycle PR has
outstanding codecov/patch failures and document the status.

---

## Applied to Cycle 022

All Cycle 022 agent prompts must include:
- The Rule G-004 checklist verbatim in Agent D's steward section
- Explicit codecov/patch test requirements in the completion standard
- The Codex disposition query command in Agent D's tasks
- A requirement that codecov/patch shows PASS before merge

Cycle 022 must also add patch-coverage tests for any code from PRs #24/#25 that
is still below 90% patch coverage on the develop branch.
