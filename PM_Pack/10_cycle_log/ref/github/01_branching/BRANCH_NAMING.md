# BRANCH NAMING CONVENTIONS
# Updated: Cycle 019 (DL-031)

---

## Branch Types and Patterns

| Type | Pattern | Example |
|---|---|---|
| Cycle integration | `cycle/{NNN}/integration` | `cycle/020/integration` |
| Story feature | `feature/epic{NN}/SCRUM-{key}-{slug}` | `feature/epic01/SCRUM-136-db-init` |
| Bug fix | `fix/SCRUM-{key}-{slug}` | `fix/SCRUM-200-config-crash` |
| Hotfix | `hotfix/{description}` | `hotfix/missing-import-guard` |

---

## DL-031 — Cycle Integration Pattern

Integration branches use `cycle/{NNN}/integration`. This is an operational necessity not covered by the original spec branch naming. The cycle integration branch consolidates all agent work for a single cycle before merging to develop.

- All 4 agents commit to the SAME integration branch
- One PR per cycle from the integration branch to develop
- Story branches (`feature/epic{NN}/SCRUM-{key}-{slug}`) are for individual story PRs outside of cycle batches

---

## Jira Key Requirement

Always include the Jira key in story and fix branch names. This activates the Jira-GitHub auto-link:
```
feature/epic01/SCRUM-136-db-init        ← Development panel auto-populates on SCRUM-136
fix/SCRUM-200-config-crash              ← Development panel auto-populates on SCRUM-200
```

Cycle integration branches do NOT need a Jira key — they link via PR body mentions.

---

## Slug Rules

- Lowercase only
- Hyphens as separators (no underscores)
- Max 30 characters for slug
- Descriptive of the primary change
- Examples: `db-init`, `playwright-session`, `demand-score`, `gig-quality-analysis`
