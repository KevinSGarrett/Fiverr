# PR Size Policy
# Fiverr Research System

---

## Size Categories

| Label | Lines Changed | Review Time | Risk Level |
|---|---|---|---|
| `size:XS` | 1-10 lines | < 5 min | Minimal |
| `size:S` | 11-50 lines | 5-15 min | Low |
| `size:M` | 51-200 lines | 15-30 min | Medium |
| `size:L` | 201-500 lines | 30-60 min | Elevated |
| `size:XL` | 501-1000 lines | 60+ min | High |
| `size:XXL` | 1000+ lines | Too large | **Must be split** |

**Lines changed = additions + deletions** (excluding auto-generated files, lock files, and test fixtures)

---

## Size Rules

### Target Size: Small to Medium (< 300 lines)
- **Ideal PR:** 50-200 lines changed
- **Maximum without justification:** 500 lines
- **Hard limit:** 1000 lines (XXL PRs are blocked by CI)

### Why Small PRs?
1. **Faster to review** — AI agents can verify correctness quickly
2. **Easier to understand** — single logical change per PR
3. **Safer to merge** — smaller blast radius if something breaks
4. **Less conflict risk** — especially with 4 agents working concurrently
5. **Faster CI** — smaller diffs = faster test runs

---

## XXL PR Policy (1000+ lines)

XXL PRs are **automatically flagged** by CI with a warning comment. They must be either:

1. **Split into smaller PRs** — preferred approach
2. **Justified** — if genuinely indivisible (e.g., initial scaffolding, large schema migration)

### Acceptable XXL Exceptions:
| Exception | Example | One-Time? |
|---|---|---|
| Initial project scaffolding | Story 1.1 — create all directories + placeholder files | Yes |
| Database model bulk creation | Story 1.3 — all 28 SQLAlchemy models | Yes |
| Large auto-generated content | Seed data files, fixture files | Yes |
| Template bulk creation | Story 5.4 — all 13 Jinja2 templates | Yes |

### NOT Acceptable XXL:
- Combining multiple stories into one PR
- "I forgot to commit earlier"
- Mixing feature code with refactoring
- Including unrelated file changes

---

## Size Exclusions

The following files are excluded from line count for size labeling:

```
*.lock          # Lock files
*.json          # Fixture/seed data (if in tests/fixtures/ or data/seeds/)
*.j2            # Jinja2 templates (counted separately as template work)
*.yaml          # Config files (if data/seeds/)
*.md            # Documentation-only PRs
__init__.py     # Empty init files
```

---

## How to Split Large PRs

### Strategy 1: Vertical Slice
Split by feature layer:
```
PR 1: Add database model for Keyword
PR 2: Add KeywordExpansion workflow
PR 3: Add expansion tests
```

### Strategy 2: Horizontal Slice
Split by component within a feature:
```
PR 1: Add DemandScoreCalculator (logic only)
PR 2: Add demand score tests
PR 3: Wire demand score into orchestrator
```

### Strategy 3: Interface First
```
PR 1: Add abstract BaseScoreCalculator + interface
PR 2: Implement DemandScoreCalculator
PR 3: Implement CompetitionScoreCalculator
```

---

## CI Enforcement

The `pr-checks` workflow automatically:
1. Counts lines changed (additions + deletions)
2. Excludes exempted file types
3. Applies the size label (`size:XS` through `size:XXL`)
4. Posts warning comment if `size:XL` or `size:XXL`
5. **Blocks merge** if `size:XXL` without `override:large-pr` label
