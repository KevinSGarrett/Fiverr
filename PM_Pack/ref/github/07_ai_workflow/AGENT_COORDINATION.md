# Agent Coordination
# Fiverr Research System — Multi-Agent Conflict Prevention & Handoff Protocol

---

## Core Principle: Directory Ownership Prevents Conflicts

Each agent owns specific directories. This is the PRIMARY conflict prevention mechanism.

### Ownership Rules
1. **Only the owning agent creates/modifies files** in their directories
2. **Other agents may READ** any file but must not modify files they don't own
3. **Cross-boundary changes** require coordination (see Handoff Protocol below)
4. **Shared interfaces** (function signatures, Pydantic models) are frozen after first merge — changes require a coordinated PR

---

## Conflict Prevention Strategies

### Strategy 1: Branch Isolation
Each agent works on branches scoped to their epic:
```
Agent 1: feature/epic01/*   (no overlap with agent 2's feature/epic02/*)
Agent 2: feature/epic02/*
Agent 3: feature/epic04/*
Agent 4: feature/epic09/*
```
Two agents should NEVER work on the same file in parallel.

### Strategy 2: Interface Contracts
Before an agent starts work that DEPENDS on another agent's module, the interface must be defined and merged first.

**Example:** Agent 3 needs `KeywordScore` model from Agent 1.
```
1. Agent 1 creates and merges the model (Epic 01)
2. Model is now on develop
3. Agent 3 pulls develop and can import the model
4. Agent 3 builds scoring logic using the model
```

If Agent 3 needs a change to the model, they:
1. Create an issue describing the needed change
2. Assign to Agent 1
3. Agent 1 makes the change in a new PR
4. After merge, Agent 3 rebases and continues

### Strategy 3: Shared Files Have Single Owners
| Shared File | Owner | Others |
|---|---|---|
| `src/__init__.py` | Agent 1 | Do not modify |
| `src/models/__init__.py` | Agent 1 | Request changes via issue |
| `config.yaml` | Agent 1 | Request new sections via issue |
| `requirements.txt` | Agent 1 | Request new deps via issue |
| `pyproject.toml` | Agent 1 | Request changes via issue |
| `tests/conftest.py` | Agent 1 | Request new fixtures via issue |

### Strategy 4: Import Convention
To avoid circular imports and merge conflicts in `__init__.py`:
```python
# Each module's __init__.py exports its public API
# Only the module owner edits their __init__.py

# src/scoring/__init__.py (owned by Agent 3)
from src.scoring.demand import DemandScoreCalculator
from src.scoring.competition import CompetitionScoreCalculator
# ... etc

# Other agents import FROM the module, never modify the __init__.py
from src.scoring import DemandScoreCalculator
```

---

## Handoff Protocol

When work must pass between agents:

### Standard Handoff (Planned)
```
1. PM creates issue: "Handoff: Agent 1 → Agent 3 — LLM Client ready for prompts"
2. Agent 1 completes their part, merges to develop
3. Agent 1 comments on handoff issue: "Merged in PR #XX. Interface: LLMClient.complete()"
4. PM updates issue: "Ready for Agent 3"
5. Agent 3 pulls develop, picks up work
6. Agent 3 comments when done: "Prompts integrated in PR #YY"
7. PM closes handoff issue
```

### Emergency Handoff (Blocking)
```
1. Blocked agent creates issue: "[BLOCKED] Agent 3 needs config change from Agent 1"
2. Labels: priority:P2-high, status:blocked, agent:1-infrastructure
3. Agent 1 picks up immediately (P2 = same day)
4. Agent 1 creates PR, merges
5. Blocked agent rebases and continues
```

### Cross-Module PR (Rare)
When a single PR MUST touch files owned by different agents:
```
1. Creating agent takes ownership of the PR
2. PR description lists all files modified and why
3. PR gets risk:high label minimum
4. Human review recommended
5. Other affected agents are mentioned in PR body
```

---

## Daily Agent Sync Protocol

Since agents are AI, coordination happens via GitHub:

### Morning Start (Each Agent)
```bash
# 1. Pull latest develop
git checkout develop
git pull origin develop

# 2. Check assigned issues
# → Filter: assignee=self, status != closed

# 3. Check for blocking issues
# → Filter: label=status:blocked, mentions self

# 4. Start highest-priority unblocked issue
git checkout -b feature/epicXX/SX.X-description
```

### Before Creating a PR
```bash
# 1. Rebase from develop (catch any new merges)
git fetch origin
git rebase origin/develop

# 2. Run local checks
ruff check src/ tests/
mypy src/
pytest tests/ -x

# 3. If all pass → push and create PR
git push -u origin feature/epicXX/SX.X-description
```

---

## Dependency Graph Between Agents

```
Agent 1 (Foundation)
   │
   ├──→ Agent 2 (Collection) — needs models, config, database
   │       │
   ├──→ Agent 3 (Analysis) — needs models, config, LLM client
   │       │    needs collection data (from Agent 2)
   │       │
   └──→ Agent 4 (Dashboard) — needs models, config
            needs scores (from Agent 3)
            needs collection data (from Agent 2)
```

### Critical Path
```
Agent 1 finishes Epic 01
  → Agent 2 can start Epic 02 + Agent 3 can start Epic 03
    → Agent 3 can start Epic 04 (after Epic 03 base)
      → Agent 4 can start Epic 08 (after scoring available)
        → Agent 4 can start Epic 09 (after most modules available)
          → All agents contribute to Epic 10
```

---

## Communication Conventions

### Issue Comments
```markdown
<!-- Starting work -->
🟢 Starting work on S4.1 — DemandScoreCalculator
Branch: feature/epic04/S4.1-demand-score

<!-- Blocked -->
🔴 BLOCKED — Need KeywordScoreInput model from Agent 1
See #12 for details

<!-- Completed -->
✅ Completed S4.1 — Merged in PR #55

<!-- Handoff ready -->
🔄 Handoff ready — LLMClient.complete() is on develop
Agent 3 can now implement prompts
```

### PR Cross-References
```markdown
<!-- In PR description -->
Depends on: #12 (must be merged first)
Blocks: #55, #56 (waiting on this PR)
Related: #47, #48 (same epic, no dependency)
```
