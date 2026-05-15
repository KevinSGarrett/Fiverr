# JIRA FIELD STANDARDS

---

## Summary Formats
| Type | Format | Example |
|---|---|---|
| Epic | Epic {NN}: {Name} | Epic 01: Foundation & Infrastructure |
| Story | S{N}.{N}: {Title} | S1.2: Configuration System |
| Task | T{N}.{N}.{N}: {Title} | T1.2.1: Create config.yaml master template |
| Bug | [Bug] {Description} | [Bug] Config loader crashes on empty niche list |
| Spike | [Spike] {Question} | [Spike] Playwright vs Puppeteer for Fiverr scraping |

## Description Template
```
## Overview
{1-2 sentence summary}

## Spec Reference
- File: project-pack/{folder}/{FILE}.md
- Section: {relevant section}

## Acceptance Criteria
- [ ] {criterion 1}
- [ ] {criterion 2}

## Technical Notes
{Implementation guidance, file paths, dependencies}

## Agent Assignment
- Agent: {A|B|C|D}
- Epic: {NN}
- Story: S{N}.{N}
```

## Labels
- Agent: agent:A, agent:B, agent:C, agent:D
- Scope: scope:epic01, scope:epic02, etc.
- Cycle: cycle:001, cycle:002, etc.
- Type: type:feature, type:fix, type:test, type:chore
