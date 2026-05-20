# CODEX REVIEW DISPOSITION PROTOCOL
# Added: Cycle 005 — Permanent PM/GitHub Governance Rule

## Purpose

Codex review comments are a required PR review input for this project. They are not automatically accepted and they are not automatically ignored. The Cursor agent assigned as Integration/GitHub Steward must review every Codex review, decide whether it is legitimate, fix or formally disposition it, reply in the PR, and resolve the thread only after the disposition is complete.

## Binding Rule

No cycle PR may merge into `develop` while any Codex review thread is unresolved, unanswered, or unclassified. No release PR may merge into `main` while any prior cycle PR contains unresolved Codex feedback.

## Required Review Sources

For every PR, the Integration/GitHub Steward must inspect:

1. PR conversation comments.
2. PR review submissions.
3. Inline review threads.
4. Codex-authored comments from `chatgpt-codex-connector` or any future Codex bot account.
5. GitHub status checks and workflow runs.
6. Codecov comment/status/report.

## Codex Disposition Categories

Each Codex item must be labeled in the PR reply using exactly one of these categories:

| Category | Meaning | Required Action |
|---|---|---|
| `VALID_FIXED` | Codex identified a real issue and the agent fixed it. | Commit fix, add/extend tests, reply with fix summary, resolve thread. |
| `VALID_DEFERRED_BLOCKER` | Codex identified a real issue that cannot safely be fixed in the current PR. | Do not merge; create Jira ticket; leave thread unresolved or convert PR to draft. |
| `VALID_DEFERRED_NONBLOCKING` | Codex identified a real issue, but it is not in this PR scope and is safe to defer. | Create Jira ticket, reply with reason, PM approval required before resolving. |
| `NOT_APPLICABLE` | Codex comment does not apply to current code/path after review. | Reply with evidence, PM approval required before resolving. |
| `FALSE_POSITIVE` | Codex suggestion is wrong or would make code worse. | Reply with evidence and tests, PM approval required before resolving. |
| `DUPLICATE` | Same issue is already tracked by another comment or ticket. | Link duplicate thread/ticket, resolve only after canonical item is handled. |

## Required Reply Format

Every Codex thread must receive a reply in this format before it is resolved:

```markdown
Codex disposition: <CATEGORY>

Decision: <1-3 sentence decision>

Evidence:
- File(s) reviewed: `<path>`
- Test(s) added/run: `<commands>`
- Commit(s): `<sha or pending local commit>`

Resolution:
- <fixed / deferred with Jira key / ignored with reason>
```

## Fix Requirements

When the disposition is `VALID_FIXED`, the agent must:

1. Implement the fix in the smallest safe scope.
2. Add a regression test that fails before the fix and passes after the fix.
3. Run targeted tests for the changed file.
4. Run full PR checks before final merge readiness.
5. Reply to the Codex thread with the required format.
6. Resolve the review thread after the fix commit is pushed and checks pass.

## Ignore Requirements

When the disposition is `FALSE_POSITIVE`, `NOT_APPLICABLE`, or `VALID_DEFERRED_NONBLOCKING`, the agent must provide evidence, not opinion. Acceptable evidence includes:

- Existing tests covering the scenario.
- New tests proving the code is correct.
- Source code path showing the concern is impossible.
- Product/PM decision documented in the PM pack or Jira.

## Merge Gate

The Integration/GitHub Steward must block merge if:

- Any Codex review thread is unresolved.
- Any Codex thread lacks a disposition reply.
- Any `VALID_FIXED` item lacks a regression test.
- Any `VALID_DEFERRED_BLOCKER` exists.
- PM has not approved a `FALSE_POSITIVE`, `NOT_APPLICABLE`, or `VALID_DEFERRED_NONBLOCKING` disposition.

## Current Cycle 005 Application

PR #3 has two Codex threads that the PM reviewed as legitimate:

1. `src/orchestrator.py` forwards non-positive `sample_size` as `max_candidates`, making the intended uncapped dry-run path fail downstream.
2. `src/collection/gig_detail.py` uses a `data-testid` extraction regex that can stop at the first child closing tag and truncate nested markup.

Cycle 005 must fix both or keep PR #3 blocked.


## Cycle 006 Update — Outdated Threads Still Require Review

A Codex thread being marked outdated does not automatically mean it can be ignored. The Integration/GitHub Steward must inspect the current target branch and answer this question: does the underlying defect still exist? If yes, the item remains a blocker even if the original review thread is outdated or attached to a merged PR.

Required disposition for outdated threads:

- `OUTDATED_FIXED`: underlying issue no longer exists and the fix is covered by tests.
- `OUTDATED_STILL_VALID`: underlying issue still exists and must be fixed in a follow-up PR before related work is considered complete.
- `OUTDATED_FALSE_POSITIVE`: underlying issue does not exist and the reason is documented.

For `OUTDATED_STILL_VALID`, create or link a Jira task, add a GitHub PR/comment reference, and require a follow-up PR with regression tests.


## Cycle 007 Update — Fixed-by-Later-Commit Threads Still Need Disposition

If a Codex review thread is opened on an earlier commit and later commits appear to fix it, the Integration/GitHub Steward still must reply to that exact thread with a formal disposition and resolve it before merge. A green CI run is not a substitute for review-thread disposition.

Cycle 007 example: PR #5 has a Codex P1 thread about Codecov auth. The current workflow head uses `codecov/codecov-action@v5` with `${{ secrets.CODECOV_TOKEN }}` and a deterministic `codecov/project` job, so the item may be `VALID_FIXED`; however, it remains a merge blocker until a disposition reply is posted and the thread is resolved or a blocker is recorded.
