====================================================================
AGENT C — CYCLE 024 PROMPT
====================================================================

## PROJECT CONTEXT
- Project: Fiverr Research System | GitHub: https://github.com/KevinSGarrett/Fiverr
- Local: C:\Fiverr\Fiverr | Branch: cycle/024/integration
- Python 3.11+ | asyncio | SQLAlchemy 2.0

## ⚠️ HARD GATE + COLLECTION PIVOT
codecov/patch ≥ 90% is hard merge blocker. Run targeted coverage before handoff.
All collection workflow functions must accept dry_run=True parameter for smoke safety.

## YOUR ROLE
Agent C builds PacingManager and the first two collection workflow stubs:
- Workflow 1: Niche Initialization (Stage 1)
- Workflow 2: Keyword Expansion (Stage 2 stub — structure + interface, no real Playwright)
Spec: PM_Pack/ref/project_plan/04_collection/PACING_MODEL.md (read first)
      PM_Pack/ref/project_plan/04_collection/COLLECTION_WORKFLOWS.md (Workflows 1-2)

## GIT INSTRUCTIONS
1. Ensure on: cycle/024/integration. Pull latest.
2. Read Agents A + B handoffs before coding.
3. All work on cycle/024/integration.
4. Commit: feat(collection): PacingManager and Workflows 1-2 [Agent C Cycle 024]
5. Do NOT push.

## MANDATORY POWERSHELL PREFLIGHT
  Get-Location; git rev-parse --show-toplevel; git branch --show-current
  git log --oneline -8; git worktree list
  python -m pytest -q tests/unit/test_session_manager.py tests/unit/test_queue_processor.py
Pass: all Agent A+B tests pass.

## TASKS

### Task 1: Preflight + read all handoffs + read spec files
Read: docs/cycle_reports/CYCLE_024_AGENT_A.md, CYCLE_024_AGENT_B.md
Read: PM_Pack/ref/project_plan/04_collection/PACING_MODEL.md (full file)
Read: PM_Pack/ref/project_plan/04_collection/COLLECTION_WORKFLOWS.md (Workflows 1 and 2)
Read: PM_Pack/ref/project_plan/04_collection/RETRY_AND_CHECKPOINT.md

### Task 2: Read E02 S2.3 + S2.4 Jira stories before coding
Query SCRUM-17 children → find S2.3 (Pacing) and S2.4 (Workflows/stages) story keys.
Read full AC/DoD for each. Transition to In Progress. Post planning comments.

### Task 3: Create src/collection/pacing.py — PacingManager
Spec: PM_Pack/ref/project_plan/04_collection/PACING_MODEL.md

class PacingManager:
  """
  Manages request pacing to avoid detection and rate limits.
  Config-driven delays with jitter. All waits are async.
  """
  def __init__(self, config: dict):
    self.config = config
    self.pacing = config.get("pacing", {})
    self._hourly_counts: dict[str, list[float]] = {}  # {pacing_key: [timestamps]}

  async def wait(self, pacing_key: str, dry_run: bool = False) -> float:
    """
    Waits for the appropriate delay for the given pacing key.
    Returns the actual delay applied (seconds).
    If dry_run=True: skips the actual sleep, returns 0.0.
    """
    if dry_run:
      return 0.0
    cfg = self.pacing.get(pacing_key, self.pacing.get("default", {}))
    base = float(cfg.get("base_delay_seconds", 2.0))
    jitter_max = float(cfg.get("jitter_seconds", 1.0))
    import random, asyncio
    delay = base + random.uniform(0.0, jitter_max)
    await asyncio.sleep(delay)
    self._record_request(pacing_key)
    return delay

  def _record_request(self, pacing_key: str) -> None:
    """Records a request timestamp for hourly rate tracking."""
    import time
    now = time.time()
    if pacing_key not in self._hourly_counts:
      self._hourly_counts[pacing_key] = []
    self._hourly_counts[pacing_key].append(now)
    # Purge entries older than 1 hour
    cutoff = now - 3600
    self._hourly_counts[pacing_key] = [t for t in self._hourly_counts[pacing_key] if t > cutoff]

  def requests_in_last_hour(self, pacing_key: str) -> int:
    """Returns count of requests made in the last hour for this pacing key."""
    import time
    now = time.time()
    cutoff = now - 3600
    return sum(1 for t in self._hourly_counts.get(pacing_key, []) if t > cutoff)

  def get_delay_config(self, pacing_key: str) -> dict:
    """Returns pacing config for the given key (for logging/audit)."""
    return self.pacing.get(pacing_key, self.pacing.get("default", {}))

### Task 4: Create src/collection/workflows/__init__.py
Export: run_niche_initialization, run_keyword_expansion_stub

### Task 5: Create src/collection/workflows/niche_init.py — Workflow 1
Spec: COLLECTION_WORKFLOWS.md "Workflow 1 — Niche Initialization (Stage 1)"

async def run_niche_initialization(
  config: dict,
  db,
  run_id: str,
  dry_run: bool = True,
) -> dict:
  """
  Stage 1: Niche Initialization.
  Loads niches from config, resolves depth settings, applies gate checks,
  creates/updates niche_config rows, loads seed keywords.
  Returns: {"niches_processed": int, "niche_specs": list[dict], "seed_keywords": dict}
  dry_run=True (default): reads config and DB, returns spec without creating jobs.
  """
  from src.config.loader import load_config  # use existing config loader
  niches_processed = 0
  niche_specs = []
  seed_keywords = {}

  niches = config.get("niches", [])
  if isinstance(niches, list):
    niche_list = niches
  else:
    niche_list = list(niches.values()) if isinstance(niches, dict) else []

  for niche in niche_list:
    niche_id = getattr(niche, "niche_id", None) or (niche.get("niche_id") if isinstance(niche, dict) else None)
    if not niche_id:
      continue

    # Resolve depth (spec: check niche_configs table for runtime override)
    depth = _resolve_niche_depth(niche_id, niche, db)

    # Apply gate check (spec: force keyword_only if gate not passed)
    depth = _apply_gate_check(niche_id, niche, depth, db)

    # Load seed keywords
    seeds = _load_seeds(niche)
    seed_keywords[niche_id] = seeds

    niche_spec = {
      "niche_id": niche_id,
      "depth": depth,
      "seed_count": len(seeds),
      "seeds": seeds if not dry_run else seeds[:3],  # limit preview in dry_run
    }
    niche_specs.append(niche_spec)
    niches_processed += 1

  return {
    "niches_processed": niches_processed,
    "niche_specs": niche_specs,
    "seed_keywords": seed_keywords,
    "dry_run": dry_run,
  }

def _resolve_niche_depth(niche_id: str, niche, db) -> str:
  """Returns depth from niche_configs DB table or config default."""
  try:
    from sqlalchemy.orm import Session
    from src.models.niche import NicheConfig  # use existing model
    if isinstance(db, Session):
      nc = db.query(NicheConfig).filter(NicheConfig.niche_id == niche_id).first()
      if nc and nc.current_depth:
        return nc.current_depth
  except Exception:
    pass
  depth = getattr(niche, "depth", None)
  if isinstance(niche, dict):
    depth = niche.get("depth", "standard")
  return depth or "standard"

def _apply_gate_check(niche_id: str, niche, depth: str, db) -> str:
  """Applies gate logic: if gating.enabled and gate not passed → keyword_only."""
  gating = getattr(niche, "gating", {}) if hasattr(niche, "gating") else {}
  if isinstance(niche, dict):
    gating = niche.get("gating", {})
  if gating.get("enabled", False) and not gating.get("gate_passed", True):
    return "keyword_only"
  return depth

def _load_seeds(niche) -> list[str]:
  """Loads seed keywords from niche config."""
  seeds = getattr(niche, "seed_keywords", []) if hasattr(niche, "seed_keywords") else []
  if isinstance(niche, dict):
    seeds = niche.get("seed_keywords", [])
  return [s.strip() for s in seeds if s and s.strip()]

### Task 6: Create src/collection/workflows/keyword_expansion.py — Workflow 2 stub
Spec: COLLECTION_WORKFLOWS.md "Workflow 2 — Keyword Expansion Per Niche (Stage 2)"

async def run_keyword_expansion(
  niche_id: str,
  seeds: list[str],
  depth: str,
  run_id: str,
  db,
  session_manager,
  pacing_manager,
  dry_run: bool = True,
) -> dict:
  """
  Stage 2: Keyword Expansion Per Niche.
  Steps 2a-2g from spec (autocomplete, Google suggest, LLM generation, etc.)
  In dry_run=True mode: returns stub result without any real browser/LLM calls.
  Returns: {"niche_id": str, "keywords_queued": int, "sources": dict, "dry_run": bool}
  """
  if dry_run:
    # Stub: simulate keyword expansion without real browser or LLM calls
    return {
      "niche_id": niche_id,
      "keywords_queued": 0,
      "sources": {
        "fiverr_autocomplete": 0,
        "google_suggest": 0,
        "llm_generated": 0,
      },
      "dry_run": True,
      "note": "Dry run: no real Playwright or LLM calls made",
    }

  # Non-dry-run: placeholder for real implementation (future cycle)
  raise NotImplementedError(
    "Keyword expansion with real Playwright not yet implemented. "
    "Set dry_run=True for stub execution."
  )

### Task 7: Write tests for PacingManager and collection workflows
Create: tests/unit/test_pacing.py (pacing tests)
Create: tests/unit/test_collection_workflows.py (workflow tests)

tests/unit/test_pacing.py (minimum 8 tests):
- test_pacing_manager_wait_dry_run — wait(key, dry_run=True) → 0.0, no sleep
- test_pacing_manager_wait_uses_config — config base_delay=0.01 → delay ≈ 0.01
  (use very small delay so test doesn't take long)
- test_pacing_manager_records_request — _record_request tracked in _hourly_counts
- test_pacing_manager_hourly_count — requests_in_last_hour increments
- test_pacing_manager_purges_old_entries — old timestamps removed from counts
- test_pacing_manager_default_config — missing pacing_key uses "default" config
- test_pacing_manager_get_delay_config — returns correct config dict for key
- test_pacing_manager_zero_delay_config — base_delay=0.0 → wait returns quickly

tests/unit/test_collection_workflows.py (minimum 10 tests):
- test_niche_init_empty_niches — empty niches list → {"niches_processed": 0}
- test_niche_init_single_niche — one niche with seeds → niche_spec returned
- test_niche_init_seed_loading — seeds extracted correctly from niche config
- test_niche_init_depth_resolved — depth from niche config used
- test_niche_init_gate_check_applied — gating.enabled=True, gate_passed=False → keyword_only
- test_niche_init_gate_check_passed — gating.gate_passed=True → depth unchanged
- test_niche_init_dry_run_default — dry_run=True is default
- test_keyword_expansion_dry_run — dry_run=True → returns stub result
- test_keyword_expansion_raises_without_dry_run — dry_run=False → NotImplementedError
- test_workflow_niche_id_in_result — result contains "niche_id" key

### Task 8: Run targeted patch coverage
python -m pytest -q --cov=src.collection.pacing --cov-report=term-missing
python -m pytest -q --cov=src.collection.workflows --cov-report=term-missing
All new code ≥ 90% covered.

### Task 9: Run full validation block
All 6 commands. Target: ≥ 1209 tests. Coverage ≥ 90%.

### Task 10: Post Jira evidence for E02 S2.3 + S2.4
S2.3 (Pacing): "PacingManager implemented. dry_run=True bypasses sleep. Config-driven delays.
  Hourly rate tracking. 8 tests. All smoke-safe."
S2.4 (Workflows): "Workflow 1 (Niche Init) implemented. Workflow 2 stub with dry_run guard.
  Stage 1 resolves depth, applies gate check, loads seeds from config. 10 tests."

### Tasks 11-16: Standard completion
11. Update ACTIVE_STORY_DOD_LEDGER.md.
12. Artifact hygiene check.
13. No-main / worktree check. Record SHA.
14. Create docs/cycle_reports/CYCLE_024_AGENT_C.md.
15. Commit scoped files.
16. Run python run.py phase2-smoke → must pass.

## COMMIT INSTRUCTIONS
git add src/collection/pacing.py src/collection/workflows/
git add tests/unit/test_pacing.py tests/unit/test_collection_workflows.py
git add docs/jira/ACTIVE_STORY_DOD_LEDGER.md docs/cycle_reports/CYCLE_024_AGENT_C.md
git commit -m "feat(collection): PacingManager and Workflows 1-2 [Agent C Cycle 024]"
====================================================================
END OF AGENT C PROMPT
====================================================================
