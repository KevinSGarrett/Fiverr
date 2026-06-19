# GitHub Repository Strategy — 24/7 Autonomous Operation

**Status:** canonical · **Owner:** PM (Claude) · **Enforced by:** `automation/repo_janitor.py`, `automation/branch_guard.py`, `automation/merge_gate.py`, `automation/codex_review_gate.py`, CI
**Audience:** every role that touches the repo — the PM, the six Cursor agents, the in‑between Codex reviewer, and the cycle‑report writers.

This document is the single source of truth for how the repository is kept clean while the cycle runner operates unattended around the clock. It exists because the repo drifted to **40 local branches / 21 stashes / 9 worktrees** despite an already‑documented branching strategy, branch protection, and a hygiene checklist. The lesson: **policy that depends on a human running it never runs in a 24/7 system.** Everything here is therefore either automated or assigned to a specific automated role.

---

## 1. Root‑cause analysis (why the repo drifted)

| # | Cause | Evidence | Fix |
|---|-------|----------|-----|
| 1 | **Cleanup was a manual weekly human task** | `ref/github/08_hygiene/HYGIENE_CHECKLIST.md` lists branch/stash cleanup under *Weekly Hygiene — Human Operator — run every Monday* | `repo_janitor.py` performs it automatically |
| 2 | **`delete_branch_after_merge` only removes the *remote* branch** | `github_policy.yml: merge.delete_branch_after_merge: true` | janitor prunes *local* merged branches too |
| 3 | **Squash‑merged cycle branches are invisible to `git branch --merged`** | `github_policy.yml: merge.method: squash` — squash creates a new commit, not an ancestor | janitor consults merged‑PR head branches via `gh` |
| 4 | **Generated artifacts were committed, then perpetually dirty** | `PM_Pack/automation/ref_catalogs/*.json` tracked before being ignored | untrack + `.gitignore` (see §4); agents never `git add` generated files |
| 5 | **Per‑cycle Agent‑A preserve/temp/quarantine stashes never cleaned** | 21 stashes spanning cycles 012–084 | janitor drops stale auto‑stashes (allow‑list + age) |
| 6 | **Manual task worktrees never removed** | 9 worktrees (merges, stage tests, verification) | janitor removes obsolete non‑CI worktrees |
| 7 | **Code reached `develop` without passing the lint gate** | 43 ruff errors sat on `develop` from a prior merge, blocking every later PR | branch protection + the lint gate must be required and green before merge |
| 8 | **Codex review threads re‑open on every push → gate fails** | `codex_review_gate.py` blocks while any thread is unresolved & not outdated | explicit *address‑and‑resolve* loop (see §8.3) |
| 9 | **Sentinel/ICV runs pollute real cycle reports** | `CYCLE_084_AGENT_A.md` repeatedly gained an `## ICV Verification Result` block (SCRUM‑999, "Feature X", "echo OK") | reports are append‑once; ICV sentinel output must not target tracked reports (see §8.4) |
| 10 | **CRLF line endings create phantom diffs** | many files show full‑file diffs that vanish under `--ignore-cr-at-eol` | `.gitattributes` normalization (see §11) |

---

## 2. Branch lifecycle (the only sanctioned flow)

```
develop ──┬─ create cycle/<NNN>/integration ─ agents commit here ─ open PR ─┐
          │                                                                  │
          │                      CI gates (lint, type, tests, smoke,         │
          │                      codecov, codex-review-gate, merge_gate)     │
          │                                                                  ▼
          └──────────────────────── squash‑merge ──────── delete REMOTE branch (auto)
                                                              │
                                              repo_janitor prunes LOCAL branch
                                              + any remote branch the auto‑delete missed
main ← release‑gated promotion only (never auto, never direct push)
```

**Rules**
- The **only** long‑lived branches are `main` (production) and `develop` (integration).
- The **only** working branches are `cycle/<NNN>/integration` (one per cycle) and the three CI‑runner branches under `C:/actions-runner/_work/**` (managed by the self‑hosted runner — **never touched by anyone**).
- **No ad‑hoc branches.** Snapshot/experiment/rebase branches are not created during autonomous operation. If a one‑off branch is ever needed, it is deleted in the same session that created it.
- Branch names match `^cycle/\d+/integration$`. `branch_guard.assert_cycle_branch` enforces this before work begins.
- Protected branches (`main`, `master`, `develop`) are never force‑pushed, never directly committed to, never deleted (`github_policy.yml: blocked_operations`).

---

## 3. Commit hygiene

- **Always stage explicit paths**: `git add <path> <path>`. **Never** `git add .`, `git add -A`, or `git add -u`. This is the single most important rule for preventing generated‑file and sentinel pollution.
- One logical change per commit; conventional‑commit subject (`feat`, `fix`, `chore`, `docs`, …).
- The working tree must be **clean** at the end of every agent turn and before every report (`branch_guard.assert_clean_working_tree`).
- Never commit secrets, tokens, `storage_state.json`, or anything matched by `.gitignore`.

---

## 4. Ignored‑artifact policy (generated files are never tracked)

Generated at runtime → **must be git‑ignored, never committed**:

- `PM_Pack/automation/ref_catalogs/*.json` (cycle_reports, docs_architecture, pm_pack_automation, pm_pack_ref catalogs)
- `runs/` (runtime run state)
- `docs/cycle_reports/CYCLE_*_SYNTHESIS.md`, `docs/cycle_reports/CYCLE_*_NEXT_CYCLE_DIRECTIVES.md`
- `PM_Pack/automation/post_cycle_reviews/current_run/`

If a generated file is found tracked: `git rm --cached <path>` and add it to `.gitignore` in the same commit (this is exactly how the `ref_catalogs` recurrence was fixed). Agents and the catalog builder must regenerate these on disk but never stage them.

---

## 5. Stash policy

- Stashes are **transient**. Auto‑created preflight/preserve/temp/quarantine stashes are owned by automation and garbage‑collected by the janitor once **older than 72h** and matching the allow‑list (`repo_janitor.STALE_STASH_PATTERNS`).
- The janitor **never** drops a stash whose message is outside the allow‑list (e.g. a human "important/keep" stash).
- Before any drop, a `stash-janitor-backup-*` tag is written, so every drop is recoverable.
- Agents should prefer committing WIP to the cycle branch over stashing.

---

## 6. Worktree policy

- The **only** sanctioned worktrees are the main checkout (`C:/Fiverr/Fiverr`) and the CI‑runner worktrees under `C:/actions-runner/_work/**`.
- CI‑runner worktrees and their branches are **hard‑excluded** from all cleanup (`repo_janitor._is_ci_path`). Never remove, never check out, never delete.
- Task worktrees (merges, stage tests, verification) are created only when necessary and removed in the same session. The janitor removes any obsolete non‑CI worktree, but only when it is **clean** (no `--force`, so uncommitted work is never discarded).

---

## 7. The autonomous janitor (`automation/repo_janitor.py`)

The active enforcement that was missing. Safe by construction:

- **Dry‑run by default**; mutations require `--execute` / `execute=True`.
- Prunes: merged **local** branches (`-d`), **squash‑merged** branches confirmed via merged‑PR head (`-D` + recovery tag), merged **remote** cycle branches, **obsolete worktrees** (clean only), and **stale auto‑stashes** (allow‑list + age + recovery tag).
- Never touches protected/current branches, CI‑runner worktrees/branches, or unmerged work.
- Returns a structured `JanitorReport` (`--json` for machine consumption) and logs every action.

```bash
python -m automation.repo_janitor            # report what would be cleaned
python -m automation.repo_janitor --execute  # perform cleanup
```

Recovery: `branch-janitor-backup-*` and `stash-janitor-backup-*` tags point at anything force‑removed.

---

## 8. Per‑role responsibilities

### 8.1 PM (Claude prompt creator)
- Embeds the GitHub rules (§2–§6) into every agent prompt's git‑instructions section.
- Targets exactly one `cycle/<NNN>/integration` branch per cycle; never spawns extra branches.
- After a cycle merges, ensures the post‑cycle path runs the janitor (§9).

### 8.2 Cursor agents
- Work only on the active cycle branch; never create or switch branches.
- Stage explicit paths only; never commit generated artifacts (§4) or sentinel output (§8.4).
- Leave a clean working tree and push before declaring `AGENT_COMPLETE`.

### 8.3 In‑between Codex reviewer (and the review gate)
- The `codex-review-gate` blocks merge while any review thread is **unresolved and not outdated**. Treat review as a **loop, not a one‑shot**:
  1. Read every Codex thread on the current head.
  2. For each: **fix** the issue (commit), **or** resolve with an explicit `won't‑fix: <reason>` reply when justified and track a follow‑up.
  3. Re‑run the gate; repeat until green.
- Every push moves the head and can re‑open/relocate threads — budget for at least one address‑and‑resolve pass after the final code push.
- A justified resolution is acceptable but must be honest and, for real issues, tracked (e.g. a SCRUM ticket).

### 8.4 Cycle‑report writers
- Reports are **append‑once** human/agent deliverables. ICV/sentinel verification (SCRUM‑999, "Feature X", "echo OK") must **never** be written into a tracked `docs/cycle_reports/CYCLE_*_AGENT_*.md`; sentinel output belongs in an ignored scratch path.
- Report synthesis/directive artifacts are generated → ignored (§4), not committed by agents.

---

## 9. Wiring (how the janitor runs unattended) — **pending operator approval**

Because this changes the behaviour of the live 24/7 runner, the wiring is proposed, not silently enabled. Two safe options (pick one):

1. **Post‑cycle hook** — call `repo_janitor.run(execute=True)` at the end of `automation/post_cycle_review.py` (mode `POST_CYCLE_PM_REVIEW`, i.e. after the PR is merged to develop), so each completed cycle cleans up after itself. Lowest latency; cleans exactly when branches become mergeable.
2. **Scheduled task** — register `python -m automation.repo_janitor --execute` as a daily task alongside the existing scheduled tasks. Fully decoupled from the controller (zero controller code change); good defence‑in‑depth.

Recommended: **both** — option 1 for immediate per‑cycle cleanliness, option 2 as a daily backstop. Until enabled, run the janitor manually (`--execute`) at the cadence of the old Weekly Hygiene step.

---

## 10. CI‑gate discipline

A PR merges to `develop` only when all required checks are green (`github_policy.yml: develop_required_checks`): `CI / lint`, `CI / type-check`, `CI / tests-coverage`, `CI / smoke-gates`, `codecov/project`, `codecov/patch`, plus `codex-review-gate` and `merge_gate`. Lint must be kept green on `develop` itself — a broken lint on the base blocks every downstream PR (this happened and cost a full debugging pass). Never merge around a red required check; fix the cause.

---

## 11. CRLF / `.gitattributes`

Phantom full‑file diffs (changes that disappear under `git diff --ignore-cr-at-eol`) come from inconsistent line endings on a Windows host. Normalize with a repo `.gitattributes` (`* text=auto eol=lf`, with explicit `*.bat/*.ps1 eol=crlf`) so files stop oscillating between CRLF and LF every time git touches them. Until normalized, treat CR‑only diffs as non‑changes (revert with `git checkout -- <file>`).

---

## 12. Recovery

Everything destructive is recoverable:
- Branches/stashes removed by the janitor → `branch-janitor-backup-*` / `stash-janitor-backup-*` tags.
- Manual cleanups in this initiative → `branch-backup-*` / `stash-backup-*` / `stash-preserve-*` tags.
Restore a branch with `git branch <name> <backup-tag>`; inspect a stash with `git stash show -p <tag>` after `git stash store`.
