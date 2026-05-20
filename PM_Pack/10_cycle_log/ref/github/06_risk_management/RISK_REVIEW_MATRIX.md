# Risk Review Matrix
# Fiverr Research System — What Gets Reviewed, By Whom, and How

---

## Review Matrix by Risk Tier

| Dimension | `risk:critical` | `risk:high` | `risk:medium` | `risk:low` |
|---|---|---|---|---|
| **CI checks** | All required | All required | All required | All required |
| **Human review** | REQUIRED | Recommended | Not needed | Not needed |
| **Auto-merge** | BLOCKED | Allowed | Allowed | Allowed |
| **Rollback plan** | REQUIRED in PR body | Recommended | Not needed | Not needed |
| **Integration tests** | Required for change | Recommended | Not needed | Not needed |
| **Spec compliance check** | Required | Required | Recommended | Not needed |
| **Manual QA** | Recommended | Optional | Not needed | Not needed |
| **Max PR size** | 500 lines | 500 lines | 1000 lines | No limit |
| **Merge delay** | After human approval | Immediate if CI green | Immediate | Immediate |

---

## File-to-Risk Mapping

This table maps specific file paths to their default risk tier. CI uses this to suggest risk labels.

### Critical Files
| File Pattern | Why Critical |
|---|---|
| `src/models/*.py` | Schema = data integrity |
| `src/models/database.py` | Connection/session = everything depends on it |
| `src/models/init_db.py` | DB initialization = destructive potential |
| `src/orchestrator.py` | Pipeline core = everything flows through it |
| `src/config/loader.py` | Config parsing = all modules depend on it |
| `src/config/models.py` | Config schema = structural change |
| `alembic/versions/*.py` | Migrations = irreversible data changes |
| `.env*` | Secrets exposure |
| `pyproject.toml` [dep changes] | Dependency changes can break everything |

### High-Risk Files
| File Pattern | Why High |
|---|---|
| `src/collection/session_manager.py` | Browser lifecycle = fragile |
| `src/collection/selectors.py` | Fiverr site changes break selectors |
| `src/collection/pacing.py` | Rate limiting = ban risk |
| `src/collection/workflows/*.py` | External API calls = unpredictable |
| `src/scoring/*.py` | Formulas = affects all downstream decisions |
| `src/llm/client.py` | LLM interface = cost and quality |
| `src/llm/cache.py` | Cache logic = cost savings |
| `src/llm/prompts/*.j2` | Prompt quality = recommendation quality |
| `src/collection/queue.py` | Job processing = pipeline throughput |
| `src/collection/checkpoint.py` | Resume logic = data continuity |

### Medium-Risk Files
| File Pattern | Why Medium |
|---|---|
| `src/analysis/*.py` | Analysis logic within established patterns |
| `src/pricing/*.py` | Pricing calculations |
| `src/discovery/*.py` | Discovery logic |
| `src/playbook/*.py` | Playbook generation |
| `src/dashboard/pages/*.py` | New UI pages |
| `src/dashboard/components.py` | UI components |
| `src/exports/*.py` | Export formats |
| `src/reports/*.py` | Alert and reporting logic |
| `src/utils/*.py` | Shared utilities |

### Low-Risk Files
| File Pattern | Why Low |
|---|---|
| `tests/**/*.py` | Tests can't break production |
| `docs/**/*.md` | Documentation only |
| `*.md` (root) | README, CHANGELOG, etc. |
| `src/dashboard/styles.py` | CSS only |
| `.github/**` | CI/CD config (meta, not code) |
| `data/seeds/*.yaml` | Seed data |
| `tests/fixtures/*` | Test fixtures |

---

## Escalation Procedures

### When Risk Tier Disagrees with Agent Assessment

If an agent believes the auto-suggested risk is wrong:

1. **Agent applies their assessed risk label** (overriding suggestion)
2. **Agent adds a comment** explaining why: "CI suggested `risk:high` but this change only adds a test for an existing function → `risk:low`"
3. **If upgrading risk** (low → medium, medium → high): just apply the higher label
4. **If downgrading risk** (high → medium, critical → high): must explain in PR body

### When Multiple Files Span Risk Tiers

If a PR touches files across risk tiers, use the **highest** tier:
- Modifying `src/models/keyword.py` (critical) + `tests/unit/test_models.py` (low) → `risk:critical`
- Modifying `src/scoring/demand.py` (high) + `src/dashboard/pages/keywords.py` (medium) → `risk:high`

### Escalation to Human

| Trigger | Action |
|---|---|
| Agent is uncertain about risk | Apply higher tier + request human review |
| CI and agent disagree | Agent explains in comment; human decides if involved |
| `risk:critical` PR fails CI | Do NOT override — fix the failure |
| Emergency (`override:emergency`) | Human must apply label and document reason |

---

## Risk Metrics (Tracked in Run Log)

| Metric | Target | Alert Threshold |
|---|---|---|
| % of PRs with risk label | 100% | < 100% → blocked by CI |
| % of critical PRs with human review | 100% | < 100% → process failure |
| Average time to merge by tier | Low: < 1hr, Med: < 2hr, High: < 4hr, Critical: < 8hr | 2x target |
| Risk downgrades without explanation | 0 | Any → flag for review |
| Emergency overrides per month | ≤ 1 | > 2 → process review |
