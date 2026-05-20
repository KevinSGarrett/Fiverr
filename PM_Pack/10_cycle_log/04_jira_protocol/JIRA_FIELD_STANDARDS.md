# JIRA FIELD STANDARDS
# Updated: Cycle 019

---

## Summary Formats
| Type | Format | Example |
|---|---|---|
| Epic | Epic {NN}: {Name} | Epic 01: Foundation & Infrastructure |
| Story | S{N}.{N}: {Title} | S1.2: Configuration System |
| Task | T{N}.{N}.{N}: {Title} | T1.2.1: Create config.yaml master template |
| Bug | [Bug] {Description} | [Bug] Config loader crashes on empty niche list |
| Spike | [Spike] {Question} | [Spike] Playwright vs Puppeteer for Fiverr scraping |

---

## Description Template
```
## Overview
{1-2 sentence summary}

## Spec Reference
- File: PM_Pack/ref/{folder}/{FILE}.md
- Section: {relevant section}

## Acceptance Criteria
- [ ] {criterion 1}
- [ ] {criterion 2}

## Definition of Done
- [ ] {dod item 1}
- [ ] {dod item 2}

## Technical Notes
{Implementation guidance, file paths, dependencies}

## Agent Assignment
- Agent: {1-Infrastructure | 2-Collection | 3-Analysis | 4-Dashboard}
- Epic: {NN}
- Story: S{N}.{N}

## Jira-GitHub Links
- Branch: feature/epic{NN}/SCRUM-{key}-{slug}
- PR: #N (added when opened)
```

---

## Complete Label Taxonomy (61 Labels — All Deployed)

### Type Labels
| Label | When to use |
|---|---|
| `type:feature` | New capability or product story |
| `type:fix` | Bug fix or correction |
| `type:test` | Test-only change |
| `type:chore` | Maintenance, cleanup, non-product |
| `type:docs` | Documentation update |
| `type:refactor` | Code restructure without behavior change |
| `type:perf` | Performance improvement |
| `type:ci` | CI/CD pipeline change |
| `type:security` | Security-related change |
| `type:spike` | Research or investigation |
| `type:revert` | Reverts a prior change |

### Priority Labels
| Label | Meaning |
|---|---|
| `priority:P1-critical` | Blocks progress — fix immediately |
| `priority:P2-high` | Must resolve this cycle |
| `priority:P3-medium` | Target this cycle if capacity allows |
| `priority:P4-low` | Nice to have — defer if needed |

### Scope Labels (one per issue — matches epic)
`scope:epic01` `scope:epic02` `scope:epic03` `scope:epic04` `scope:epic05`
`scope:epic06` `scope:epic07` `scope:epic08` `scope:epic09` `scope:epic10`
`scope:meta` (for governance/PM tickets)

### Agent Labels (one per issue — who owns it)
| Label | Agent | Epics |
|---|---|---|
| `agent:1-infrastructure` | Agent A | E01, E10 |
| `agent:2-collection` | Agent B | E02 |
| `agent:3-analysis` | Agent C | E03, E04, E05, E06, E07 |
| `agent:4-dashboard` | Agent D | E08, E09 |
| `agent:pm` | PM / Claude | Governance, meta |

### Size Labels (set by pr-checks.yml — but apply manually to Jira)
| Label | Lines changed |
|---|---|
| `size:XS` | < 50 lines |
| `size:S` | 50–149 lines |
| `size:M` | 150–299 lines |
| `size:L` | 300–499 lines |
| `size:XL` | 500–999 lines |
| `size:XXL` | 1000+ lines |

### Status Labels
`status:blocked` `status:needs-review` `status:in-progress`
`status:ready-to-merge` `status:wont-fix` `status:duplicate` `status:stale`

### Risk Labels
`risk:breaking-change` `risk:data-migration` `risk:performance` `risk:security`

### Issue Labels (for bugs/defects)
`issue:logic-error` `issue:missing-test` `issue:type-error` `issue:import-error`
`issue:schema-mismatch` `issue:missing-file` `issue:wrong-status` `issue:duplicate`

### Override Labels (PM-authorized only)
`override:large-pr` — bypasses the 1000-line PR size gate
`override:skip-smoke` — bypasses smoke gate check
`override:force-merge` — PM-authorized emergency merge

---

## Field Assignments Per Issue Type

| Field | Epic | Story | Task | Bug |
|---|---|---|---|---|
| Type label | Required | Required | Required | type:fix |
| Priority label | Required | Required | Required | Required |
| Scope label | Required | Required | Required | Required |
| Agent label | Required | Required | Required | Required |
| Size label | PR only | PR only | PR only | Optional |
| Sprint | Required | Required | Required | Required |
| fixVersion | If in v0.1.0 | If in v0.1.0 | Optional | Optional |
