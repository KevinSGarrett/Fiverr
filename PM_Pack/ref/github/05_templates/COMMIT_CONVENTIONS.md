# Commit Conventions
# Fiverr Research System — Commit Message Standards

---

## Commit Message Format

```
{type}({scope}): {subject}

{body}

{footer}
```

### Header (Required)
- **Same format as PR titles** — see PR_TITLE_CONVENTIONS.md
- Max 72 characters
- Imperative mood: "add", "fix", "update" — not "added", "fixed", "updated"

### Body (Optional but Recommended)
- Blank line between header and body
- Wrap at 72 characters per line
- Explain WHAT and WHY, not HOW (code shows how)
- Use when the header alone doesn't convey enough context

### Footer (Optional)
- Reference issues: `Closes #47`, `Relates to #12`
- Breaking changes: `BREAKING CHANGE: description`

---

## Commit Types

Same as PR title types — see PR_TITLE_CONVENTIONS.md for the full list:
`feat`, `fix`, `refactor`, `test`, `docs`, `chore`, `style`, `perf`, `ci`, `build`, `release`, `hotfix`, `revert`

---

## Individual Commits vs PR Title

### Key Distinction
- **Individual commits** within a feature branch are for the agent's own tracking — they get squashed on merge, so they DON'T need to be perfect
- **The PR title** becomes the actual commit on develop/main — it MUST follow conventions exactly

### What This Means in Practice
```
# These individual commits on a feature branch are fine (they'll be squashed):
git commit -m "wip: start demand score"
git commit -m "add log scaling"
git commit -m "fix test"
git commit -m "add edge cases"

# The PR title (which becomes the squash commit) must be perfect:
feat(scoring): add demand score calculator with 4 components
```

### Agent Guidelines for Individual Commits
Even though commits are squashed, agents SHOULD still write reasonable messages because:
1. They help during development if you need to find/revert specific changes
2. They appear in the PR diff view for review
3. Good habits produce good code

### Recommended Individual Commit Style
```
# Good (clear, useful during development)
git commit -m "feat(scoring): scaffold DemandScoreCalculator class"
git commit -m "feat(scoring): implement log-scaled fiverr count component"
git commit -m "test(scoring): add demand score unit tests"
git commit -m "fix(scoring): handle null trend data in demand score"

# Acceptable (less formal but still useful)
git commit -m "add base demand score class"
git commit -m "implement all 4 components"
git commit -m "add tests, fix edge case"

# Bad (useless — don't do this even though commits are squashed)
git commit -m "update"
git commit -m "fix"
git commit -m "wip"
git commit -m "asdf"
git commit -m "."
```

---

## Examples — Full Commit Messages

### Feature Commit (with body)
```
feat(scoring): add demand score calculator with 4 components

Implements DemandScoreCalculator per DEMAND_SCORE.md spec:
- Log10 scaling for Fiverr result count (0-50K+ range)
- Linear autocomplete position mapping (1=100, 10=10, absent=0)
- Google Trends slope with configurable thresholds
- Reddit intent signal normalized to 0-100 scale

All weights configurable via weight profile system.

Closes #47
```

### Fix Commit (with body)
```
fix(collection): handle null gig price in package parser

Fiverr occasionally returns gig pages without the standard 3-tier
package section (~2% of gigs, typically custom-offer-only sellers).
Added null check before accessing packages array; returns empty
PackageList with is_custom=True flag.

Closes #63
```

### Chore Commit (header only)
```
chore(deps): upgrade sqlalchemy to 2.0.30
```

### Refactor Commit (with body)
```
refactor(scoring): extract BaseScoreCalculator abstract class

All 11 score calculators share validation, normalization, and weight
application logic. Extracted into BaseScoreCalculator to reduce
duplication and enforce consistent interface.

Relates to #50
```

---

## Commit Signing

### Policy: Optional (Recommended for Production)
- Not required during development phase
- Recommended to enable before v1.0.0 release
- If enabled, set in branch protection: "Require signed commits"

### Setup (if enabling later)
```bash
# Generate GPG key
gpg --full-generate-key

# Configure git to sign
git config --global user.signingkey YOUR_KEY_ID
git config --global commit.gpgsign true
```

---

## Commit Frequency Guidelines

| Scenario | Guidance |
|---|---|
| Implementing a story | Commit after each meaningful unit (class, function, test suite) |
| Fixing a bug | Can be a single commit |
| Refactoring | Commit after each safe transformation |
| Exploration/spike | Commit when something works |

### Rule of Thumb
If you couldn't explain what a commit does in one sentence, it's too big. Split it.
