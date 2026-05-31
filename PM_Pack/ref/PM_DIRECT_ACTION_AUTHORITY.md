# PM Direct-Action Authority — Decision Table

**Canonical rule lives in `AGENT_EXECUTION_STRATEGY.md` §9.** This file is the quick decision table
the PM consults after every cycle and between cycles.

## The one-line test

> Reversible **AND** leaves `src/` + `tests/` + config-behavior untouched **AND** needs no gate/merge?
> → **PM does it now (Tier A).**
> Touches code / tests / config-behavior, or needs a gate? → **cursor agent (Tier C).**
> Irreversible, or cost / security / account impact? → **ask the user (Tier D).**

## Decision table

| Item | Tier | Who | Notes |
| --- | --- | --- | --- |
| Transition Jira to match merged reality | A | PM now | record nothing extra |
| Add/edit Jira comments; link to epic; fix labels/sprint | A | PM now | |
| Create cycle control + story tickets | A/B | PM now | record created keys (B) |
| Revert a Jira story wrongly marked Done (DoD unmet) | A | PM now | |
| Delete the *merged* cycle branch on origin | A | PM now | only if merged |
| Prune stale *already-merged* remote cycle branches | A | PM now | |
| Comment on / inspect a PR; read CI; read Codex threads | A | PM now | |
| Edit PM_Pack / strategy doc / hydration / tracker / prep notes | A | PM now | |
| Refresh templates; add a steward note to a cycle report | A | PM now | report body stays agent-authored |
| Remove untracked PM scratch litter | A | PM now | |
| `git rm --cached` an accidentally-tracked artifact | B | PM now | pair with .gitignore entry + record |
| Extend `.gitignore` (scratch, `config.live.yaml`) | A | PM now | |
| Run tests / `--cov` / config-check / smoke / git/gh reads / Codex query | A | PM now | read-only; always allowed |
| Commit + push PM doc/governance changes to develop | A | PM now | ZERO src/ + tests/ + config-behavior; `docs(...)`/`chore(...)` |
| Large/multi-file doc commit | B | PM now | record SHA + rationale in prep notes |
| **Any change under `src/`** (even one line) | C | **Agent B** | defect note; preserves attribution invariant |
| **Any add/modify under `tests/`** | C | **Agent B / F** | PM never authors tests |
| **Any `config.yaml` runtime-behavior change** (toggles/thresholds/weights/scrapfly-on) | C | **Agent B** | parity + config gate + CI + Codex + D-merge |
| Anything that must pass a gate or merge as cycle scope | C | cursor agents | G-001..G-004 + Agent D |
| Drop/clear stashes; history rewrite; force-push; delete unmerged/non-cycle branch | D | **ask user** | irreversible |
| Rotate secrets; change repo settings / branch protection | D | **ask user** | security |
| Large live ScrapFly run (significant credit burn) | D | **ask user** | small validation sample is A/B |

## Why the bright line at `src/`

Agent D's merge gate verifies that **every `src/`-touching commit in a cycle range is an Agent B
`feat/`|`fix/` commit**, and that there is **no no-op "attribution" touch**. If the PM edits `src/`
directly, that invariant breaks and the gate (correctly) blocks. The Cycle-051 failures c6489b9
(Agent C edited src/) and c7b9b52 (Agent D no-op touch) are kept closed *because* nobody but Agent B
writes `src/`. The PM's expanded autonomy stays entirely outside `src/`, `tests/`, and config
behavior for exactly this reason.

## What a clean post-cycle PM pass now looks like

1. Verify merge state (develop HEAD, PR, CI, Codex, Jira) — read-only (Tier A).
2. Correct Jira to match reality; delete the merged cycle branch; prune stale branches (Tier A).
3. Remove scratch litter; fix any accidentally-tracked artifact + `.gitignore` (Tier A/B).
4. Update PM_Pack / strategy doc / hydration / tracker / prep notes (Tier A).
5. Commit + push those doc changes to develop (Tier A; zero src/tests/config).
6. Write the next cycle's prompts.
7. Escalate anything in Tier C to the cursor agents and anything in Tier D to the user.
