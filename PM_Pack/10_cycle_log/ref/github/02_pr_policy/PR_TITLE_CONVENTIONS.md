# PR Title Conventions
# Fiverr Research System

---

## Title Format

```
{type}({scope}): {description}
```

**Max length:** 72 characters
**All lowercase** except proper nouns

---

## Type Prefixes (Required)

| Type | When to Use | Example |
|---|---|---|
| `feat` | New feature or functionality | `feat(scoring): add demand score calculator` |
| `fix` | Bug fix | `fix(collection): handle null gig price in parser` |
| `refactor` | Code restructuring without behavior change | `refactor(models): extract base model mixin` |
| `test` | Adding or modifying tests only | `test(scoring): add demand score edge case tests` |
| `docs` | Documentation changes | `docs(readme): add setup instructions` |
| `chore` | Dependencies, config, CI, tooling | `chore(deps): upgrade sqlalchemy to 2.0.30` |
| `style` | Formatting, whitespace, lint fixes (no logic change) | `style(analysis): fix ruff formatting violations` |
| `perf` | Performance improvement | `perf(queries): add index on keyword_id` |
| `ci` | CI/CD pipeline changes | `ci: add type-checking step to pipeline` |
| `build` | Build system changes | `build: update pyproject.toml dependencies` |
| `release` | Release to main | `release: epic 01 foundation and infrastructure` |
| `hotfix` | Emergency production fix | `hotfix: fix database migration missing column` |
| `revert` | Reverting a previous commit | `revert: undo demand score log scaling change` |

---

## Scope (Required)

The scope identifies WHAT area of the codebase is changed.

| Scope | Maps To | Example |
|---|---|---|
| `config` | src/config/ | `feat(config): add niche validation rules` |
| `models` | src/models/ | `feat(models): create keyword and gig models` |
| `collection` | src/collection/ | `feat(collection): implement fiverr search workflow` |
| `analysis` | src/analysis/ | `feat(analysis): add gig quality rubric scoring` |
| `scoring` | src/scoring/ | `feat(scoring): implement competition score` |
| `llm` | src/llm/ | `feat(llm): add cache layer with sha-256 keys` |
| `pricing` | src/pricing/ | `feat(pricing): implement kde price distribution` |
| `discovery` | src/discovery/ | `feat(discovery): add adjacent keyword generator` |
| `playbook` | src/playbook/ | `feat(playbook): create visual analysis classifier` |
| `dashboard` | src/dashboard/ | `feat(dashboard): build opportunities page` |
| `exports` | src/exports/ | `feat(exports): add excel multi-sheet export` |
| `cli` | run.py, orchestrator | `feat(cli): add --mode resume flag` |
| `deps` | Dependencies | `chore(deps): pin playwright to 1.42.0` |
| `ci` | .github/workflows/ | `ci(ci): add security scanning workflow` |
| `repo` | Repo config/templates | `chore(repo): add pr template` |

If a PR touches multiple scopes, use the primary scope. If truly cross-cutting, omit scope: `chore: update all __init__.py exports`

---

## Description Rules

1. **Start with a verb** — imperative mood: "add", "fix", "update", "remove", "implement"
2. **No period** at the end
3. **Specific** — what exactly changed, not vague
4. **Max 50 characters** for description portion (after type and scope)

### Good Titles
```
feat(scoring): add demand score calculator with 4 components
feat(collection): implement fiverr search workflow with pagination
fix(models): handle null json fields in gig packages
test(analysis): add clustering edge case tests
chore(deps): upgrade openai sdk to 1.30.0
refactor(scoring): extract base score calculator class
ci: add ruff linting to pr checks pipeline
release: epic 02 collection engine
```

### Bad Titles
```
❌ Update files                          (vague, no type, no scope)
❌ feat: stuff                           (vague description)
❌ FEAT(SCORING): ADD DEMAND SCORE       (uppercase)
❌ feat(scoring): add demand score.      (trailing period)
❌ feat(scoring): I added the demand score calculator that processes all the various input signals  (too long)
❌ wip                                   (meaningless)
❌ fix things                            (vague, no scope)
```

---

## CI Enforcement

The `pr-checks / validate-pr` GitHub Action enforces:
1. Title matches regex: `^(feat|fix|refactor|test|docs|chore|style|perf|ci|build|release|hotfix|revert)(\([a-z0-9-]+\))?: .{1,50}$`
2. Title total length ≤ 72 characters
3. Description is not empty (min 50 characters in PR body)
4. At least one type label matches the title prefix
