# Label Automation
# Fiverr Research System — Automatic Label Application

---

## Auto-Applied Labels

### 1. Size Labels (Applied by CI on every PR)
The `pr-checks.yml` workflow calculates lines changed and applies the correct size label.

**Logic:**
```
additions + deletions (excluding exempted files) → size label
1-10 → size:XS
11-50 → size:S
51-200 → size:M
201-500 → size:L
501-1000 → size:XL
1000+ → size:XXL
```

**Exempted files:** `*.lock`, `*.json` in fixtures/, `*.j2`, `*.yaml` in seeds/, `*.md`, `__init__.py`

### 2. Type Label from PR Title
The `pr-checks.yml` workflow parses the PR title prefix and verifies a matching type label exists:
- `feat(...)` → must have `type:feature` label
- `fix(...)` → must have `type:fix` label
- etc.

If the label is missing, CI posts a comment reminding the agent to add it.

### 3. Scope Label from Branch Name
The workflow parses the branch name:
- `feature/epic01/...` → verify `scope:epic01-foundation` label exists
- `feature/epic02/...` → verify `scope:epic02-collection` label exists

### 4. Stale Label
Applied by a scheduled workflow (runs daily):
- PR with no activity for 3+ days → add `status:stale` label + comment
- Issue with no activity for 7+ days → add `status:stale` label

### 5. Risk Label Suggestion
CI analyzes the files changed and suggests a risk label:

| Files Changed | Suggested Risk |
|---|---|
| `src/models/*.py` (schema changes) | `risk:critical` |
| `src/orchestrator.py` | `risk:critical` |
| `src/collection/session_manager.py` | `risk:high` |
| `src/scoring/*.py` (formula changes) | `risk:high` |
| `src/llm/prompts/*.j2` | `risk:high` |
| `src/collection/workflows/*.py` | `risk:high` |
| `src/dashboard/pages/*.py` | `risk:medium` |
| `src/analysis/*.py` | `risk:medium` |
| `tests/**` | `risk:low` |
| `docs/**` | `risk:low` |
| `*.md` only | `risk:low` |

If no risk label is present, CI posts a comment with the suggested risk level. The agent must add the risk label manually (CI suggests but doesn't auto-apply risk labels since the agent knows context the CI doesn't).

---

## Label Enforcement Rules

### Required Labels (PR cannot merge without these)
| Category | Minimum | Enforced By |
|---|---|---|
| `type:*` | Exactly 1 | pr-checks CI |
| `priority:*` | Exactly 1 | pr-checks CI |
| `scope:*` | At least 1 | pr-checks CI |
| `risk:*` | Exactly 1 | pr-checks CI |
| `size:*` | Exactly 1 (auto-applied) | pr-checks CI |

### Optional Labels (Informational)
| Category | Applied By |
|---|---|
| `status:*` | Agent or automation |
| `agent:*` | Agent or PM |
| `override:*` | Human operator only |

---

## Label Conflict Rules

| Conflict | Resolution |
|---|---|
| Multiple `type:` labels | Error — exactly 1 required |
| Multiple `priority:` labels | Error — exactly 1 required |
| Multiple `risk:` labels | Error — exactly 1 required |
| Multiple `size:` labels | CI removes old, applies new |
| Multiple `scope:` labels | Allowed — PR can touch multiple epics |
| Multiple `status:` labels | Remove old before applying new |
| Multiple `agent:` labels | Allowed — collaboration across agents |
