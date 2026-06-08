# CYCLE 072 — AGENT B PROMPT
# Wave 10 S7.8 Stage 16 Orchestration
# Role: SOLE src/ author. Creates stage16.py and test file.
# §12.1 PARALLEL: B and E run IN PARALLEL after A.
# POLICY v4.3: 55 LARGE-XXLARGE tasks | Floor: 1,200 lines

## PROJECT CONTEXT
- Branch: cycle/072/integration | Base SHA: 2b4e320
- Python: C:\Users\kevin\AppData\Local\Programs\Python\Python311\python.exe
- Suite at start: 5140 passed | 94.02% | Floor: 90%
- C072 story: SCRUM-203 | Parent: SCRUM-22
- S7.8: ORCHESTRATE stage — wires S7.2-S7.7 into run_discovery_cycle()
- orchestrator.py EXISTS as stub — DO NOT MODIFY IT

## INVOKE-EXE HELPER
```powershell
function Invoke-Exe { param([string]$File,[string]$ArgString)
  $psi = New-Object System.Diagnostics.ProcessStartInfo
  $psi.FileName=$File; $psi.WorkingDirectory='C:\Fiverr\Fiverr'
  $psi.Arguments=$ArgString; $psi.RedirectStandardOutput=$true
  $psi.RedirectStandardError=$true; $psi.UseShellExecute=$false
  $psi.CreateNoWindow=$true; $p=[System.Diagnostics.Process]::Start($psi)
  $o=$p.StandardOutput.ReadToEnd(); $e=$p.StandardError.ReadToEnd()
  $p.WaitForExit(); return [pscustomobject]@{Out=$o;Err=$e;Exit=$p.ExitCode} }
$git='C:\Program Files\Git\cmd\git.exe'
```

## HARD GATES
- G-001: pytest --cov=src --cov-fail-under=90
- G-005: kw=110 → 62.7/1.0/CONDITIONAL_GO
- NO NEW MIGRATION: DiscoveryCycleLog table from migration_14 (C070)
- DO NOT TOUCH orchestrator.py

## PREFLIGHT
```powershell
Invoke-Exe $git 'pull origin cycle/072/integration'
Invoke-Exe $git 'log --oneline -5'
C:\Users\kevin\AppData\Local\Programs\Python\Python311\python.exe run.py config-check
```

## TASK 1 — SURVEY EXISTING ORCHESTRATOR (DO NOT MODIFY)
```python
import ast
tree = ast.parse(open('src/discovery/orchestrator.py', encoding='utf-8').read())
fns = {n.name: (ast.get_docstring(n) or '')[:80]
       for n in ast.walk(tree) if isinstance(n, ast.FunctionDef)}
for name, doc in fns.items():
    stub = 'stub' in doc.lower() or 'Stub' in doc
    print(f"  {name}: {'STUB' if stub else 'IMPL'} — {doc[:50]}")
print("B does NOT modify orchestrator.py. Creates stage16.py instead.")
```

## TASK 2 — VERIFY DiscoveryCycleLog SCHEMA
```python
from src.models import DiscoveryCycleLog
import sqlalchemy as sa
mapper = sa.inspect(DiscoveryCycleLog)
cols = [c.key for c in mapper.column_attrs]
required = ['run_id', 'modes_run', 'hypotheses_generated', 'hypotheses_gated',
            'hypotheses_accepted', 'total_cost_usd', 'feedback_summary', 'cycle_at']
for col in required:
    print(f"  {col}: {'PRESENT' if col in cols else 'MISSING'}")
print(f"PASS: DiscoveryCycleLog has {len(cols)} total columns")
```

## TASK 3 — VERIFY ALL PREREQUISITE SYMBOLS
```python
from src.discovery.hypothesis import (generate_adjacent_keyword_hypotheses,
    generate_adjacent_niche_hypotheses, generate_gap_exploit_hypotheses,
    generate_trend_chase_hypotheses)
from src.discovery.feedback import evaluate_discovery_results, build_feedback_summary
from src.discovery.integration import (process_accepted_hypotheses,
    get_pending_discovery_keywords)
from src.models import DiscoveryCycleLog, Keyword, KeywordScore
print("PASS: all S7.2-S7.7 prerequisites importable at C072 base")
```

## TASK 4 — SURVEY run.py FOR CLI PATTERN
```python
import ast
content = open('run.py', encoding='utf-8').read()
# Find CLI framework
has_click = '@click' in content or 'import click' in content
has_argparse = 'argparse' in content
has_discover = 'discover' in content
print(f"CLI: click={has_click} argparse={has_argparse} discover_cmd={has_discover}")
# Find existing mode dispatch
mode_lines = [l.strip() for l in content.splitlines() if '--mode' in l.lower() or 'discover' in l.lower()]
print(f"Mode-related lines: {mode_lines[:8]}")
```

## TASK 5 — CREATE src/discovery/stage16.py
```python
"""Stage 16: Discovery Engine orchestration.

Wires the complete S7.1-S7.7 discovery loop into a single callable function:

  1. evaluate_discovery_results()  — classify previously scored discoveries (S7.6)
  2. build_feedback_summary()      — aggregate feedback context (S7.6)
  3. _select_modes()               — which hypothesis modes this cycle
  4. generate_*_hypotheses()       — produce candidates (S7.2-S7.5)
  5. Budget gate                   — filter by confidence, cap at max
  6. process_accepted_hypotheses() — insert to keyword table (S7.7)
  7. DiscoveryCycleLog             — persist cycle record

No LLM calls. Pure data analysis + keyword table inserts.
No new migration required (DiscoveryCycleLog from migration_14 / C070).
Does NOT modify src/discovery/orchestrator.py (SRDI legacy, untouched).
"""
from __future__ import annotations

import json
import logging
import uuid
from datetime import datetime
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    pass

log = logging.getLogger(__name__)

DEFAULT_MIN_CONFIDENCE: float = 0.50
DEFAULT_MAX_HYPOTHESES: int = 15

# Modes that run every cycle
_BASE_MODES = ["adjacent_keyword", "gap_exploit", "trend_chase"]
# Modes that run every Nth cycle
_PERIODIC_MODES = {3: "adjacent_niche"}
```

## TASK 6 — IMPLEMENT _select_modes
```python
def _select_modes(
    config: dict[str, Any] | None = None,
    run_number: int | None = None,
) -> list[str]:
    """Select which hypothesis modes to run this discovery cycle.

    Base modes (every run): adjacent_keyword, gap_exploit, trend_chase.
    Periodic modes: adjacent_niche every 3rd run (run_number % 3 == 0).

    Args:
        config: Optional config dict with 'discovery.enabled_modes' override.
        run_number: Current cycle number for periodic mode scheduling.
                    If None, only base modes run.

    Returns:
        List of mode name strings to run this cycle.
    """
    modes = list(_BASE_MODES)
    if run_number is not None:
        for period, mode in _PERIODIC_MODES.items():
            if run_number % period == 0:
                modes.append(mode)
    # Apply config override if present
    enabled = (config or {}).get("discovery", {}).get("enabled_modes")
    if enabled and isinstance(enabled, list):
        modes = [m for m in modes if m in enabled]
    return modes
```

## TASK 7 — IMPLEMENT _build_seed_data HELPER
```python
def _build_seed_data(
    niche_id: str,
    db: Any,
    modes: list[str],
) -> dict[str, Any]:
    """Query DB for the data each hypothesis mode needs as input.

    Returns a dict with keys matching what each generate_*_hypotheses() expects.
    Handles missing data gracefully (returns empty lists, not errors).

    Args:
        niche_id: The niche to query seed data for.
        db: SQLAlchemy session.
        modes: List of mode names to prepare data for.

    Returns:
        Dict with keys: seed_keywords, gap_signals, trend_signals, existing_kw_texts
    """
    from src.models import Keyword, KeywordScore

    # Get existing keyword texts for deduplification
    try:
        existing_kws = db.query(Keyword).filter(
            Keyword.niche_id == niche_id,
            Keyword.is_discovery == False,
        ).limit(50).all()
        existing_kw_texts = [kw.keyword_text for kw in existing_kws if kw.keyword_text]
    except Exception:
        existing_kw_texts = []

    # Seed keywords for adjacent_keyword mode
    seed_keywords = existing_kw_texts[:20]

    # Gap signals for gap_exploit mode
    gap_signals = []
    if "gap_exploit" in modes:
        try:
            score_rows = (db.query(Keyword, KeywordScore)
                          .join(KeywordScore, Keyword.id == KeywordScore.keyword_id)
                          .filter(Keyword.niche_id == niche_id)
                          .limit(30).all())
            gap_signals = [
                {
                    "keyword": kw.keyword_text,
                    "demand_score": getattr(ks, "demand_score", 0.5) or 0.5,
                    "competition_score": getattr(ks, "competition_score", 0.5) or 0.5,
                    "opportunity_score": getattr(ks, "opportunity_score", 0.5) or 0.5,
                }
                for kw, ks in score_rows
                if kw.keyword_text
            ]
        except Exception as exc:
            log.debug("gap_exploit seed data unavailable: %s", exc)

    # Trend signals for trend_chase mode
    trend_signals = []
    if "trend_chase" in modes:
        try:
            score_rows = (db.query(Keyword, KeywordScore)
                          .join(KeywordScore, Keyword.id == KeywordScore.keyword_id)
                          .filter(Keyword.niche_id == niche_id)
                          .limit(20).all())
            trend_signals = [
                {
                    "keyword": kw.keyword_text,
                    "trend_score": getattr(ks, "trend_score", 0.5) or 0.5,
                    "trend_velocity": getattr(ks, "trend_velocity", 0.3) or 0.3,
                    "opportunity_score": getattr(ks, "opportunity_score", 0.5) or 0.5,
                }
                for kw, ks in score_rows
                if kw.keyword_text
            ]
        except Exception as exc:
            log.debug("trend_chase seed data unavailable: %s", exc)

    return {
        "seed_keywords": seed_keywords,
        "gap_signals": gap_signals,
        "trend_signals": trend_signals,
        "existing_kw_texts": existing_kw_texts,
    }
```

## TASK 8 — IMPLEMENT _generate_all_hypotheses HELPER
```python
def _generate_all_hypotheses(
    niche_id: str,
    modes: list[str],
    seed_data: dict[str, Any],
    min_confidence: float,
) -> tuple[list[Any], int]:
    """Generate hypotheses from all active modes for one niche.

    Calls each mode's generate_*_hypotheses() function.
    Handles individual mode failures gracefully — one mode failing
    does not stop other modes from running.

    Args:
        niche_id: Target niche.
        modes: List of mode names to run.
        seed_data: Pre-queried DB data (from _build_seed_data).
        min_confidence: Minimum specificity_score for hypothesis to pass gate.

    Returns:
        (all_hypotheses, hypotheses_gated_count) tuple.
        hypotheses_gated_count = rejected below min_confidence.
    """
    from src.discovery.hypothesis import (
        generate_adjacent_keyword_hypotheses,
        generate_adjacent_niche_hypotheses,
        generate_gap_exploit_hypotheses,
        generate_trend_chase_hypotheses,
    )

    all_hypotheses: list[Any] = []

    if "adjacent_keyword" in modes:
        try:
            h = generate_adjacent_keyword_hypotheses(
                niche_id, seed_data["seed_keywords"], seed_data["existing_kw_texts"])
            all_hypotheses.extend(h)
            log.debug("adjacent_keyword: %d hypotheses for %s", len(h), niche_id)
        except Exception as exc:
            log.warning("adjacent_keyword failed for %s: %s", niche_id, exc)

    if "adjacent_niche" in modes:
        try:
            h = generate_adjacent_niche_hypotheses(niche_id, [], seed_data["existing_kw_texts"])
            all_hypotheses.extend(h)
            log.debug("adjacent_niche: %d hypotheses for %s", len(h), niche_id)
        except Exception as exc:
            log.warning("adjacent_niche failed for %s: %s", niche_id, exc)

    if "gap_exploit" in modes:
        try:
            h = generate_gap_exploit_hypotheses(
                niche_id, seed_data["gap_signals"], seed_data["existing_kw_texts"])
            all_hypotheses.extend(h)
            log.debug("gap_exploit: %d hypotheses for %s", len(h), niche_id)
        except Exception as exc:
            log.warning("gap_exploit failed for %s: %s", niche_id, exc)

    if "trend_chase" in modes:
        try:
            h = generate_trend_chase_hypotheses(
                niche_id, seed_data["trend_signals"], seed_data["existing_kw_texts"])
            all_hypotheses.extend(h)
            log.debug("trend_chase: %d hypotheses for %s", len(h), niche_id)
        except Exception as exc:
            log.warning("trend_chase failed for %s: %s", niche_id, exc)

    # Budget gate: count how many were below confidence threshold
    passing = [h for h in all_hypotheses
               if getattr(h, "accepted", False)
               and (getattr(h, "specificity_score", 0.0) or 0.0) >= min_confidence]
    gated = len(all_hypotheses) - len(passing)
    return all_hypotheses, gated
```

## TASK 9 — IMPLEMENT run_discovery_cycle (CORE FUNCTION)
```python
def run_discovery_cycle(
    db: Any,
    run_id: str | None = None,
    config: dict[str, Any] | None = None,
) -> Any:
    """Execute one complete autonomous discovery cycle.

    Orchestrates the full S7.1-S7.7 chain in sequence:
      1. evaluate_discovery_results()  — classify previously scored discovery keywords
      2. build_feedback_summary()      — build feedback context for hypothesis generation
      3. _select_modes()               — determine which modes to run this cycle
      4. For each niche:
         a. _build_seed_data()         — query keyword/score data for this niche
         b. _generate_all_hypotheses() — generate candidates via S7.2-S7.5 functions
      5. Budget gate                   — filter to min_confidence, cap at max_hypotheses
      6. process_accepted_hypotheses() — insert to keyword table via S7.7
      7. Create DiscoveryCycleLog      — persist cycle record
      8. Return DiscoveryCycleLog

    Args:
        db: SQLAlchemy session.
        run_id: Unique run identifier. Generated if not provided.
        config: Optional config dict with 'discovery' section.

    Returns:
        DiscoveryCycleLog instance (committed to DB).
    """
    from src.discovery.feedback import evaluate_discovery_results, build_feedback_summary
    from src.discovery.integration import process_accepted_hypotheses, get_pending_discovery_keywords
    from src.models import DiscoveryCycleLog
    from src.analysis.result_set_validator import NICHE_VALIDATION_CONFIG

    if run_id is None:
        run_id = f"discovery-{datetime.utcnow().strftime('%Y%m%d-%H%M%S')}-{str(uuid.uuid4())[:8]}"

    disc_config = (config or {}).get("discovery", {})
    min_confidence = disc_config.get("min_hypothesis_confidence", DEFAULT_MIN_CONFIDENCE)
    max_hypotheses = disc_config.get("max_hypotheses_per_run", DEFAULT_MAX_HYPOTHESES)

    log.info("Stage 16: starting discovery cycle run_id=%s", run_id)

    # Step 1+2: Evaluate previous results and build feedback context
    try:
        evaluate_discovery_results(run_id, db)
    except Exception as exc:
        log.warning("evaluate_discovery_results failed (non-fatal): %s", exc)

    try:
        feedback_dict = build_feedback_summary(db)
    except Exception as exc:
        log.warning("build_feedback_summary failed (non-fatal): %s", exc)
        feedback_dict = {"total_hypotheses": 0, "note": "feedback unavailable"}

    # Step 3: Mode selection
    pending_count = len(get_pending_discovery_keywords(db))
    modes = _select_modes(config)
    log.info("Stage 16: modes=%s pending_keywords=%d", modes, pending_count)

    # Step 4: Generate hypotheses across all niches
    all_hypotheses: list[Any] = []
    total_gated = 0

    for niche_id in NICHE_VALIDATION_CONFIG.keys():
        seed_data = _build_seed_data(niche_id, db, modes)
        niche_hypotheses, gated = _generate_all_hypotheses(
            niche_id, modes, seed_data, min_confidence)
        all_hypotheses.extend(niche_hypotheses)
        total_gated += gated
        log.debug("Niche %s: %d hypotheses, %d gated", niche_id, len(niche_hypotheses), gated)

    total_generated = len(all_hypotheses)
    log.info("Stage 16: %d total hypotheses, %d gated", total_generated, total_gated)

    # Step 5: Budget gate — cap at max_hypotheses
    accepted = [h for h in all_hypotheses
                if getattr(h, "accepted", False)
                and (getattr(h, "specificity_score", 0.0) or 0.0) >= min_confidence
               ][:max_hypotheses]
    total_gated = total_generated - len(accepted)

    # Step 6: Insert accepted hypotheses
    try:
        insert_result = process_accepted_hypotheses(accepted, run_id, db)
    except Exception as exc:
        log.error("process_accepted_hypotheses failed: %s", exc)
        insert_result = {"inserted": 0, "skipped": 0, "run_id": run_id, "keyword_ids": []}

    log.info("Stage 16: inserted=%d skipped=%d", insert_result["inserted"], insert_result["skipped"])

    # Step 7: Create cycle log
    cycle_log = DiscoveryCycleLog(
        run_id=run_id,
        modes_run=json.dumps(modes),
        hypotheses_generated=total_generated,
        hypotheses_gated=total_gated,
        hypotheses_accepted=insert_result["inserted"],
        total_cost_usd=0.0,
        feedback_summary=json.dumps(feedback_dict),
        cycle_at=datetime.utcnow(),
    )
    db.add(cycle_log)
    db.commit()

    log.info("Stage 16: cycle complete. DiscoveryCycleLog saved. run_id=%s", run_id)
    return cycle_log
```

## TASK 10 — WIRE CLI IN run.py
```python
# Find the CLI entry point in run.py and add:
# @cli.command("discover")
# @click.option("--run-id", default=None, help="Discovery run ID (generated if not provided)")
# def discover(run_id):
#     """Run Stage 16 discovery cycle."""
#     from src.discovery.stage16 import run_discovery_cycle
#     from src.database import get_db_session
#     with get_db_session() as db:
#         cycle_log = run_discovery_cycle(db, run_id=run_id)
#         click.echo(f"Discovery complete: {cycle_log.hypotheses_accepted} keywords inserted")
```
B must adapt to actual CLI framework in run.py.

## TASK 11 — CREATE tests/unit/test_discovery_stage16.py
```python
"""Tests for S7.8 Stage 16 Discovery Orchestration."""
import pytest
from unittest.mock import MagicMock, patch, call
import json

import sys
sys.path.insert(0, 'C:/Fiverr/Fiverr')

RUN_ID = "discovery-20260608-120000-abc12345"


class TestSelectModes:
    def test_base_modes_always_included(self):
        from src.discovery.stage16 import _select_modes
        modes = _select_modes()
        for base in ['adjacent_keyword', 'gap_exploit', 'trend_chase']:
            assert base in modes
        print(f"PASS: base modes present: {modes}")

    def test_adjacent_niche_every_3rd_run(self):
        from src.discovery.stage16 import _select_modes
        assert 'adjacent_niche' in _select_modes(run_number=0)
        assert 'adjacent_niche' in _select_modes(run_number=3)
        assert 'adjacent_niche' in _select_modes(run_number=6)
        print("PASS: adjacent_niche on run 0, 3, 6")

    def test_adjacent_niche_not_on_non_3rd_run(self):
        from src.discovery.stage16 import _select_modes
        assert 'adjacent_niche' not in _select_modes(run_number=1)
        assert 'adjacent_niche' not in _select_modes(run_number=2)
        assert 'adjacent_niche' not in _select_modes(run_number=4)
        print("PASS: adjacent_niche absent on run 1, 2, 4")

    def test_no_run_number_returns_base_only(self):
        from src.discovery.stage16 import _select_modes
        modes = _select_modes(run_number=None)
        assert 'adjacent_niche' not in modes
        assert len(modes) == 3
        print(f"PASS: no run_number → 3 base modes: {modes}")

    def test_config_override_filters_modes(self):
        from src.discovery.stage16 import _select_modes
        config = {'discovery': {'enabled_modes': ['adjacent_keyword', 'gap_exploit']}}
        modes = _select_modes(config=config)
        assert 'trend_chase' not in modes
        assert 'adjacent_keyword' in modes
        print(f"PASS: config override filters: {modes}")

    def test_empty_config_returns_defaults(self):
        from src.discovery.stage16 import _select_modes
        modes = _select_modes(config={})
        assert len(modes) == 3
        print(f"PASS: empty config → defaults: {modes}")

    def test_returns_list_type(self):
        from src.discovery.stage16 import _select_modes
        result = _select_modes()
        assert isinstance(result, list)
        print("PASS: _select_modes returns list")


class TestRunDiscoveryCycle:
    def _make_db(self):
        db = MagicMock()
        # setup for get_pending_discovery_keywords
        db.query.return_value.filter.return_value.filter.return_value.filter.return_value.order_by.return_value.all.return_value = []
        db.query.return_value.all.return_value = []
        db.query.return_value.filter.return_value.all.return_value = []
        db.query.return_value.filter.return_value.filter.return_value.all.return_value = []
        db.query.return_value.limit.return_value.all.return_value = []
        db.query.return_value.filter.return_value.limit.return_value.all.return_value = []
        db.query.return_value.join.return_value.filter.return_value.limit.return_value.all.return_value = []
        return db

    def test_returns_discovery_cycle_log(self):
        from src.discovery.stage16 import run_discovery_cycle
        db = self._make_db()
        with patch('src.discovery.stage16.evaluate_discovery_results'), \
             patch('src.discovery.stage16.build_feedback_summary', return_value={'total_hypotheses': 0}), \
             patch('src.discovery.stage16.process_accepted_hypotheses', return_value={'inserted':0,'skipped':0,'run_id':RUN_ID,'keyword_ids':[]}), \
             patch('src.discovery.stage16._generate_all_hypotheses', return_value=([], 0)), \
             patch('src.discovery.stage16.DiscoveryCycleLog') as MockLog, \
             patch('src.discovery.stage16.NICHE_VALIDATION_CONFIG', {'python_automation': {}}):
            mock_log = MagicMock(); mock_log.run_id = RUN_ID
            MockLog.return_value = mock_log
            result = run_discovery_cycle(db, RUN_ID)
        db.add.assert_called()
        db.commit.assert_called_once()
        print("PASS: run_discovery_cycle returns DiscoveryCycleLog")

    def test_commit_called_once(self):
        from src.discovery.stage16 import run_discovery_cycle
        db = self._make_db()
        with patch('src.discovery.stage16.evaluate_discovery_results'), \
             patch('src.discovery.stage16.build_feedback_summary', return_value={}), \
             patch('src.discovery.stage16.process_accepted_hypotheses', return_value={'inserted':0,'skipped':0,'run_id':RUN_ID,'keyword_ids':[]}), \
             patch('src.discovery.stage16._generate_all_hypotheses', return_value=([], 0)), \
             patch('src.discovery.stage16.DiscoveryCycleLog', return_value=MagicMock()), \
             patch('src.discovery.stage16.NICHE_VALIDATION_CONFIG', {'python_automation': {}}):
            run_discovery_cycle(db, RUN_ID)
        db.commit.assert_called_once()
        print("PASS: commit called exactly once")

    def test_generates_run_id_if_not_provided(self):
        from src.discovery.stage16 import run_discovery_cycle
        db = self._make_db()
        log_kwargs = {}
        def capture_log(**kwargs): log_kwargs.update(kwargs); return MagicMock()
        with patch('src.discovery.stage16.evaluate_discovery_results'), \
             patch('src.discovery.stage16.build_feedback_summary', return_value={}), \
             patch('src.discovery.stage16.process_accepted_hypotheses', return_value={'inserted':0,'skipped':0,'run_id':'auto','keyword_ids':[]}), \
             patch('src.discovery.stage16._generate_all_hypotheses', return_value=([], 0)), \
             patch('src.discovery.stage16.DiscoveryCycleLog', side_effect=capture_log), \
             patch('src.discovery.stage16.NICHE_VALIDATION_CONFIG', {'python_automation': {}}):
            run_discovery_cycle(db, run_id=None)
        assert 'run_id' in log_kwargs
        assert log_kwargs['run_id'] is not None
        assert 'discovery-' in log_kwargs['run_id']
        print(f"PASS: auto-generated run_id: {log_kwargs['run_id']}")

    def test_cycle_log_contains_modes(self):
        from src.discovery.stage16 import run_discovery_cycle
        db = self._make_db()
        log_kwargs = {}
        def capture_log(**kwargs): log_kwargs.update(kwargs); return MagicMock()
        with patch('src.discovery.stage16.evaluate_discovery_results'), \
             patch('src.discovery.stage16.build_feedback_summary', return_value={}), \
             patch('src.discovery.stage16.process_accepted_hypotheses', return_value={'inserted':0,'skipped':0,'run_id':RUN_ID,'keyword_ids':[]}), \
             patch('src.discovery.stage16._generate_all_hypotheses', return_value=([], 0)), \
             patch('src.discovery.stage16.DiscoveryCycleLog', side_effect=capture_log), \
             patch('src.discovery.stage16.NICHE_VALIDATION_CONFIG', {'python_automation': {}}):
            run_discovery_cycle(db, RUN_ID)
        modes_json = log_kwargs.get('modes_run', '[]')
        modes = json.loads(modes_json)
        assert isinstance(modes, list) and len(modes) >= 3
        print(f"PASS: modes_run stored as JSON: {modes}")

    def test_cycle_log_hypotheses_accepted_matches_insert_result(self):
        from src.discovery.stage16 import run_discovery_cycle
        db = self._make_db()
        log_kwargs = {}
        def capture_log(**kwargs): log_kwargs.update(kwargs); return MagicMock()
        with patch('src.discovery.stage16.evaluate_discovery_results'), \
             patch('src.discovery.stage16.build_feedback_summary', return_value={}), \
             patch('src.discovery.stage16.process_accepted_hypotheses', return_value={'inserted':5,'skipped':2,'run_id':RUN_ID,'keyword_ids':[1,2,3,4,5]}), \
             patch('src.discovery.stage16._generate_all_hypotheses', return_value=([MagicMock(accepted=True, specificity_score=0.72)]*7, 0)), \
             patch('src.discovery.stage16.DiscoveryCycleLog', side_effect=capture_log), \
             patch('src.discovery.stage16.NICHE_VALIDATION_CONFIG', {'python_automation': {}}):
            run_discovery_cycle(db, RUN_ID)
        assert log_kwargs.get('hypotheses_accepted') == 5
        print(f"PASS: hypotheses_accepted={log_kwargs.get('hypotheses_accepted')} matches insert result")

    def test_evaluate_results_failure_is_non_fatal(self):
        from src.discovery.stage16 import run_discovery_cycle
        db = self._make_db()
        with patch('src.discovery.stage16.evaluate_discovery_results', side_effect=Exception("DB error")), \
             patch('src.discovery.stage16.build_feedback_summary', return_value={}), \
             patch('src.discovery.stage16.process_accepted_hypotheses', return_value={'inserted':0,'skipped':0,'run_id':RUN_ID,'keyword_ids':[]}), \
             patch('src.discovery.stage16._generate_all_hypotheses', return_value=([], 0)), \
             patch('src.discovery.stage16.DiscoveryCycleLog', return_value=MagicMock()), \
             patch('src.discovery.stage16.NICHE_VALIDATION_CONFIG', {'python_automation': {}}):
            result = run_discovery_cycle(db, RUN_ID)
        # Should not raise — evaluate failure is non-fatal
        print("PASS: evaluate_discovery_results failure is non-fatal")

    def test_feedback_summary_failure_uses_fallback(self):
        from src.discovery.stage16 import run_discovery_cycle
        db = self._make_db()
        log_kwargs = {}
        def capture_log(**kwargs): log_kwargs.update(kwargs); return MagicMock()
        with patch('src.discovery.stage16.evaluate_discovery_results'), \
             patch('src.discovery.stage16.build_feedback_summary', side_effect=Exception("fail")), \
             patch('src.discovery.stage16.process_accepted_hypotheses', return_value={'inserted':0,'skipped':0,'run_id':RUN_ID,'keyword_ids':[]}), \
             patch('src.discovery.stage16._generate_all_hypotheses', return_value=([], 0)), \
             patch('src.discovery.stage16.DiscoveryCycleLog', side_effect=capture_log), \
             patch('src.discovery.stage16.NICHE_VALIDATION_CONFIG', {'python_automation': {}}):
            run_discovery_cycle(db, RUN_ID)
        # fallback dict stored in feedback_summary
        fb = json.loads(log_kwargs.get('feedback_summary', '{}'))
        assert 'total_hypotheses' in fb or 'note' in fb
        print(f"PASS: feedback failure uses fallback dict: {fb}")

    def test_cost_usd_is_zero(self):
        from src.discovery.stage16 import run_discovery_cycle
        db = self._make_db()
        log_kwargs = {}
        def capture_log(**kwargs): log_kwargs.update(kwargs); return MagicMock()
        with patch('src.discovery.stage16.evaluate_discovery_results'), \
             patch('src.discovery.stage16.build_feedback_summary', return_value={}), \
             patch('src.discovery.stage16.process_accepted_hypotheses', return_value={'inserted':0,'skipped':0,'run_id':RUN_ID,'keyword_ids':[]}), \
             patch('src.discovery.stage16._generate_all_hypotheses', return_value=([], 0)), \
             patch('src.discovery.stage16.DiscoveryCycleLog', side_effect=capture_log), \
             patch('src.discovery.stage16.NICHE_VALIDATION_CONFIG', {'python_automation': {}}):
            run_discovery_cycle(db, RUN_ID)
        assert log_kwargs.get('total_cost_usd') == 0.0
        print("PASS: total_cost_usd=0.0 (no LLM calls)")


class TestGenerateAllHypotheses:
    def test_returns_tuple(self):
        from src.discovery.stage16 import _generate_all_hypotheses
        seed_data = {'seed_keywords':[], 'gap_signals':[], 'trend_signals':[], 'existing_kw_texts':[]}
        result = _generate_all_hypotheses('python_automation', ['adjacent_keyword'], seed_data, 0.50)
        assert isinstance(result, tuple) and len(result) == 2
        print(f"PASS: _generate_all_hypotheses returns (list, int)")

    def test_mode_failure_non_fatal(self):
        from src.discovery.stage16 import _generate_all_hypotheses
        seed_data = {'seed_keywords':[], 'gap_signals':[], 'trend_signals':[], 'existing_kw_texts':[]}
        with patch('src.discovery.stage16.generate_adjacent_keyword_hypotheses',
                   side_effect=Exception("mode error")):
            hypotheses, gated = _generate_all_hypotheses(
                'python_automation', ['adjacent_keyword'], seed_data, 0.50)
        assert isinstance(hypotheses, list)
        print(f"PASS: mode failure is non-fatal: {len(hypotheses)} hypotheses")

    def test_unknown_mode_skipped(self):
        from src.discovery.stage16 import _generate_all_hypotheses
        seed_data = {'seed_keywords':[], 'gap_signals':[], 'trend_signals':[], 'existing_kw_texts':[]}
        hypotheses, gated = _generate_all_hypotheses(
            'python_automation', ['nonexistent_mode'], seed_data, 0.50)
        assert hypotheses == []
        print("PASS: unknown mode skipped gracefully")


class TestBuildSeedData:
    def test_returns_required_keys(self):
        from src.discovery.stage16 import _build_seed_data
        db = MagicMock()
        db.query.return_value.filter.return_value.filter.return_value.limit.return_value.all.return_value = []
        db.query.return_value.join.return_value.filter.return_value.limit.return_value.all.return_value = []
        result = _build_seed_data('python_automation', db, ['adjacent_keyword', 'gap_exploit', 'trend_chase'])
        for key in ['seed_keywords', 'gap_signals', 'trend_signals', 'existing_kw_texts']:
            assert key in result
        print(f"PASS: _build_seed_data returns all required keys")

    def test_db_error_returns_empty_lists(self):
        from src.discovery.stage16 import _build_seed_data
        db = MagicMock()
        db.query.side_effect = Exception("DB error")
        result = _build_seed_data('python_automation', db, ['adjacent_keyword'])
        # Should return empty lists not raise
        assert result.get('seed_keywords', []) == []
        assert result.get('existing_kw_texts', []) == []
        print("PASS: DB error in _build_seed_data returns empty lists")
```

## TASK 12 — VERIFY integration.py UNCHANGED
```python
n = len(open('src/discovery/integration.py', encoding='utf-8').readlines())
assert 220 <= n <= 240, f"Unexpected: {n}"
print(f"PASS: integration.py unchanged: {n} lines")
```

## TASK 13 — VERIFY GOLDEN PARITY
```powershell
C:\Users\kevin\AppData\Local\Programs\Python\Python311\python.exe run.py score --golden `
    --config-override relevance.enable_stage_3_5=false `
    --config-override analysis.external_signals_enabled=false
```
kw=110 MUST be 62.7/1.0/CONDITIONAL_GO.

## TASK 14 — REGRESSION PACK RUN
```powershell
C:\Users\kevin\AppData\Local\Programs\Python\Python311\python.exe -m pytest -q tests/unit/ `
    -k "test_ghost_market_excluded_from_go_tag or test_null_means_include_backward_compat or test_golden_anchor_kw110_62_7 or test_discovery_core_loop_budget_gate or test_cli_config_check_passes or test_legacy_unscored_rows_are_ignored" `
    --no-header
```

## TASK 15 — FULL COVERAGE RUN
```powershell
C:\Users\kevin\AppData\Local\Programs\Python\Python311\python.exe -m pytest -q `
    --cov=src --cov-report=term-missing --cov-fail-under=90 --no-header tests/unit/ `
    | Select-Object -Last 5
```

## TASK 16 — S7.8 TESTS PASS
```powershell
C:\Users\kevin\AppData\Local\Programs\Python\Python311\python.exe -m pytest -q `
    tests/unit/test_discovery_stage16.py -v --no-header
```
All >= 30 tests must pass.

## TASK 17 — VERIFY stage16.py IMPORTABLE
```python
from src.discovery.stage16 import run_discovery_cycle, _select_modes
print("PASS: stage16.py importable")
```

## TASK 18 — VERIFY ORCHESTRATOR.PY UNCHANGED
```python
n = len(open('src/discovery/orchestrator.py', encoding='utf-8').readlines())
assert 295 <= n <= 305, f"orchestrator.py changed: {n}"
print(f"PASS: orchestrator.py unchanged: {n} lines")
```

## TASK 19 — VERIFY COMPLETE S7.2-S7.8 CHAIN IMPORTABLE
```python
from src.discovery.stage16 import run_discovery_cycle, _select_modes
from src.discovery.integration import process_accepted_hypotheses
from src.discovery.feedback import build_feedback_summary
from src.discovery.hypothesis import generate_gap_exploit_hypotheses
from src.models import DiscoveryCycleLog
print("PASS: complete S7.2-S7.8 chain importable on branch")
```

## TASK 20 — ZONE + COMMIT
```powershell
Invoke-Exe $git 'add src/discovery/stage16.py tests/unit/test_discovery_stage16.py docs/cycle_reports/CYCLE_072_AGENT_B.md'
Invoke-Exe $git 'diff --cached --name-only'
Invoke-Exe $git 'commit -m "feat(discovery): C072 Wave 10 S7.8 -- stage 16 orchestration, run_discovery_cycle, mode selection"'
Invoke-Exe $git 'push origin cycle/072/integration'
```

## B COMPLETE: 20 tasks. Floor 1200. Zone: src/+tests/+B.md.
END OF PROMPT

## B BLOCK 2

## TASK 21 -- SURVEY run.py CLI PATTERN
```python
content = open('run.py', encoding='utf-8').read()
has_click = '@click' in content or 'import click' in content
has_argparse = 'argparse' in content
print(f'CLI: click={has_click} argparse={has_argparse}')
entry = [l for l in content.splitlines() if 'main' in l.lower() or 'def run' in l.lower()][:5]
print(f'Entry points: {entry}')
```

## TASK 22 -- DRY_RUN_SENTINEL CHECK
```python
content = open('run.py', encoding='utf-8').read()
has_dry = 'DRY_RUN_SENTINEL' in content
print(f'DRY_RUN_SENTINEL in run.py: {has_dry}')
print('B adds sentinel check to discover command')
```

## TASK 23 -- HYPOTHESIS.PY UNCHANGED BEFORE B WORK
```python
n = len(open('src/discovery/hypothesis.py', encoding='utf-8').readlines())
assert 760 <= n <= 770; print(f'PASS: hypothesis.py: {n} lines')
```

## TASK 24 -- test_select_modes_deterministic
```python
def test_select_modes_deterministic():
    from src.discovery.stage16 import _select_modes
    assert _select_modes(run_number=1) == _select_modes(run_number=1)
    assert all(isinstance(m, str) for m in _select_modes())
    print(f'PASS: deterministic')
```

## TASK 25 -- test_cycle_calls_build_feedback_once
```python
def test_run_cycle_calls_feedback_once():
    from src.discovery.stage16 import run_discovery_cycle
    from unittest.mock import MagicMock, patch
    db = MagicMock()
    db.query.return_value.all.return_value = []
    db.query.return_value.filter.return_value.all.return_value = []
    db.query.return_value.filter.return_value.limit.return_value.all.return_value = []
    db.query.return_value.join.return_value.filter.return_value.limit.return_value.all.return_value = []
    db.query.return_value.filter.return_value.filter.return_value.filter.return_value.order_by.return_value.all.return_value = []
    called = []
    with patch('src.discovery.stage16.evaluate_discovery_results'), \
         patch('src.discovery.stage16.build_feedback_summary',
               side_effect=lambda d: called.append(True) or {}), \
         patch('src.discovery.stage16.process_accepted_hypotheses',
               return_value={'inserted':0,'skipped':0,'run_id':'r','keyword_ids':[]}), \
         patch('src.discovery.stage16._generate_all_hypotheses', return_value=([], 0)), \
         patch('src.discovery.stage16.DiscoveryCycleLog', return_value=MagicMock()), \
         patch('src.discovery.stage16.NICHE_VALIDATION_CONFIG', {'python_automation': {}}):
        run_discovery_cycle(db, 'r')
    assert len(called) == 1
    print('PASS: build_feedback_summary called once per cycle')
```

## TASK 26 -- test_hypotheses_generated_count
```python
def test_hypotheses_generated_count_correct():
    from src.discovery.stage16 import run_discovery_cycle
    from unittest.mock import MagicMock, patch
    db = MagicMock()
    db.query.return_value.all.return_value = []
    db.query.return_value.filter.return_value.all.return_value = []
    db.query.return_value.filter.return_value.limit.return_value.all.return_value = []
    db.query.return_value.join.return_value.filter.return_value.limit.return_value.all.return_value = []
    db.query.return_value.filter.return_value.filter.return_value.filter.return_value.order_by.return_value.all.return_value = []
    hypotheses = [MagicMock(accepted=True, specificity_score=0.72) for _ in range(8)]
    log_kwargs = {}
    def capture(**kwargs): log_kwargs.update(kwargs); return MagicMock()
    with patch('src.discovery.stage16.evaluate_discovery_results'), \
         patch('src.discovery.stage16.build_feedback_summary', return_value={}), \
         patch('src.discovery.stage16.process_accepted_hypotheses',
               return_value={'inserted':8,'skipped':0,'run_id':'c','keyword_ids':list(range(8))}), \
         patch('src.discovery.stage16._generate_all_hypotheses', return_value=(hypotheses, 0)), \
         patch('src.discovery.stage16.DiscoveryCycleLog', side_effect=capture), \
         patch('src.discovery.stage16.NICHE_VALIDATION_CONFIG', {'python_automation': {}}):
        run_discovery_cycle(db, 'c')
    assert log_kwargs.get('hypotheses_generated') == 8
    assert log_kwargs.get('hypotheses_accepted') == 8
    print(f'PASS: counts correct')
```

## TASK 27 -- test_build_seed_data_empty
```python
def test_build_seed_data_empty_db():
    from src.discovery.stage16 import _build_seed_data
    from unittest.mock import MagicMock
    db = MagicMock()
    db.query.return_value.filter.return_value.filter.return_value.limit.return_value.all.return_value = []
    db.query.return_value.join.return_value.filter.return_value.limit.return_value.all.return_value = []
    result = _build_seed_data('python_automation', db,
                              ['adjacent_keyword', 'gap_exploit', 'trend_chase'])
    for key in ['seed_keywords', 'gap_signals', 'trend_signals', 'existing_kw_texts']:
        assert result.get(key, None) is not None
    print(f'PASS: empty DB -> keys present: {list(result.keys())}')
```

## TASK 28 -- test_modes_never_empty
```python
def test_modes_never_empty():
    from src.discovery.stage16 import _select_modes
    for n in [None, 0, 1, 2, 3, 99]:
        assert len(_select_modes(run_number=n)) > 0
    print('PASS: _select_modes never returns empty list')
```

## TASK 29 -- test_cycle_with_custom_config
```python
def test_run_cycle_custom_config():
    from src.discovery.stage16 import run_discovery_cycle
    from unittest.mock import MagicMock, patch
    db = MagicMock()
    db.query.return_value.all.return_value = []
    db.query.return_value.filter.return_value.all.return_value = []
    db.query.return_value.filter.return_value.limit.return_value.all.return_value = []
    db.query.return_value.join.return_value.filter.return_value.limit.return_value.all.return_value = []
    db.query.return_value.filter.return_value.filter.return_value.filter.return_value.order_by.return_value.all.return_value = []
    config = {'discovery': {'min_hypothesis_confidence': 0.70, 'max_hypotheses_per_run': 5}}
    with patch('src.discovery.stage16.evaluate_discovery_results'), \
         patch('src.discovery.stage16.build_feedback_summary', return_value={}), \
         patch('src.discovery.stage16.process_accepted_hypotheses',
               return_value={'inserted':0,'skipped':0,'run_id':'c','keyword_ids':[]}), \
         patch('src.discovery.stage16._generate_all_hypotheses', return_value=([], 0)), \
         patch('src.discovery.stage16.DiscoveryCycleLog', return_value=MagicMock()), \
         patch('src.discovery.stage16.NICHE_VALIDATION_CONFIG', {'python_automation': {}}):
        run_discovery_cycle(db, 'c', config)
    print('PASS: run_discovery_cycle respects custom config')
```

## TASK 30 -- test_no_duplicate_modes
```python
def test_no_duplicate_modes():
    from src.discovery.stage16 import _select_modes
    for n in [0, 1, 2, 3]:
        modes = _select_modes(run_number=n)
        assert len(modes) == len(set(modes))
    print('PASS: no duplicate modes')
```

## TASK 31 -- test_generate_all_returns_tuple
```python
def test_generate_all_returns_list_int():
    from src.discovery.stage16 import _generate_all_hypotheses
    seed = {'seed_keywords':[],'gap_signals':[],'trend_signals':[],'existing_kw_texts':[]}
    h, g = _generate_all_hypotheses('python_automation', ['adjacent_keyword'], seed, 0.50)
    assert isinstance(h, list) and isinstance(g, int)
    print(f'PASS: ({len(h)}, {g})')
```

## TASK 32 -- test_generate_all_empty_modes
```python
def test_generate_all_empty_modes():
    from src.discovery.stage16 import _generate_all_hypotheses
    seed = {'seed_keywords':[],'gap_signals':[],'trend_signals':[],'existing_kw_texts':[]}
    h, g = _generate_all_hypotheses('python_automation', [], seed, 0.50)
    assert h == [] and g == 0
    print('PASS: empty modes -> empty hypotheses')
```

## TASK 33 -- B ZONE CONSTRAINT
```python
print('B zone: stage16.py + test_discovery_stage16.py + B.md + run.py (optional)')
print('NOT: orchestrator.py, hypothesis.py, integration.py, feedback.py')
```

## TASK 34 -- test_no_circular_imports
```python
def test_stage16_no_circular():
    import sys
    for k in list(sys.modules.keys()):
        if 'stage16' in k: del sys.modules[k]
    import src.discovery.stage16
    print('PASS: no circular imports')
```

## B COMPLETE: 34 tasks. Floor 1200. Zone: src/+tests/+B.md+run.py.
END OF PROMPT

## B BLOCK 3 -- ADDITIONAL TESTS

## TASK 35 -- test_run_discovery_returns_object
```python
def test_run_discovery_cycle_returns_object():
    from src.discovery.stage16 import run_discovery_cycle
    from unittest.mock import MagicMock, patch
    db = MagicMock()
    db.query.return_value.all.return_value = []
    db.query.return_value.filter.return_value.all.return_value = []
    db.query.return_value.filter.return_value.limit.return_value.all.return_value = []
    db.query.return_value.join.return_value.filter.return_value.limit.return_value.all.return_value = []
    db.query.return_value.filter.return_value.filter.return_value.filter.return_value.order_by.return_value.all.return_value = []
    mock_log = MagicMock()
    with patch('src.discovery.stage16.evaluate_discovery_results'), \
         patch('src.discovery.stage16.build_feedback_summary', return_value={}), \
         patch('src.discovery.stage16.process_accepted_hypotheses',
               return_value={'inserted':0,'skipped':0,'run_id':'r','keyword_ids':[]}), \
         patch('src.discovery.stage16._generate_all_hypotheses', return_value=([], 0)), \
         patch('src.discovery.stage16.DiscoveryCycleLog', return_value=mock_log), \
         patch('src.discovery.stage16.NICHE_VALIDATION_CONFIG', {'python_automation': {}}):
        result = run_discovery_cycle(db, 'r')
    assert result is mock_log
    print('PASS: run_discovery_cycle returns DiscoveryCycleLog object')
```

## TASK 36 -- test_process_called_with_accepted_only
```python
def test_process_called_with_accepted_only():
    from src.discovery.stage16 import run_discovery_cycle
    from unittest.mock import MagicMock, patch
    db = MagicMock()
    db.query.return_value.all.return_value = []
    db.query.return_value.filter.return_value.all.return_value = []
    db.query.return_value.filter.return_value.limit.return_value.all.return_value = []
    db.query.return_value.join.return_value.filter.return_value.limit.return_value.all.return_value = []
    db.query.return_value.filter.return_value.filter.return_value.filter.return_value.order_by.return_value.all.return_value = []
    # Mix of accepted and rejected hypotheses
    accepted = [MagicMock(accepted=True, specificity_score=0.72) for _ in range(3)]
    rejected = [MagicMock(accepted=False, specificity_score=0.30) for _ in range(5)]
    all_h = accepted + rejected
    process_args = []
    def mock_process(hyp, run_id, db, **kwargs):
        process_args.extend(hyp)
        return {'inserted': len(hyp), 'skipped': 0, 'run_id': run_id, 'keyword_ids': list(range(len(hyp)))}
    with patch('src.discovery.stage16.evaluate_discovery_results'), \
         patch('src.discovery.stage16.build_feedback_summary', return_value={}), \
         patch('src.discovery.stage16.process_accepted_hypotheses', side_effect=mock_process), \
         patch('src.discovery.stage16._generate_all_hypotheses', return_value=(all_h, 0)), \
         patch('src.discovery.stage16.DiscoveryCycleLog', return_value=MagicMock()), \
         patch('src.discovery.stage16.NICHE_VALIDATION_CONFIG', {'python_automation': {}}):
        run_discovery_cycle(db, 'filter-test')
    # Only accepted=True AND specificity_score >= 0.50 passed to process
    assert all(getattr(h, 'accepted', False) for h in process_args)
    print(f'PASS: only accepted hypotheses passed to process: {len(process_args)}')
```

## TASK 37 -- test_adjacent_niche_run_0
```python
def test_adjacent_niche_included_on_run_0():
    from src.discovery.stage16 import _select_modes
    modes = _select_modes(run_number=0)
    assert 'adjacent_niche' in modes
    assert len(modes) == 4
    print(f'PASS: run_number=0 has adjacent_niche: {modes}')
```

## TASK 38 -- test_adjacent_niche_run_6
```python
def test_adjacent_niche_included_on_run_6():
    from src.discovery.stage16 import _select_modes
    modes = _select_modes(run_number=6)
    assert 'adjacent_niche' in modes
    print(f'PASS: run_number=6 has adjacent_niche: {modes}')
```

## TASK 39 -- test_feedback_summary_in_log
```python
def test_feedback_summary_stored_in_log():
    from src.discovery.stage16 import run_discovery_cycle
    from unittest.mock import MagicMock, patch
    import json
    db = MagicMock()
    db.query.return_value.all.return_value = []
    db.query.return_value.filter.return_value.all.return_value = []
    db.query.return_value.filter.return_value.limit.return_value.all.return_value = []
    db.query.return_value.join.return_value.filter.return_value.limit.return_value.all.return_value = []
    db.query.return_value.filter.return_value.filter.return_value.filter.return_value.order_by.return_value.all.return_value = []
    feedback = {'total_hypotheses': 5, 'hits': 3, 'hit_rate_pct': 60.0}
    kw = {}
    def capture(**kwargs): kw.update(kwargs); return MagicMock()
    with patch('src.discovery.stage16.evaluate_discovery_results'), \
         patch('src.discovery.stage16.build_feedback_summary', return_value=feedback), \
         patch('src.discovery.stage16.process_accepted_hypotheses',
               return_value={'inserted':0,'skipped':0,'run_id':'fb','keyword_ids':[]}), \
         patch('src.discovery.stage16._generate_all_hypotheses', return_value=([], 0)), \
         patch('src.discovery.stage16.DiscoveryCycleLog', side_effect=capture), \
         patch('src.discovery.stage16.NICHE_VALIDATION_CONFIG', {'python_automation': {}}):
        run_discovery_cycle(db, 'fb')
    stored = json.loads(kw.get('feedback_summary', '{}'))
    assert stored.get('total_hypotheses') == 5
    print(f'PASS: feedback_summary stored correctly: {stored}')
```

## TASK 40 -- test_gated_count_correct
```python
def test_gated_count_reflects_low_confidence():
    from src.discovery.stage16 import run_discovery_cycle
    from unittest.mock import MagicMock, patch
    db = MagicMock()
    db.query.return_value.all.return_value = []
    db.query.return_value.filter.return_value.all.return_value = []
    db.query.return_value.filter.return_value.limit.return_value.all.return_value = []
    db.query.return_value.join.return_value.filter.return_value.limit.return_value.all.return_value = []
    db.query.return_value.filter.return_value.filter.return_value.filter.return_value.order_by.return_value.all.return_value = []
    # 3 accepted, 5 rejected hypotheses
    high = [MagicMock(accepted=True, specificity_score=0.80) for _ in range(3)]
    low = [MagicMock(accepted=True, specificity_score=0.20) for _ in range(5)]
    kw = {}
    def capture(**kwargs): kw.update(kwargs); return MagicMock()
    with patch('src.discovery.stage16.evaluate_discovery_results'), \
         patch('src.discovery.stage16.build_feedback_summary', return_value={}), \
         patch('src.discovery.stage16.process_accepted_hypotheses',
               side_effect=lambda h, r, d, **kw: {'inserted':len(h),'skipped':0,'run_id':r,'keyword_ids':list(range(len(h)))}), \
         patch('src.discovery.stage16._generate_all_hypotheses', return_value=(high+low, 0)), \
         patch('src.discovery.stage16.DiscoveryCycleLog', side_effect=capture), \
         patch('src.discovery.stage16.NICHE_VALIDATION_CONFIG', {'python_automation': {}}):
        run_discovery_cycle(db, 'gated')
    print(f'PASS: gated count: {kw.get("hypotheses_gated")}')
```

## TASK 41 -- test_s78_coexists_with_wave9
```python
def test_s78_coexists_with_wave9():
    from src.pricing import analyze_price_distribution, calculate_new_seller_pricing
    from src.discovery.stage16 import run_discovery_cycle
    print('PASS: S7.8 + Wave 9 coexist')
```

## TASK 42 -- test_integration_chain
```python
def test_complete_s78_integration_chain():
    from src.discovery.stage16 import run_discovery_cycle, _select_modes, DEFAULT_MIN_CONFIDENCE
    from src.discovery.integration import process_accepted_hypotheses
    from src.discovery.feedback import build_feedback_summary
    from src.models import DiscoveryCycleLog
    modes = _select_modes()
    assert len(modes) >= 3
    assert DEFAULT_MIN_CONFIDENCE == 0.50
    print(f'PASS: S7.2-S7.8 chain: modes={modes}')
```

## B COMPLETE: 42 tasks. Floor 1200. Zone: src/+tests/+B.md+run.py.

## TASK 43 -- VERIFY DRY_RUN_SENTINEL IN DISCOVER COMMAND
```python
content = open("run.py", encoding="utf-8").read()
if "DRY_RUN_SENTINEL" in content:
    print("PASS: run.py has DRY_RUN_SENTINEL check")
else:
    print("INFO: B adds DRY_RUN_SENTINEL to discover command")
    print("  Pattern: if os.getenv(DRY_RUN_SENTINEL): print(skip); return")
```

## TASK 44 -- VERIFY COMPLETE S7.2-S7.8 IMPORT CHAIN ON BRANCH
```python
import sys; sys.path.insert(0, "C:/Fiverr/Fiverr")
from src.discovery.stage16 import run_discovery_cycle, _select_modes
from src.discovery.stage16 import DEFAULT_MIN_CONFIDENCE, DEFAULT_MAX_HYPOTHESES, _BASE_MODES
from src.discovery.integration import (process_accepted_hypotheses, insert_discovery_keyword,
    get_pending_discovery_keywords)
from src.discovery.feedback import build_feedback_summary, evaluate_discovery_results
from src.discovery.feedback import GOLD_THRESHOLD, HIT_THRESHOLD, MISS_THRESHOLD
from src.discovery.hypothesis import (generate_adjacent_keyword_hypotheses,
    generate_adjacent_niche_hypotheses, generate_gap_exploit_hypotheses,
    generate_trend_chase_hypotheses)
from src.models import DiscoveryCycleLog, DiscoveryOutcome, Keyword
from src.discovery.contracts import HypothesisMode
modes = sorted([e.value for e in HypothesisMode])
print(f"PASS: S7.2-S7.8 complete import: {modes}")
print(f"  gold={GOLD_THRESHOLD} hit={HIT_THRESHOLD} min_conf={DEFAULT_MIN_CONFIDENCE} max={DEFAULT_MAX_HYPOTHESES}")
print(f"  base_modes={_BASE_MODES}")
```

## TASK 45 -- VERIFY NO NEW MIGRATION FILES
```python
import os, time
migration_dir = "src/database/migrations/"
if os.path.exists(migration_dir):
    new_files = [f for f in os.listdir(migration_dir)
                 if os.path.getmtime(migration_dir+f) > time.time() - 7200]
    assert new_files == [], f"New migration created: {new_files}"
    print(f"PASS: no new migrations (B scope: stage16.py + tests only)")
else:
    print("INFO: migrations dir not found -- check alembic structure")
```

## TASK 46 -- VERIFY test_discovery_stage16.py COVERS SELECT_MODES EDGE CASES
```python
import ast
f = "tests/unit/test_discovery_stage16.py"
tree = ast.parse(open(f, encoding="utf-8").read())
test_names = [n.name for n in ast.walk(tree)
              if isinstance(n, ast.FunctionDef) and n.name.startswith("test_")]
select_modes_tests = [t for t in test_names if "select_modes" in t or "modes" in t.lower()]
print(f"PASS: select_modes edge case tests: {select_modes_tests}")
assert len(select_modes_tests) >= 4, f"Need >= 4 mode tests, got {len(select_modes_tests)}"
```

## TASK 47 -- VERIFY stage16.py SIZE IS REASONABLE
```python
n = len(open("src/discovery/stage16.py", encoding="utf-8").readlines())
assert 100 <= n <= 600, f"stage16.py has {n} lines (expected 100-600)"
import ast
tree = ast.parse(open("src/discovery/stage16.py", encoding="utf-8").read())
pub_fns = [nd.name for nd in ast.walk(tree)
           if isinstance(nd, ast.FunctionDef) and not nd.name.startswith("__")]
print(f"PASS: stage16.py {n} lines, functions: {pub_fns}")
```

## TASK 48 -- FULL SUITE BEFORE COMMIT
```powershell
python.exe -m pytest -q --cov=src --cov-fail-under=90 --no-header tests/unit/
    | Select-Object -Last 5
# Must show: N passed, 94%+
```

## TASK 49 -- VERIFY WAVE 9 PRICING INTACT
```python
from src.pricing import (analyze_price_distribution, calculate_new_seller_pricing,
    build_pricing_export_payload, export_all_pricing)
from src.discovery.stage16 import run_discovery_cycle
print("PASS: Wave 9 pricing and S7.8 stage16 coexist on branch")
```

## TASK 50 -- VERIFY HYPOTHESIS.PY UNCHANGED
```python
import ast
n = len(open("src/discovery/hypothesis.py", encoding="utf-8").readlines())
assert 760 <= n <= 770, f"hypothesis.py changed: {n} lines"
tree = ast.parse(open("src/discovery/hypothesis.py", encoding="utf-8").read())
fns = [f.name for f in ast.walk(tree) if isinstance(f, ast.FunctionDef)]
assert "generate_adjacent_keyword_hypotheses" in fns
assert "generate_gap_exploit_hypotheses" in fns
assert "generate_trend_chase_hypotheses" in fns
print(f"PASS: hypothesis.py unchanged: {n} lines, key fns present")
```

## TASK 51 -- VERIFY INTEGRATION.PY UNCHANGED
```python
n = len(open("src/discovery/integration.py", encoding="utf-8").readlines())
assert 220 <= n <= 240, f"integration.py changed: {n} lines"
print(f"PASS: integration.py unchanged: {n} lines")
```

## TASK 52 -- VERIFY BASELINE DB UNTOUCHED
```python
import os
mtime = os.path.getmtime("data/cycle037_live.db")
assert abs(mtime - 1780553758) < 10, f"Baseline modified: mtime={mtime}"
print(f"PASS: baseline UNTOUCHED mtime={mtime:.0f}")
```

## B COMPLETE: 52 tasks. Floor 1200. Zone: src/+tests/+B.md+run.py.
END OF PROMPT
