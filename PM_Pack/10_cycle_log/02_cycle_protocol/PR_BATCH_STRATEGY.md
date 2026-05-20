# PR BATCH STRATEGY
# How to batch all 4 agents into a single PR per cycle

---

## Workflow

```
1. Human creates branch from develop:
   git checkout develop && git pull
   git checkout -b cycle/{NNN}/integration

2. Human runs Agent A prompt in Cursor
   -> Agent A creates/modifies files in its scope
   -> git add . && git commit -m "feat(epic01): S1.1 scaffolding [Agent A]"

3. Human runs Agent B prompt
   -> git add . && git commit -m "feat(epic02): S2.1 session manager [Agent B]"

4. Human runs Agent C prompt
   -> git add . && git commit -m "feat(epic04): S4.1 demand score [Agent C]"

5. Human runs Agent D prompt
   -> git add . && git commit -m "feat(epic09): S9.1 design system [Agent D]"

6. Human pushes:
   git push -u origin cycle/{NNN}/integration

7. Human creates ONE PR: cycle/{NNN}/integration -> develop
8. CI runs ONCE on combined work
9. If green -> squash merge
10. Branch auto-deleted
```

## Conflict Prevention (PM responsibility)
1. No two agents create/modify the same file
2. No two agents modify the same __init__.py
3. If shared files needed -> assign to ONE agent only


## Required PM Output Each Cycle

The PM cycle reply must include the exact human operator commands for this workflow. It is not enough for these instructions to exist only in the PM pack. Every cycle reply must print:

```bash
cd C:\Fiverr
git checkout develop
git pull origin develop
git checkout -b cycle/{NNN}/integration
# run Agent A -> commit
# run Agent B -> commit
# run Agent C -> commit
# run Agent D -> commit
git status
git push -u origin cycle/{NNN}/integration
```

Then the reply must state: create one PR from `cycle/{NNN}/integration` into `develop`, use the PM-provided PR title/body, wait for CI, and do not merge to `main`.
