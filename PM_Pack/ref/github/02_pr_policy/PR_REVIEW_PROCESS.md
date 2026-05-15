# PR Review Process
# Fiverr Research System

---

## Review Model: Automated-First, Human-Selective

Since this project is built by AI agents with a single human operator, the review process is:

1. **Automated checks** (CI) are the primary quality gate — always required
2. **Human review** is selective — applied based on risk tier and complexity
3. **ChatGPT PM** can review PR descriptions and flag issues via comments

---

## Automated Review (Every PR)

| Check | Tool | What It Catches |
|---|---|---|
| Code style | Ruff | Formatting, import order, unused imports, style violations |
| Type safety | Mypy (strict) | Type errors, missing annotations, wrong types |
| Tests | Pytest | Logic errors, regression, coverage drops |
| PR format | Custom Action | Bad title, missing labels, oversized PR |
| Security | Custom Action | Secrets in code, hardcoded credentials |
| Dependencies | Dependabot | Known vulnerabilities in packages |

---

## Human Review Triggers

The human operator should review a PR when:

| Trigger | Risk Level | Example |
|---|---|---|
| PR is `risk:critical` | P1 | Database schema migration, orchestrator changes |
| PR is `risk:high` | P2 | New collection workflow, scoring formula change |
| PR touches multiple epics | Any | Cross-cutting refactor |
| PR is `size:XL` or larger | Any | Large feature implementation |
| Agent requests review | Any | Agent is uncertain about approach |
| CI passes but behavior is complex | Any | LLM prompt changes, async coordination |
| Release PR (develop → main) | Always | Epic completion release |

---

## Review Checklist (When Human Reviews)

### Correctness
- [ ] Does the code do what the PR description claims?
- [ ] Does it match the spec in project-pack/?
- [ ] Are edge cases handled (null, empty, out-of-range)?

### Architecture
- [ ] Is the code in the right module/file?
- [ ] Does it follow existing patterns in the codebase?
- [ ] Are there any circular dependencies introduced?

### Testing
- [ ] Are new tests meaningful (not just boilerplate)?
- [ ] Do tests cover the happy path AND error cases?
- [ ] Is coverage maintained or improved?

### Security
- [ ] No hardcoded secrets or API keys?
- [ ] No sensitive data logged or exposed?
- [ ] Input validation present where needed?

### Performance
- [ ] No N+1 queries introduced?
- [ ] No unbounded loops or memory growth?
- [ ] Appropriate caching where applicable?

---

## Review Resolution

### Comment Types
| Type | Format | Meaning |
|---|---|---|
| Blocking | `[BLOCKING] Fix this before merge` | Must be resolved |
| Suggestion | `[SUGGESTION] Consider using X instead` | Optional improvement |
| Question | `[QUESTION] Why did you choose X over Y?` | Need clarification |
| Nitpick | `[NIT] Minor style preference` | Ignore if you disagree |

### Resolution Rules
- **BLOCKING** comments must be resolved (code change or explanation)
- **SUGGESTION** comments should be addressed but can be deferred
- **QUESTION** comments require a reply (can be brief)
- **NIT** comments can be ignored
- All conversations must be resolved before merge (enforced by branch protection)

---

## Self-Merge Policy

Since this is a single-developer AI project:
- AI agents can self-merge when all CI checks pass AND the PR is `risk:low` or `risk:medium`
- `risk:high` and `risk:critical` PRs should wait for human review
- Release PRs (develop → main) always get human review
- Auto-merge is enabled for qualifying PRs (CI green + correct labels)
