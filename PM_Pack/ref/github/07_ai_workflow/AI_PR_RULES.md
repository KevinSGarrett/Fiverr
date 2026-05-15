# AI PR Rules
# Fiverr Research System — Rules AI Agents Must Follow When Creating PRs

---

## Mandatory Rules (Every PR, No Exceptions)

### Rule 1: Always Branch from Latest Develop
```bash
git checkout develop
git pull origin develop
git checkout -b feature/epicXX/SX.X-description
```
NEVER branch from another feature branch. NEVER branch from a stale develop.

### Rule 2: Run Checks Before Pushing
```bash
ruff check src/ tests/
ruff format src/ tests/ --check
mypy src/ --ignore-missing-imports --strict
pytest tests/ -x --cov=src --cov-fail-under=80
```
If ANY check fails, fix it before pushing. Do NOT push broken code hoping CI will catch it.

### Rule 3: PR Title Must Match Convention
```
{type}({scope}): {description}
```
See PR_TITLE_CONVENTIONS.md. CI will reject non-conforming titles.

### Rule 4: Fill Out the ENTIRE PR Template
Every section must have meaningful content:
- **What:** ≥ 1 sentence describing the change
- **Why:** Issue link with `Closes #XX` or `Relates to #XX`
- **How:** Implementation approach
- **Testing:** What tests exist
- **Checklist:** All items checked or explicitly marked N/A with reason

### Rule 5: Apply All Required Labels Before Requesting Merge
| Category | Exactly 1 | At Least 1 |
|---|---|---|
| `type:*` | ✅ | |
| `priority:*` | ✅ | |
| `risk:*` | ✅ | |
| `scope:*` | | ✅ |
| `agent:*` | ✅ | |

CI will block merge if required labels are missing.

### Rule 6: One PR = One Story or One Logical Change
- Do NOT combine multiple stories in one PR
- Do NOT include unrelated refactoring or fixes
- Do NOT include "while I was here" changes
- If you find a bug while working on a feature → create a separate issue + separate PR

### Rule 7: Keep PRs Small
- Target: < 300 lines changed
- Acceptable: < 500 lines
- XL warning: 501-1000 lines (justify in PR body)
- XXL blocked: > 1000 lines (must split or get override label)

### Rule 8: Never Commit Secrets
- No API keys, tokens, passwords, or connection strings
- No `.env` files (only `.env.example` with placeholder values)
- No hardcoded URLs with credentials
- CI scans for common secret patterns and will fail the PR

### Rule 9: Tests Are Required for Feature and Fix PRs
- `type:feature` → must include unit tests for new code
- `type:fix` → must include test that reproduces the bug + verifies the fix
- `type:test` → obviously has tests
- `type:docs`, `type:chore`, `type:style` → tests optional

### Rule 10: Match the Spec
Every feature must trace back to a spec document in `project-pack/`:
- Reference the spec in the PR body: "Implements per project-pack/05_scoring/DEMAND_SCORE.md Section 3"
- If the implementation deviates from the spec, explain WHY in the PR body
- If the spec is wrong or incomplete, create an issue to update it

---

## Behavioral Rules

### On Merge Conflicts
```
# Always rebase, never merge develop into your branch
git fetch origin
git rebase origin/develop
# Resolve conflicts carefully
# Re-run checks after rebase
ruff check src/ tests/
pytest tests/ -x
git push --force-with-lease
```

### On CI Failure
1. Read the CI log carefully — identify which check failed
2. Fix the issue locally
3. Re-run the failing check locally to confirm fix
4. Push the fix
5. Do NOT add `override:*` labels to bypass CI — fix the problem

### On Uncertainty
If an agent is unsure about:
- **Architecture:** Comment on the issue asking PM for guidance
- **Spec interpretation:** Reference the specific spec section, ask PM to clarify
- **Risk level:** Apply the HIGHER risk tier, add comment explaining uncertainty
- **Scope boundary:** Create a spike issue, timebox the investigation

### On Cross-Agent Dependencies
- NEVER modify files owned by another agent
- If you need a change in another agent's code → create an issue assigned to that agent
- If blocked by another agent → label your issue `status:blocked` + mention the blocking issue
- If urgently blocked (P1/P2) → flag to PM immediately via issue comment

---

## PR Anti-Patterns (What NOT to Do)

| Anti-Pattern | Why It's Bad | What to Do Instead |
|---|---|---|
| Giant PR with 2000+ lines | Impossible to review, high risk | Split into 3-5 smaller PRs |
| PR with "fix everything" title | No traceability, unclear scope | One PR per fix, clear titles |
| PR that modifies 8 different modules | Blast radius too large | Separate PRs per module |
| Force-pushing to develop | Destroys history for all agents | Never force-push shared branches |
| Merging without labels | Breaks tracking and automation | CI blocks this, but don't try |
| Copying code instead of importing | Duplication = maintenance burden | Import from the owning module |
| Skipping tests "to save time" | Technical debt compounds fast | Tests are never optional for features |
| Committing .env or secrets | Security breach | Use .env.example, GitHub Secrets |
| Working on wrong branch | Merge nightmares | Always verify: `git branch` before committing |
