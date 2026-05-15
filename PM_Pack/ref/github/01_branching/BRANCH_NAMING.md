# Branch Naming Conventions
# Fiverr Research System

---

## Branch Name Format

```
{type}/{scope}/{description}
```

### Components

| Component | Required | Format | Examples |
|---|---|---|---|
| type | Yes | Lowercase keyword | `feature`, `fix`, `hotfix`, `chore`, `refactor`, `test`, `docs` |
| scope | Yes | Epic or module reference | `epic01`, `epic02`, `collection`, `scoring`, `ci` |
| description | Yes | Kebab-case, max 50 chars | `S1.2-config-system`, `broken-gig-selector`, `add-pytest-fixtures` |

---

## Type Prefixes

| Prefix | When to Use | Target Branch |
|---|---|---|
| `feature/` | New functionality, story implementation | develop |
| `fix/` | Bug fixes during development | develop |
| `hotfix/` | Critical production fixes | main |
| `chore/` | Dependencies, config, CI, non-code changes | develop |
| `refactor/` | Code restructuring without behavior change | develop |
| `test/` | Adding or improving tests only | develop |
| `docs/` | Documentation changes only | develop |

---

## Scope Reference

| Scope | Covers | Agent |
|---|---|---|
| `epic01` | Foundation, config, models, CLI, LLM client | Agent 1 |
| `epic02` | Collection engine, Playwright, workflows | Agent 2 |
| `epic03` | Analysis engine, clustering, quality | Agent 3 |
| `epic04` | Scoring engine, all 11 calculators | Agent 3 |
| `epic05` | Recommendation engine, LLM tasks | Agent 3 |
| `epic06` | Pricing engine | Agent 3 |
| `epic07` | Discovery engine | Agent 3 |
| `epic08` | Playbook engine | Agent 4 |
| `epic09` | Dashboard, reporting, exports | Agent 4 |
| `epic10` | Integration, testing, launch | All |
| `ci` | CI/CD pipeline changes | Agent 1 |
| `deps` | Dependency updates | Agent 1 |
| `docs` | Documentation | Any |

---

## Naming Rules

1. **All lowercase** — no uppercase letters anywhere
2. **Kebab-case** for description — hyphens between words, no underscores in description
3. **No spaces** — ever
4. **Max 70 characters total** for the full branch name
5. **Story ID in description** when implementing a specific story (e.g., `S1.2` for Story 1.2)
6. **Be specific** — `feature/epic02/S2.8-fiverr-search-workflow` not `feature/epic02/search`
7. **No ticket numbers** unless using GitHub Issues — then prefix with issue number: `feature/epic01/42-config-loader`

---

## Examples — Correct

```
feature/epic01/S1.1-project-scaffolding
feature/epic01/S1.3-database-models
feature/epic02/S2.1-playwright-session-manager
feature/epic02/S2.8-fiverr-search-workflow
feature/epic04/S4.1-demand-score-calculator
feature/epic09/S9.3-opportunities-page
fix/epic02/gig-selector-fallback-broken
fix/epic04/nan-score-null-input
hotfix/db-migration-missing-column
chore/deps/upgrade-sqlalchemy-2.0.30
chore/ci/add-type-checking-step
refactor/epic03/extract-base-analyzer-class
test/epic01/add-config-validation-tests
docs/epic01/update-readme-setup-instructions
```

## Examples — WRONG (Do Not Use)

```
❌ Feature/Epic01/Config       (uppercase, too vague)
❌ feature/config_system        (underscore, missing scope)
❌ my-branch                    (no type prefix, no scope)
❌ feature/epic01/S1.2_config   (underscore in description)
❌ feature/epic01/implement-the-entire-configuration-system-with-all-nine-niches-loaded  (too long)
❌ wip                          (meaningless)
❌ test123                      (meaningless)
```

---

## Agent-Specific Naming

Each agent should use their epic scope to avoid naming collisions:

| Agent | Typical Branch Prefix |
|---|---|
| Agent 1 (Infrastructure) | `feature/epic01/...`, `chore/ci/...`, `chore/deps/...` |
| Agent 2 (Collection) | `feature/epic02/...` |
| Agent 3 (Analysis/Scoring) | `feature/epic03/...`, `feature/epic04/...`, `feature/epic05/...`, `feature/epic06/...`, `feature/epic07/...` |
| Agent 4 (Dashboard/UX) | `feature/epic08/...`, `feature/epic09/...` |
