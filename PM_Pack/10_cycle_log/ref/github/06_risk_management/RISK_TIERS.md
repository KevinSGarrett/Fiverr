# Risk Tiers
# Fiverr Research System — PR Risk Classification System

---

## Four Risk Tiers

Every PR must be classified into exactly one risk tier. The tier determines review requirements, merge conditions, and rollback planning.

---

## Tier 1: `risk:critical` — RED

### Definition
Changes that, if broken, could corrupt data, break the entire pipeline, or compromise security.

### Criteria (ANY of these → critical)
| Criterion | Examples |
|---|---|
| Database schema changes | Adding/removing/renaming columns, new migrations, model field type changes |
| Orchestrator core logic | RunOrchestrator pipeline flow, stage ordering, job dispatching |
| Security-sensitive code | Authentication, API key handling, .env parsing, secret management |
| Data deletion or mutation | Bulk update/delete queries, checkpoint purging, database reset scripts |
| Multi-epic breaking changes | Interface changes that affect 3+ epics |
| LLM client core | LLMClient base class, cache invalidation, token counting |
| Database connection/session | Engine creation, session factory, connection pooling |
| Configuration schema | Changes to config.yaml structure that affect all modules |

### Requirements
| Requirement | Enforced |
|---|---|
| All CI checks pass | ✅ Automated |
| Human review required | ✅ Manual |
| Rollback plan documented in PR | ✅ Manual |
| Integration test for the change | ✅ Manual |
| Cannot auto-merge | ✅ (presence of `risk:critical` blocks auto-merge) |
| Deploy to develop first, verify, then release | ✅ Process |

### Rollback Plan Template
```markdown
### Rollback Plan
- **Revert commit:** `git revert <sha>` on develop
- **Database rollback:** Run `alembic downgrade -1` (if migration)
- **Data recovery:** Restore from backup at data/backups/<timestamp>
- **Verification:** Run `pytest tests/integration/` after rollback
```

### Expected Frequency
~5-10% of all PRs. Mostly during Epic 01 (models/config) and Epic 10 (integration).

---

## Tier 2: `risk:high` — ORANGE

### Definition
Changes that introduce new behavior, complex logic, or external integrations that could subtly break downstream features.

### Criteria (ANY of these → high)
| Criterion | Examples |
|---|---|
| New collection workflow | Adding fiverr_search.py, gig_detail.py, or any new Playwright workflow |
| Scoring formula changes | Modifying weights, thresholds, normalization in any score calculator |
| LLM prompt changes | Editing .j2 templates that affect recommendation quality |
| New external API integration | Google Trends, Reddit, autocomplete endpoint |
| Async/concurrency logic | Queue processing, checkpoint resume, parallel execution |
| Pacing/rate-limiting changes | PacingManager thresholds, delay calculations |
| Selector updates | CSS selectors for Fiverr page scraping (site may have changed) |
| Cross-module interface changes | Changing function signatures used by other modules |

### Requirements
| Requirement | Enforced |
|---|---|
| All CI checks pass | ✅ Automated |
| Human review recommended | ⚠️ Recommended (not blocked) |
| Targeted tests for the change | ✅ Automated (coverage gate) |
| PR description explains the "why" | ✅ Convention |
| Auto-merge allowed after CI | ✅ (if human review not requested) |

### Expected Frequency
~20-25% of all PRs. Common during Epics 02-08.

---

## Tier 3: `risk:medium` — YELLOW

### Definition
New functionality that follows established patterns, or modifications to existing features with clear boundaries.

### Criteria
| Criterion | Examples |
|---|---|
| New feature within established patterns | Adding a new score calculator following BaseScoreCalculator |
| New dashboard page following existing layout | Adding discovery.py page like existing opportunities.py |
| New test suite | Adding comprehensive tests for an existing module |
| New export format | Adding Excel export following existing CSV pattern |
| Component additions | New UI component following design system |
| Utility functions | New helpers in utils/ |

### Requirements
| Requirement | Enforced |
|---|---|
| All CI checks pass | ✅ Automated |
| Human review not required | ✅ Self-merge OK |
| Tests for new code | ✅ Automated (coverage gate) |
| Auto-merge allowed | ✅ |

### Expected Frequency
~40-50% of all PRs. The most common tier.

---

## Tier 4: `risk:low` — GREEN

### Definition
Changes with negligible risk of breaking anything. No behavior change or behavior change is trivially verifiable.

### Criteria
| Criterion | Examples |
|---|---|
| Test-only changes | Adding tests, improving test coverage, test refactoring |
| Documentation | README, docstrings, comments, markdown files |
| Configuration values | Changing non-structural config values (thresholds, descriptions) |
| Style/formatting | Ruff auto-fixes, whitespace, import ordering |
| Dependency version bumps | Minor/patch version updates |
| Typo fixes | Spelling corrections in code or docs |
| `.gitignore` updates | Adding new ignore patterns |

### Requirements
| Requirement | Enforced |
|---|---|
| All CI checks pass | ✅ Automated |
| Human review not required | ✅ Self-merge OK |
| Auto-merge allowed | ✅ Immediate after CI green |

### Expected Frequency
~20-25% of all PRs. Common throughout all epics.

---

## Risk Decision Tree

```
Does this PR change database schema or migrations?
  └── YES → risk:critical

Does this PR modify the orchestrator pipeline flow?
  └── YES → risk:critical

Does this PR handle secrets, keys, or authentication?
  └── YES → risk:critical

Does this PR add a new Playwright workflow or external API call?
  └── YES → risk:high

Does this PR change a scoring formula or LLM prompt?
  └── YES → risk:high

Does this PR modify CSS selectors for Fiverr scraping?
  └── YES → risk:high

Does this PR change cross-module interfaces?
  └── YES → risk:high

Does this PR add new functionality following existing patterns?
  └── YES → risk:medium

Does this PR only change tests, docs, config values, or formatting?
  └── YES → risk:low
```

---

## Risk Tier Summary

| Tier | Label | Color | Human Review | Auto-Merge | Rollback Plan | Frequency |
|---|---|---|---|---|---|---|
| Critical | `risk:critical` | Red `#B60205` | Required | Blocked | Required | ~5-10% |
| High | `risk:high` | Orange `#D93F0B` | Recommended | Allowed | Recommended | ~20-25% |
| Medium | `risk:medium` | Yellow `#FBCA04` | Not needed | Allowed | Not needed | ~40-50% |
| Low | `risk:low` | Green `#0E8A16` | Not needed | Allowed | Not needed | ~20-25% |
