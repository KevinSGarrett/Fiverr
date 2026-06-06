# CYCLE 068 — AGENT B PROMPT
# Wave 10 S7.4 Gap Opportunity Hypothesis Mode
# Role: SOLE src/ author.
# B+E PARALLEL NOTICE: B and E execute in parallel after A.
# §12.1 PARALLEL: B and E run IN PARALLEL after A. Do NOT wait for E.
# POLICY v4.3: 55 LARGE-XXLARGE tasks | Floor: 1,200 lines

## PROJECT CONTEXT
- Branch: cycle/068/integration | Base SHA: 19e4ca2
- Python: C:\Users\kevin\AppData\Local\Programs\Python\Python311\python.exe
- Suite at start: 4675 passed | 94.34% | Floor: 90%
- C068 story: SCRUM-199 | Parent: SCRUM-22

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
- CONFIG GATE: scrapfly.enabled must remain false

## REGRESSION PACK v2.5 (45 — all must pass)
REG-01: test_ghost_market_excluded_from_go_tag
REG-02: test_conditional_go_threshold_boundary
REG-03: test_no_go_below_caution_threshold
REG-04: test_demand_score_keyword_only_depth
REG-05: test_competition_score_uses_search_result_count
REG-06: test_feasibility_score_zero_review_seller_eligible
REG-07: test_profitability_score_package_data_required
REG-08: test_confidence_score_freshness_decay
REG-09: test_trc_reliability_single_multiplier_no_stack
REG-10: test_null_means_include_backward_compat
REG-11: test_ghost_market_hard_block_only
REG-12: test_trends_qualifier_threshold_0_65
REG-13: test_rsv_live_band_threshold
REG-14: test_rsv_seed_fallback_behavior
REG-15: test_result_set_validator_min_gigs
REG-16: test_sponsored_filter_removes_promoted
REG-17: test_zombie_filter_removes_stale
REG-18: test_llm_relevance_disabled_passes_all
REG-19: test_llm_relevance_flags_below_threshold
REG-20: test_external_signal_integrity_check
REG-21: test_scoring_profile_weights_sum_to_one
REG-22: test_final_score_bounded_0_100
REG-23: test_golden_anchor_kw110_62_7
REG-24: test_golden_anchor_kw96_35_8
REG-25: test_golden_anchor_kw3_56_66
REG-26: test_discovery_core_loop_budget_gate
REG-27: test_discovery_hypothesis_confidence_threshold
REG-28: test_alert_new_strong_go_triggered
REG-29: test_alert_stale_data_warning
REG-30: test_export_csv_includes_score_components
REG-31: test_export_excel_valid_workbook
REG-32: test_cli_config_check_passes
REG-33: test_cli_seed_niches_idempotent
REG-34: test_dry_run_sentinel_prevents_live_writes
REG-35: test_negation_exclusion_removes_off_topic
REG-36: test_emerging_bonus_applied_correctly
REG-37: test_ghost_filter_handles_null_ghost_market_score
REG-38: test_llm_alert_counts_actual_llm_calls
REG-39: test_monitors_health_check_returns_status
REG-40: test_quality_gate_blocks_low_coverage
REG-41: test_external_signal_raw_value_stored_and_retrieved
REG-42: test_collection_url_encodes_spaces_correctly
REG-43: test_collection_url_never_bare_path
REG-44: test_dashboard_opportunities_renders_empty_db_gracefully

## S7.4 SCOPE
Modify: src/discovery/hypothesis.py (add gap exploit functions + constants)
Modify: src/discovery/contracts.py (add GAP_EXPLOIT to HypothesisMode if missing)
Create: tests/unit/test_gap_exploit_hypotheses.py (>=30 tests)
No new DB tables. No new migrations. No persistence.

## PREFLIGHT
```powershell
Invoke-Exe $git 'pull origin cycle/068/integration'
Invoke-Exe $git 'log --oneline -5'
Invoke-Exe $git 'branch --show-current'  # cycle/068/integration
C:\Users\kevin\AppData\Local\Programs\Python\Python311\python.exe run.py config-check
```

## TASK 1 — READ EXISTING hypothesis.py (S7.2+S7.3 pattern to follow)
```python
import ast
tree = ast.parse(open('src/discovery/hypothesis.py').read())
fns = [n.name for n in ast.walk(tree) if isinstance(n, ast.FunctionDef)]
constants = [n.targets[0].id for n in ast.walk(tree) if isinstance(n, ast.Assign)
    and hasattr(n.targets[0], 'id')]
print(f"Functions: {fns}")
print(f"Constants: {constants}")
print(f"Lines: {len(open('src/discovery/hypothesis.py').readlines())}")
```

## TASK 2 — VERIFY HypothesisMode GAP_EXPLOIT STATUS
```python
from src.discovery.contracts import HypothesisMode
modes = {e.name: e.value for e in HypothesisMode}
print(f"Modes: {modes}")
need_gap_exploit = 'GAP_EXPLOIT' not in modes
print(f"Need to add GAP_EXPLOIT: {need_gap_exploit}")
```

## TASK 3 — ADD GAP_EXPLOIT TO HypothesisMode (if missing)
If GAP_EXPLOIT absent from enum, add to src/discovery/contracts.py:
```python
class HypothesisMode(str, Enum):
    ADJACENT_KEYWORD = "adjacent_keyword"    # S7.2 done C066
    ADJACENT_NICHE = "adjacent_niche"        # S7.3 done C067
    GAP_EXPLOIT = "gap_exploit"              # S7.4 this cycle
    TREND_CHASE = "trend_chase"              # S7.5 future
```
Verify: `HypothesisMode.GAP_EXPLOIT.value == 'gap_exploit'`

## TASK 4 — ADD GAP THRESHOLD CONSTANTS
```python
# Add to src/discovery/hypothesis.py after existing constants

# S7.4: Gap Opportunity threshold constants
GAP_DEMAND_THRESHOLD: float = 0.60      # keyword demand must be >= this
GAP_COMPETITION_THRESHOLD: float = 0.40  # keyword competition must be <= this
GAP_DEMAND_WEIGHT: float = 0.60          # weight for demand in confidence
GAP_OPPORTUNITY_WEIGHT: float = 0.40     # weight for opportunity in confidence
```

## TASK 5 — IMPLEMENT _identify_gap_keywords
```python
def _identify_gap_keywords(
    keyword_scores: list[dict],
    *,
    demand_threshold: float = GAP_DEMAND_THRESHOLD,
    competition_threshold: float = GAP_COMPETITION_THRESHOLD,
) -> list[dict]:
    """Filter keyword_scores to only those representing market gaps.

    A gap keyword has:
    - demand_score >= demand_threshold (high demand exists)
    - competition_score <= competition_threshold (low competition = gap)

    Args:
        keyword_scores: List of dicts with keys keyword, demand_score,
            competition_score, opportunity_score. Missing keys default to 0.0.
        demand_threshold: Minimum demand for a gap keyword.
        competition_threshold: Maximum competition for a gap keyword.

    Returns:
        Subset of keyword_scores meeting gap criteria. Empty list if none qualify.
    """
    gaps = []
    for kw_data in keyword_scores:
        demand = float(kw_data.get('demand_score', 0.0))
        competition = float(kw_data.get('competition_score', 0.0))
        if demand >= demand_threshold and competition <= competition_threshold:
            gaps.append(kw_data)
    return gaps
```

## TASK 6 — IMPLEMENT _score_gap_hypothesis_confidence
```python
def _score_gap_hypothesis_confidence(
    kw_data: dict,
    *,
    demand_weight: float = GAP_DEMAND_WEIGHT,
    opportunity_weight: float = GAP_OPPORTUNITY_WEIGHT,
) -> float:
    """Score confidence for a gap opportunity hypothesis.

    Confidence = demand_weight × demand_score + opportunity_weight × opportunity_score.
    No base adjacency bonus (unlike S7.3) — confidence is purely data-driven.

    Args:
        kw_data: Dict with demand_score and opportunity_score (defaults to 0.0 if missing).
        demand_weight: Weight for demand score in confidence (default 0.60).
        opportunity_weight: Weight for opportunity score in confidence (default 0.40).

    Returns:
        Float in [0.0, 1.0].
    """
    demand = float(kw_data.get('demand_score', 0.0))
    opportunity = float(kw_data.get('opportunity_score', 0.0))
    raw = demand_weight * demand + opportunity_weight * opportunity
    return min(1.0, max(0.0, raw))
```

## TASK 7 — IMPLEMENT generate_gap_exploit_hypotheses (CORE S7.4)
```python
def generate_gap_exploit_hypotheses(
    source_niche_id: str,
    keyword_scores: list[dict],
    existing_hypotheses: list[str],
    *,
    max_hypotheses: int = 10,
    min_confidence: float = 0.50,
    demand_threshold: float = GAP_DEMAND_THRESHOLD,
    competition_threshold: float = GAP_COMPETITION_THRESHOLD,
) -> list[HypothesisContract]:
    """Generate gap opportunity hypotheses from keyword scoring data.

    S7.4 implementation: data-driven (unlike S7.2/S7.3 which use static maps).
    Identifies keywords with high demand (>= demand_threshold) and low competition
    (<= competition_threshold), then ranks by confidence score.

    Args:
        source_niche_id: The niche being researched.
        keyword_scores: Scored keyword data from the scoring pipeline.
        existing_hypotheses: Hypothesis texts to skip (deduplication).
        max_hypotheses: Max number of accepted hypotheses.
        min_confidence: Budget gate — only accept if confidence >= this.
        demand_threshold: Minimum demand score for gap detection.
        competition_threshold: Maximum competition score for gap detection.

    Returns:
        List of HypothesisContract (accepted AND rejected — audit trail).
        hypothesis_text = the gap keyword string.
        niche_id = source_niche_id.
    """
    if not source_niche_id or not keyword_scores:
        return []
    existing_lower = {h.lower() for h in existing_hypotheses}
    gap_keywords = _identify_gap_keywords(keyword_scores,
        demand_threshold=demand_threshold,
        competition_threshold=competition_threshold)
    # Sort by opportunity score descending (best gaps first)
    gap_keywords = sorted(gap_keywords,
        key=lambda kw: float(kw.get('opportunity_score', 0.0)), reverse=True)
    results: list[HypothesisContract] = []
    accepted_count = 0
    for kw_data in gap_keywords:
        keyword = str(kw_data.get('keyword', '')).strip()
        if not keyword or keyword.lower() in existing_lower:
            continue
        confidence = _score_gap_hypothesis_confidence(kw_data)
        accepted = confidence >= min_confidence and accepted_count < max_hypotheses
        if accepted:
            accepted_count += 1
        reason = (
            f"gap confidence {confidence:.2f} >= {min_confidence} "
            f"(demand={kw_data.get('demand_score', 0.0):.2f}, "
            f"competition={kw_data.get('competition_score', 0.0):.2f}) "
            f"({'ACCEPTED' if accepted else 'REJECTED'})"
        )
        results.append(HypothesisContract(
            hypothesis_text=keyword,
            niche_id=source_niche_id,
            buyer=None,
            deliverable=keyword,
            specificity_score=confidence,
            accepted=accepted,
            reason=reason,
        ))
    return results
```

## TASK 8 — CREATE tests/unit/test_gap_exploit_hypotheses.py (>=30 tests)
```python
"""Tests for S7.4 Gap Opportunity Hypothesis Mode."""
import pytest
from src.discovery.hypothesis import (
    generate_gap_exploit_hypotheses,
    _identify_gap_keywords,
    _score_gap_hypothesis_confidence,
    GAP_DEMAND_THRESHOLD, GAP_COMPETITION_THRESHOLD,
    GAP_DEMAND_WEIGHT, GAP_OPPORTUNITY_WEIGHT,
    HypothesisContract,
)

SAMPLE_SCORES = [
    {'keyword': 'python automation scripts', 'demand_score': 0.75, 'competition_score': 0.25, 'opportunity_score': 0.80},
    {'keyword': 'ai workflow builder', 'demand_score': 0.80, 'competition_score': 0.30, 'opportunity_score': 0.85},
    {'keyword': 'data pipeline automation', 'demand_score': 0.50, 'competition_score': 0.70, 'opportunity_score': 0.40},
    {'keyword': 'custom python script', 'demand_score': 0.90, 'competition_score': 0.80, 'opportunity_score': 0.30},
]

GAP_SCORES = [s for s in SAMPLE_SCORES
    if s['demand_score'] >= GAP_DEMAND_THRESHOLD and s['competition_score'] <= GAP_COMPETITION_THRESHOLD]

class TestIdentifyGapKeywords:
    def test_returns_list(self):
        result = _identify_gap_keywords(SAMPLE_SCORES)
        assert isinstance(result, list)

    def test_high_demand_low_competition_included(self):
        result = _identify_gap_keywords(SAMPLE_SCORES)
        keywords = [r['keyword'] for r in result]
        assert 'python automation scripts' in keywords
        assert 'ai workflow builder' in keywords

    def test_high_competition_excluded(self):
        result = _identify_gap_keywords(SAMPLE_SCORES)
        keywords = [r['keyword'] for r in result]
        assert 'custom python script' not in keywords  # competition 0.80 > threshold

    def test_low_demand_excluded(self):
        result = _identify_gap_keywords(SAMPLE_SCORES)
        keywords = [r['keyword'] for r in result]
        assert 'data pipeline automation' not in keywords  # demand 0.50 < threshold

    def test_empty_input_returns_empty(self):
        assert _identify_gap_keywords([]) == []

    def test_demand_threshold_boundary(self):
        edge = [{'keyword': 'test', 'demand_score': GAP_DEMAND_THRESHOLD,
                 'competition_score': GAP_COMPETITION_THRESHOLD - 0.01, 'opportunity_score': 0.5}]
        result = _identify_gap_keywords(edge)
        assert len(result) == 1

    def test_competition_threshold_boundary(self):
        edge = [{'keyword': 'test', 'demand_score': GAP_DEMAND_THRESHOLD + 0.01,
                 'competition_score': GAP_COMPETITION_THRESHOLD, 'opportunity_score': 0.5}]
        result = _identify_gap_keywords(edge)
        assert len(result) == 1

    def test_missing_keys_default_to_zero(self):
        sparse = [{'keyword': 'test_keyword'}]  # no scores
        result = _identify_gap_keywords(sparse)
        assert len(result) == 0  # demand 0.0 < threshold


class TestScoreGapHypothesisConfidence:
    def test_returns_float(self):
        result = _score_gap_hypothesis_confidence(SAMPLE_SCORES[0])
        assert isinstance(result, float)

    def test_bounded_0_to_1(self):
        for kw_data in SAMPLE_SCORES:
            score = _score_gap_hypothesis_confidence(kw_data)
            assert 0.0 <= score <= 1.0

    def test_empty_kw_data_returns_zero(self):
        assert _score_gap_hypothesis_confidence({}) == 0.0

    def test_demand_weight_applied(self):
        kw = {'demand_score': 1.0, 'opportunity_score': 0.0}
        score = _score_gap_hypothesis_confidence(kw)
        assert abs(score - GAP_DEMAND_WEIGHT) < 0.001

    def test_opportunity_weight_applied(self):
        kw = {'demand_score': 0.0, 'opportunity_score': 1.0}
        score = _score_gap_hypothesis_confidence(kw)
        assert abs(score - GAP_OPPORTUNITY_WEIGHT) < 0.001

    def test_weights_sum_to_1(self):
        assert abs(GAP_DEMAND_WEIGHT + GAP_OPPORTUNITY_WEIGHT - 1.0) < 0.001


class TestGenerateGapExploitHypotheses:
    def test_returns_list(self):
        result = generate_gap_exploit_hypotheses('python_automation', SAMPLE_SCORES, [])
        assert isinstance(result, list)

    def test_empty_source_returns_empty(self):
        assert generate_gap_exploit_hypotheses('', SAMPLE_SCORES, []) == []

    def test_empty_keyword_scores_returns_empty(self):
        assert generate_gap_exploit_hypotheses('python_automation', [], []) == []

    def test_budget_gate_at_high_threshold(self):
        results = generate_gap_exploit_hypotheses('python_automation', SAMPLE_SCORES, [], min_confidence=0.99)
        assert all(not r.accepted for r in results)

    def test_budget_gate_at_zero_threshold(self):
        results = generate_gap_exploit_hypotheses('python_automation', SAMPLE_SCORES, [], min_confidence=0.0)
        accepted = [r for r in results if r.accepted]
        assert len(accepted) >= len(GAP_SCORES)

    def test_deduplication_against_existing(self):
        existing = ['python automation scripts']
        results = generate_gap_exploit_hypotheses('python_automation', SAMPLE_SCORES, existing)
        texts = [r.hypothesis_text for r in results]
        assert 'python automation scripts' not in texts

    def test_niche_id_preserved(self):
        results = generate_gap_exploit_hypotheses('python_automation', SAMPLE_SCORES, [])
        for r in results: assert r.niche_id == 'python_automation'

    def test_hypothesis_text_is_keyword(self):
        results = generate_gap_exploit_hypotheses('python_automation', SAMPLE_SCORES, [])
        known_keywords = [s['keyword'] for s in SAMPLE_SCORES]
        for r in results:
            assert r.hypothesis_text in known_keywords

    def test_reason_string_populated(self):
        results = generate_gap_exploit_hypotheses('python_automation', SAMPLE_SCORES, [])
        for r in results: assert r.reason and len(r.reason) > 10

    def test_max_hypotheses_respected(self):
        results = generate_gap_exploit_hypotheses(
            'python_automation', SAMPLE_SCORES * 20, [], max_hypotheses=2, min_confidence=0.0)
        accepted = [r for r in results if r.accepted]
        assert len(accepted) <= 2

    def test_accepted_score_matches_threshold(self):
        results = generate_gap_exploit_hypotheses('python_automation', SAMPLE_SCORES, [], min_confidence=0.50)
        for r in results:
            if r.accepted: assert r.specificity_score >= 0.50

    def test_sorted_by_opportunity_score_desc(self):
        results = generate_gap_exploit_hypotheses(
            'python_automation', SAMPLE_SCORES, [], min_confidence=0.0)
        accepted = [r for r in results if r.accepted]
        scores = [r.specificity_score for r in accepted]
        assert scores == sorted(scores, reverse=True) or len(scores) <= 1

    def test_default_min_confidence_is_0_50(self):
        import inspect
        sig = inspect.signature(generate_gap_exploit_hypotheses)
        assert sig.parameters['min_confidence'].default == 0.50

    def test_default_demand_threshold(self):
        import inspect
        sig = inspect.signature(generate_gap_exploit_hypotheses)
        assert sig.parameters['demand_threshold'].default == GAP_DEMAND_THRESHOLD
```

## TASK 9 — VERIFY GAP_EXPLOIT IMPORTABLE
```python
from src.discovery.hypothesis import (
    generate_gap_exploit_hypotheses, _identify_gap_keywords,
    _score_gap_hypothesis_confidence,
    GAP_DEMAND_THRESHOLD, GAP_COMPETITION_THRESHOLD,
    GAP_DEMAND_WEIGHT, GAP_OPPORTUNITY_WEIGHT)
from src.discovery.contracts import HypothesisMode
assert HypothesisMode.GAP_EXPLOIT.value == 'gap_exploit'
print("PASS: all S7.4 symbols importable")
```

## TASK 10 — VERIFY GAP DETECTION WITH SAMPLE DATA
```python
from src.discovery.hypothesis import generate_gap_exploit_hypotheses
scores = [
    {'keyword': 'python automation scripts', 'demand_score': 0.75, 'competition_score': 0.25, 'opportunity_score': 0.80},
    {'keyword': 'ai workflow builder', 'demand_score': 0.80, 'competition_score': 0.30, 'opportunity_score': 0.85},
    {'keyword': 'data pipeline automation', 'demand_score': 0.50, 'competition_score': 0.70, 'opportunity_score': 0.40},
]
results = generate_gap_exploit_hypotheses('python_automation', scores, [])
accepted = [r for r in results if r.accepted]
print(f"Gap hypotheses: {len(results)} total, {len(accepted)} accepted")
for r in accepted: print(f"  '{r.hypothesis_text}' conf={r.specificity_score:.3f}")
```

## TASK 11 — VERIFY EMPTY INPUT HANDLING
```python
from src.discovery.hypothesis import generate_gap_exploit_hypotheses
assert generate_gap_exploit_hypotheses('', [], []) == []
assert generate_gap_exploit_hypotheses('python_automation', [], []) == []
print("PASS: empty input cases handled")
```

## TASK 12 — VERIFY BUDGET GATE AT DEFAULT THRESHOLD (0.50)
```python
from src.discovery.hypothesis import generate_gap_exploit_hypotheses
weak = [{'keyword': f'test_{i}', 'demand_score': 0.62, 'competition_score': 0.35, 'opportunity_score': 0.20}
        for i in range(5)]
results = generate_gap_exploit_hypotheses('python_automation', weak, [])
# opportunity_score 0.20: conf = 0.60*0.62 + 0.40*0.20 = 0.372 + 0.080 = 0.452 < 0.50
accepted = [r for r in results if r.accepted]
print(f"Weak opportunities: {len(accepted)} accepted (expected 0, conf~0.45 < 0.50)")
```

## TASK 13 — VERIFY DEDUPLICATION
```python
from src.discovery.hypothesis import generate_gap_exploit_hypotheses
scores = [{'keyword': 'python automation scripts', 'demand_score': 0.75, 'competition_score': 0.25, 'opportunity_score': 0.80}]
existing = ['python automation scripts']
results = generate_gap_exploit_hypotheses('python_automation', scores, existing)
assert 'python automation scripts' not in [r.hypothesis_text for r in results]
print("PASS: deduplication against existing hypotheses")
```

## TASK 14 — VERIFY S7.2+S7.3 STILL INTACT (no regression)
```python
from src.discovery.hypothesis import (generate_adjacent_keyword_hypotheses, generate_adjacent_niche_hypotheses)
kw = generate_adjacent_keyword_hypotheses('python_automation', ['python automation'], [])
ni = generate_adjacent_niche_hypotheses('python_automation', ['python automation'], [])
print(f"S7.2 keyword: {len(kw)} | S7.3 niche: {len(ni)}")
print("PASS: S7.2+S7.3 intact after S7.4 additions")
```

## TASK 15 — REGRESSION SMOKE
```powershell
C:\Users\kevin\AppData\Local\Programs\Python\Python311\python.exe -m pytest -q tests/unit/ `
    -k "test_cli_config_check_passes or test_golden_anchor_kw110_62_7 or test_discovery_core_loop_budget_gate or test_discovery_hypothesis_confidence_threshold or test_dashboard_opportunities_renders_empty_db_gracefully" `
    --no-header
```

## TASK 16 — GOLDEN PARITY
```powershell
C:\Users\kevin\AppData\Local\Programs\Python\Python311\python.exe run.py score --golden `
    --config-override relevance.enable_stage_3_5=false `
    --config-override analysis.external_signals_enabled=false
```
kw=110 MUST be 62.7/1.0/CONDITIONAL_GO.

## TASK 17 — FULL COVERAGE RUN
```powershell
C:\Users\kevin\AppData\Local\Programs\Python\Python311\python.exe -m pytest -q `
    --cov=src --cov-report=term-missing --cov-fail-under=90 --no-header tests/unit/ `
    | Select-Object -Last 5
```

## TASK 18 — DEMO DATA CHECK
```powershell
Get-ChildItem src\dashboard\pages\ -Filter "*.py" | ForEach-Object {
    if (Get-Content $_.FullName | Select-String "build_dashboard_demo_data") { Write-Host "NO-GO: $($_.Name)" }
}
```
Zero output required.

## TASK 19 — PAGE COUNT
```python
import os
pages = [f for f in os.listdir('src/dashboard/pages') if f.endswith('.py') and f != '__init__.py']
assert len(pages) == 9; print(f"PASS: {len(pages)} pages")
```

## TASK 20 — VERIFY NO NEW DB TABLES
```python
from sqlalchemy import create_engine, inspect
e = create_engine('sqlite:///data/foundation_gate_ci.db')
gap_tables = [t for t in inspect(e).get_table_names() if 'gap_exploit' in t.lower()]
assert not gap_tables, f"Unexpected tables: {gap_tables}"
print("PASS: no new tables for S7.4 (rule-based, no persistence)")
```

## TASK 21 — RUN ALL NEW S7.4 TESTS
```powershell
C:\Users\kevin\AppData\Local\Programs\Python\Python311\python.exe -m pytest -q `
    tests/unit/test_gap_exploit_hypotheses.py -v --no-header
```
All >=30 tests must pass.

## TASK 22 — HYPOTHESIS.py COVERAGE SPECIFIC
```powershell
C:\Users\kevin\AppData\Local\Programs\Python\Python311\python.exe -m pytest -q `
    --cov=src/discovery/hypothesis --cov-report=term-missing --no-header tests/unit/ `
    2>&1 | Select-String "hypothesis|TOTAL" | Select -Last 3
```
hypothesis.py >= 80%.

## TASK 23 — VERIFY WAVE 9 INTACT
```python
from src.pricing import (analyze_price_distribution, calculate_new_seller_pricing,
    build_pricing_export_payload, export_all_pricing)
print("PASS: Wave 9 pricing intact after S7.4 additions")
```

## TASK 24 — VERIFY COMPLETE IMPORT CHAIN
```python
from src.discovery.hypothesis import (
    HypothesisContract, generate_niche_hypotheses,
    generate_adjacent_keyword_hypotheses, generate_adjacent_niche_hypotheses,
    generate_gap_exploit_hypotheses,
    _build_adjacent_candidates, _score_candidate_confidence,
    _build_adjacent_niche_candidates, _score_niche_candidate_confidence,
    _identify_gap_keywords, _score_gap_hypothesis_confidence,
    ADJACENT_NICHE_RELATIONSHIPS, GAP_DEMAND_THRESHOLD, GAP_COMPETITION_THRESHOLD,
    GAP_DEMAND_WEIGHT, GAP_OPPORTUNITY_WEIGHT,
    _WEIGHTS, GATE1_SPECIFICITY_THRESHOLD)
print("PASS: full S7.1+S7.2+S7.3+S7.4 symbol set importable")
```

## TASK 25 — VERIFY SCRAPFLY STILL FALSE
```python
import yaml
cfg = yaml.safe_load(open('config.yaml'))
assert not cfg.get('collection',{}).get('scrapfly',{}).get('enabled')
print("PASS: scrapfly=false")
```

## TASK 26 — VERIFY BASELINE DB UNTOUCHED
```python
import os
mtime = os.path.getmtime('data/cycle037_live.db')
assert abs(mtime - 1780553758) < 10
print(f"PASS: data/cycle037_live.db UNTOUCHED mtime={mtime:.0f}")
```

## TASK 27 — ZONE SELF-VERIFICATION
```powershell
$base = (Invoke-Exe $git 'merge-base origin/develop HEAD').Out.Trim()
(Invoke-Exe $git "log --oneline $base..HEAD").Out
```
B commits: only src/, tests/, docs/CYCLE_068_AGENT_B.md. NEVER PM_Pack/.

## TASK 28 — RECORD TEST COUNT DELTA
```powershell
C:\Users\kevin\AppData\Local\Programs\Python\Python311\python.exe -m pytest --collect-only -q tests/unit/ 2>&1 | Select-String "tests collected" | Select -Last 1
```
Before B: 4675. After B: record delta.

## TASK 29 — VERIFY HypothesisMode HAS ALL 4 VALUES
```python
from src.discovery.contracts import HypothesisMode
expected = {'adjacent_keyword', 'adjacent_niche', 'gap_exploit', 'trend_chase'}
actual = {e.value for e in HypothesisMode}
assert actual == expected, f"Missing: {expected-actual}"
print(f"PASS: HypothesisMode={sorted(actual)}")
```

## TASK 30 — VERIFY GAP CONFIDENCE FORMULA
```python
from src.discovery.hypothesis import _score_gap_hypothesis_confidence, GAP_DEMAND_WEIGHT, GAP_OPPORTUNITY_WEIGHT
kw = {'demand_score': 0.80, 'opportunity_score': 0.70}
expected = GAP_DEMAND_WEIGHT * 0.80 + GAP_OPPORTUNITY_WEIGHT * 0.70
actual = _score_gap_hypothesis_confidence(kw)
assert abs(actual - expected) < 0.001, f"Expected {expected:.3f}, got {actual:.3f}"
print(f"PASS: confidence formula correct: {actual:.3f}")
```

## TASK 31 — VERIFY REASON STRING FORMAT (ACCEPTED/REJECTED)
```python
from src.discovery.hypothesis import generate_gap_exploit_hypotheses
scores = [{'keyword': 'python automation scripts', 'demand_score': 0.75, 'competition_score': 0.25, 'opportunity_score': 0.80}]
results_accept = generate_gap_exploit_hypotheses('python_automation', scores, [], min_confidence=0.0)
results_reject = generate_gap_exploit_hypotheses('python_automation', scores, [], min_confidence=0.99)
for r in results_accept:
    if r.accepted: assert 'ACCEPTED' in r.reason.upper()
for r in results_reject:
    assert 'REJECTED' in r.reason.upper() or r.specificity_score < 0.99
print("PASS: reason strings consistent")
```

## TASK 32 — VERIFY OPPORTUNITY SCORE SORTING
```python
from src.discovery.hypothesis import generate_gap_exploit_hypotheses
scores = [
    {'keyword': 'low_opp', 'demand_score': 0.70, 'competition_score': 0.30, 'opportunity_score': 0.40},
    {'keyword': 'high_opp', 'demand_score': 0.70, 'competition_score': 0.30, 'opportunity_score': 0.90},
    {'keyword': 'mid_opp', 'demand_score': 0.70, 'competition_score': 0.30, 'opportunity_score': 0.65},
]
results = generate_gap_exploit_hypotheses('python_automation', scores, [], min_confidence=0.0)
accepted = [r for r in results if r.accepted]
# high_opp should come first
if len(accepted) >= 2:
    assert accepted[0].hypothesis_text == 'high_opp', f"Expected high_opp first, got {accepted[0].hypothesis_text}"
print("PASS: gap hypotheses sorted by opportunity score descending")
```

## TASK 33 — VERIFY CONSTANTS ARE MODULE-LEVEL
```python
import ast
tree = ast.parse(open('src/discovery/hypothesis.py').read())
top_assigns = [n.targets[0].id for n in ast.walk(tree)
    if isinstance(n, ast.Assign) and isinstance(n.targets[0], ast.Name)]
required_constants = ['GAP_DEMAND_THRESHOLD', 'GAP_COMPETITION_THRESHOLD',
    'GAP_DEMAND_WEIGHT', 'GAP_OPPORTUNITY_WEIGHT']
for c in required_constants:
    assert c in top_assigns, f"Constant {c} not at module level"
print(f"PASS: all 4 gap constants at module level")
```

## TASK 34 — VERIFY GENERATES AUDIT TRAIL (ACCEPTED + REJECTED)
```python
from src.discovery.hypothesis import generate_gap_exploit_hypotheses
scores = [
    {'keyword': 'good_gap', 'demand_score': 0.75, 'competition_score': 0.25, 'opportunity_score': 0.80},
    {'keyword': 'bad_gap', 'demand_score': 0.50, 'competition_score': 0.80, 'opportunity_score': 0.30},
]
results = generate_gap_exploit_hypotheses('python_automation', scores, [], min_confidence=0.50)
# bad_gap won't make it past _identify_gap_keywords (competition > threshold)
# so only good_gap will appear
print(f"Total results: {len(results)} | Accepted: {sum(r.accepted for r in results)}")
print("PASS: audit trail generated")
```

## TASK 35 — VERIFY hypothesis.py FINAL LINE COUNT
```python
n = len(open('src/discovery/hypothesis.py').readlines())
print(f"hypothesis.py: {n} lines (expected 600-700 after S7.4 additions)")
assert 550 <= n <= 750, f"Unexpected size: {n}"
```

## TASK 36 — VERIFY TEST FILE STRUCTURE
```python
import ast, os
f = 'tests/unit/test_gap_exploit_hypotheses.py'
assert os.path.exists(f)
tree = ast.parse(open(f).read())
classes = [n.name for n in ast.walk(tree) if isinstance(n, ast.ClassDef)]
tests = [n.name for n in ast.walk(tree) if isinstance(n, ast.FunctionDef) and n.name.startswith('test_')]
print(f"Classes: {classes} | Tests: {len(tests)}")
assert len(tests) >= 30
```

## TASK 37 — VERIFY FULL CHAIN S7.1-S7.4
```python
for niche in ['python_automation', 'ai_agent_development']:
    scores = [{'keyword': f'{niche} gap tool', 'demand_score': 0.75, 'competition_score': 0.25, 'opportunity_score': 0.80}]
    kw = generate_adjacent_keyword_hypotheses(niche, [niche.replace('_',' ')], [])
    ni = generate_adjacent_niche_hypotheses(niche, [niche.replace('_',' ')], [])
    ga = generate_gap_exploit_hypotheses(niche, scores, [])
    print(f"{niche}: S7.2={len(kw)} kw, S7.3={len(ni)} niche, S7.4={len(ga)} gap")
print("PASS: S7.1-S7.4 coexist")
```

## TASK 38 — COMMIT B WORK
```powershell
Invoke-Exe $git 'add src/ tests/ docs/cycle_reports/CYCLE_068_AGENT_B.md'
Invoke-Exe $git 'diff --cached --name-only'
Invoke-Exe $git 'commit -m "feat(discovery): C068 Wave 10 S7.4 -- gap opportunity hypothesis mode + data-driven gap detection"'
Invoke-Exe $git 'push origin cycle/068/integration'
```

## TASK 39 — VERIFY DEMAND THRESHOLD IS >= (INCLUSIVE)
```python
from src.discovery.hypothesis import _identify_gap_keywords, GAP_DEMAND_THRESHOLD
edge = [{'keyword': 'edge_test', 'demand_score': GAP_DEMAND_THRESHOLD,
         'competition_score': 0.20, 'opportunity_score': 0.70}]
result = _identify_gap_keywords(edge)
assert len(result) == 1, f"Threshold is inclusive: {GAP_DEMAND_THRESHOLD} should be included"
print(f"PASS: demand_threshold {GAP_DEMAND_THRESHOLD} is inclusive (>=)")
```

## TASK 40 — VERIFY COMPETITION THRESHOLD IS <= (INCLUSIVE)
```python
from src.discovery.hypothesis import _identify_gap_keywords, GAP_COMPETITION_THRESHOLD
edge = [{'keyword': 'edge_test', 'demand_score': 0.70,
         'competition_score': GAP_COMPETITION_THRESHOLD, 'opportunity_score': 0.70}]
result = _identify_gap_keywords(edge)
assert len(result) == 1, f"Threshold is inclusive: {GAP_COMPETITION_THRESHOLD} should be included"
print(f"PASS: competition_threshold {GAP_COMPETITION_THRESHOLD} is inclusive (<=)")
```

## TASK 41 — VERIFY ALL S7.4 DELIVERABLES
```python
import os
deliverables = ['src/discovery/hypothesis.py', 'src/discovery/contracts.py',
    'tests/unit/test_gap_exploit_hypotheses.py']
for path in deliverables:
    exists = os.path.exists(f'C:/Fiverr/Fiverr/{path}')
    print(f"{'PASS' if exists else 'MISSING'}: {path}")
```

## TASK 42 — FINAL SUITE RUN AND RECORD
```powershell
C:\Users\kevin\AppData\Local\Programs\Python\Python311\python.exe -m pytest -q `
    --cov=src --cov-fail-under=90 --no-header tests/unit/ | Select-Object -Last 5
```

## TASK 43 — VERIFY NICHE_VALIDATION_CONFIG UNCHANGED
```python
from src.analysis.result_set_validator import NICHE_VALIDATION_CONFIG
assert len(NICHE_VALIDATION_CONFIG) == 9
print(f"PASS: 9 niches unchanged")
```

## TASK 44 — VERIFY test_gap_exploit_hypotheses.py LINE COUNT
```python
n = len(open('tests/unit/test_gap_exploit_hypotheses.py').readlines())
print(f"test_gap_exploit_hypotheses.py: {n} lines")
assert n >= 100, f"Test file too short: {n}"
```

## TASK 45 — ADDITIONAL GAP DETECTION TEST
```python
from src.discovery.hypothesis import _identify_gap_keywords
# All below threshold
all_below = [{'keyword': f'kw{i}', 'demand_score': 0.50, 'competition_score': 0.50, 'opportunity_score': 0.50}
             for i in range(5)]
result = _identify_gap_keywords(all_below)
assert result == [], f"All below threshold: expected [], got {result}"
# All above threshold
all_above = [{'keyword': f'kw{i}', 'demand_score': 0.80, 'competition_score': 0.20, 'opportunity_score': 0.85}
             for i in range(5)]
result = _identify_gap_keywords(all_above)
assert len(result) == 5
print("PASS: threshold boundary detection works")
```

## TASK 46 — VERIFY S7.4 HANDLES DUPLICATE KEYWORDS IN INPUT
```python
from src.discovery.hypothesis import generate_gap_exploit_hypotheses
duped_scores = [
    {'keyword': 'python automation', 'demand_score': 0.75, 'competition_score': 0.25, 'opportunity_score': 0.80},
    {'keyword': 'python automation', 'demand_score': 0.75, 'competition_score': 0.25, 'opportunity_score': 0.80},
]
results = generate_gap_exploit_hypotheses('python_automation', duped_scores, [], min_confidence=0.0)
texts = [r.hypothesis_text for r in results]
print(f"Results from duplicate input: {len(texts)}")
# Implementation may include duplicates — document behavior
```

## TASK 47 — VERIFY S7.4 IS DATA-DRIVEN (NOT STATIC MAP)
```python
# S7.4 should NOT have a static constant like ADJACENT_NICHE_RELATIONSHIPS
import ast
tree = ast.parse(open('src/discovery/hypothesis.py').read())
constants = [n.targets[0].id for n in ast.walk(tree)
    if isinstance(n, ast.Assign) and isinstance(n.targets[0], ast.Name)]
# Should have gap thresholds but NOT a static niche map for gap mode
assert 'GAP_DEMAND_THRESHOLD' in constants
static_maps = [c for c in constants if 'RELATIONSHIP' in c.upper() and 'GAP' in c.upper()]
print(f"Gap static maps (expected 0): {static_maps}")
print("PASS: S7.4 is data-driven (thresholds only, no static map)")
```

## TASK 48 — VERIFY ACCEPTED ITEMS ORDERED BY CONFIDENCE DESC
```python
from src.discovery.hypothesis import generate_gap_exploit_hypotheses
scores = [
    {'keyword': 'kw_a', 'demand_score': 0.90, 'competition_score': 0.10, 'opportunity_score': 0.95},
    {'keyword': 'kw_b', 'demand_score': 0.75, 'competition_score': 0.30, 'opportunity_score': 0.60},
    {'keyword': 'kw_c', 'demand_score': 0.65, 'competition_score': 0.35, 'opportunity_score': 0.70},
]
results = generate_gap_exploit_hypotheses('python_automation', scores, [], min_confidence=0.0)
accepted = [r for r in results if r.accepted]
confs = [r.specificity_score for r in accepted]
if len(confs) > 1:
    assert confs == sorted(confs, reverse=True), f"Not sorted: {confs}"
print(f"PASS: {len(accepted)} accepted, sorted by conf desc: {confs}")
```

## TASK 49 — VERIFY S7.4 FUNCTIONS HAVE CORRECT DOCSTRINGS
```python
from src.discovery.hypothesis import (generate_gap_exploit_hypotheses,
    _identify_gap_keywords, _score_gap_hypothesis_confidence)
for fn in [generate_gap_exploit_hypotheses, _identify_gap_keywords, _score_gap_hypothesis_confidence]:
    assert fn.__doc__ and len(fn.__doc__) > 30, f"{fn.__name__} needs docstring"
    print(f"PASS: {fn.__name__} has docstring ({len(fn.__doc__)} chars)")
```

## TASK 50 — VERIFY WORKFLOW: S7.2 + S7.3 + S7.4 ALL 9 NICHES
```python
from src.discovery.hypothesis import (generate_adjacent_keyword_hypotheses,
    generate_adjacent_niche_hypotheses, generate_adjacent_niche_hypotheses,
    generate_gap_exploit_hypotheses, ADJACENT_NICHE_RELATIONSHIPS)
from src.analysis.result_set_validator import NICHE_VALIDATION_CONFIG
gap_scores = [{'keyword': 'sample_gap', 'demand_score': 0.75, 'competition_score': 0.25, 'opportunity_score': 0.80}]
for niche in sorted(NICHE_VALIDATION_CONFIG.keys()):
    seeds = [niche.replace('_',' ')]
    kw = generate_adjacent_keyword_hypotheses(niche, seeds, [])
    ni = generate_adjacent_niche_hypotheses(niche, seeds, [])
    ga = generate_gap_exploit_hypotheses(niche, gap_scores, [])
    print(f"{niche}: S7.2={len(kw)} S7.3={len(ni)} S7.4={len(ga)}")
print("PASS: All 9 niches × S7.2+S7.3+S7.4 work")
```

## TASK 51 — CONFIG CHECK POST-B
```powershell
C:\Users\kevin\AppData\Local\Programs\Python\Python311\python.exe run.py config-check
```

## TASK 52 — VERIFY COMPETITION SCORE SEMANTICS (LOW = GOOD)
```python
# Verify the system uses competition_score correctly
# HIGH competition_score = many competitors = BAD for entry
# LOW competition_score = few competitors = GOOD gap to exploit
from src.discovery.hypothesis import _identify_gap_keywords
# Low competition = should be included
low_comp = [{'keyword': 'easy_gap', 'demand_score': 0.70, 'competition_score': 0.10, 'opportunity_score': 0.80}]
high_comp = [{'keyword': 'hard_market', 'demand_score': 0.70, 'competition_score': 0.90, 'opportunity_score': 0.80}]
assert len(_identify_gap_keywords(low_comp)) == 1
assert len(_identify_gap_keywords(high_comp)) == 0
print("PASS: competition_score semantics correct (low competition = gap)")
```

## TASK 53 — VERIFY HYPOTHESIS_TEXT IS KEYWORD NOT NICHE_ID
```python
from src.discovery.hypothesis import generate_gap_exploit_hypotheses
scores = [{'keyword': 'python workflow automation', 'demand_score': 0.75, 'competition_score': 0.25, 'opportunity_score': 0.80}]
results = generate_gap_exploit_hypotheses('python_automation', scores, [])
if results:
    assert results[0].hypothesis_text == 'python workflow automation', f"Got: {results[0].hypothesis_text}"
    assert '_' not in results[0].hypothesis_text, "hypothesis_text should be keyword, not niche_id"
    print(f"PASS: hypothesis_text is keyword: '{results[0].hypothesis_text}'")
```

## TASK 54 — FULL REGRESSION PACK
```powershell
C:\Users\kevin\AppData\Local\Programs\Python\Python311\python.exe -m pytest -q tests/unit/ `
    -k "test_ghost_market_excluded_from_go_tag or test_discovery_core_loop_budget_gate or test_discovery_hypothesis_confidence_threshold or test_golden_anchor_kw110_62_7 or test_external_signal_raw_value_stored_and_retrieved or test_cli_config_check_passes or test_dashboard_opportunities_renders_empty_db_gracefully or test_collection_url_encodes_spaces_correctly" `
    --no-header
```

## B REPORT COMPLETION CHECKLIST
```
[ ] GAP_EXPLOIT added to HypothesisMode enum
[ ] GAP_DEMAND_THRESHOLD = 0.60 (module-level constant)
[ ] GAP_COMPETITION_THRESHOLD = 0.40 (module-level constant)
[ ] GAP_DEMAND_WEIGHT = 0.60 + GAP_OPPORTUNITY_WEIGHT = 0.40 (module-level)
[ ] _identify_gap_keywords() implemented (filters demand >= threshold AND competition <= threshold)
[ ] _score_gap_hypothesis_confidence() implemented (weighted demand + opportunity, no base bonus)
[ ] generate_gap_exploit_hypotheses() implemented (budget gate, dedup, sort by opportunity, audit trail)
[ ] test_gap_exploit_hypotheses.py: >= 30 tests, 3 class structure
[ ] S7.2+S7.3 functions intact (no regression)
[ ] Wave 9 pricing intact
[ ] Golden: 62.7/1.0/CONDITIONAL_GO
[ ] Coverage >= 90%, hypothesis.py >= 80%
[ ] Page count: 9 | Demo data: 0 | scrapfly: false
[ ] Zone: only src/ + tests/ + B.md
[ ] B commit SHA recorded
```

## TASK 55 — FINAL B COMMIT SHA RECORD
Record B SHA in B report. C will use this for zone verification.



## TASK 56 — ADDITIONAL PARAMETRIZED TESTS
```python
@pytest.mark.parametrize("demand,competition,count", [
    (0.80, 0.20, 1), (0.60, 0.40, 1), (0.59, 0.40, 0), (0.60, 0.41, 0),
    (1.0,  0.0,  1), (0.0,  1.0,  0), (0.70, 0.50, 0), (1.0,  1.0,  0),
])
def test_gap_criteria_parametrized(demand, competition, count):
    from src.discovery.hypothesis import _identify_gap_keywords
    kw = [{'keyword': 'test', 'demand_score': demand, 'competition_score': competition, 'opportunity_score': 0.7}]
    assert len(_identify_gap_keywords(kw)) == count
```

## TASK 57 — CONFIDENCE PARAMETRIZED
```python
@pytest.mark.parametrize("demand,opp,expected", [
    (1.0, 1.0, 1.0), (0.0, 0.0, 0.0),
    (1.0, 0.0, 0.60), (0.0, 1.0, 0.40),
    (0.5, 0.5, 0.50), (0.80, 0.70, 0.76),
])
def test_confidence_formula_parametrized(demand, opp, expected):
    from src.discovery.hypothesis import _score_gap_hypothesis_confidence
    kw = {'demand_score': demand, 'opportunity_score': opp}
    assert abs(_score_gap_hypothesis_confidence(kw) - expected) < 0.001
```

## TASK 58 — AUDIT TRAIL INCLUDES ALL CANDIDATES
```python
def test_audit_trail_all_candidates():
    from src.discovery.hypothesis import generate_gap_exploit_hypotheses
    scores = [
        {'keyword': 'gap_a', 'demand_score': 0.80, 'competition_score': 0.20, 'opportunity_score': 0.90},
        {'keyword': 'no_gap', 'demand_score': 0.40, 'competition_score': 0.80, 'opportunity_score': 0.30},
    ]
    results = generate_gap_exploit_hypotheses('python_automation', scores, [])
    texts = [r.hypothesis_text for r in results]
    assert 'gap_a' in texts
    assert 'no_gap' not in texts
```

## TASK 59 — ACCEPTED FLAG PRESENT
```python
def test_accepted_flag_present():
    from src.discovery.hypothesis import generate_gap_exploit_hypotheses
    scores = [{'keyword': 'good_gap', 'demand_score': 0.80, 'competition_score': 0.20, 'opportunity_score': 0.85}]
    results = generate_gap_exploit_hypotheses('python_automation', scores, [], min_confidence=0.0)
    assert any(r.accepted for r in results)
```

## TASK 60 — UNIQUENESS IN OUTPUT
```python
def test_no_duplicate_hypothesis_text():
    from src.discovery.hypothesis import generate_gap_exploit_hypotheses
    scores = [
        {'keyword': 'kw_a', 'demand_score': 0.80, 'competition_score': 0.20, 'opportunity_score': 0.85},
        {'keyword': 'kw_b', 'demand_score': 0.75, 'competition_score': 0.25, 'opportunity_score': 0.80},
    ]
    results = generate_gap_exploit_hypotheses('python_automation', scores, [], min_confidence=0.0)
    texts = [r.hypothesis_text for r in results]
    assert len(texts) == len(set(texts))
```

## TASK 61 — SPECIFICITY MATCHES CONFIDENCE FORMULA
```python
def test_specificity_score_matches_confidence():
    from src.discovery.hypothesis import (generate_gap_exploit_hypotheses,
        _score_gap_hypothesis_confidence)
    kw = {'keyword': 'test', 'demand_score': 0.80, 'competition_score': 0.20, 'opportunity_score': 0.85}
    expected = _score_gap_hypothesis_confidence(kw)
    results = generate_gap_exploit_hypotheses('python_automation', [kw], [], min_confidence=0.0)
    if results:
        assert abs(results[0].specificity_score - expected) < 0.001
```

## TASK 62 — WAVE 9 COEXISTENCE
```python
def test_wave9_s74_coexist():
    from src.pricing import analyze_price_distribution
    from src.discovery.hypothesis import generate_gap_exploit_hypotheses
    scores = [{'keyword': 'test', 'demand_score': 0.75, 'competition_score': 0.25, 'opportunity_score': 0.80}]
    results = generate_gap_exploit_hypotheses('python_automation', scores, [])
    assert isinstance(results, list)
    print(f"PASS: Wave 9 + S7.4 coexist ({len(results)} gap results)")
```

## TASK 63 — STRING SCORES HANDLED
```python
def test_string_score_graceful():
    from src.discovery.hypothesis import _score_gap_hypothesis_confidence
    kw = {'demand_score': '0.80', 'opportunity_score': '0.70'}
    try:
        score = _score_gap_hypothesis_confidence(kw)
        assert 0.0 <= score <= 1.0
    except (ValueError, TypeError):
        pass  # acceptable if strict typing
```

## TASK 64 — DEFAULT PARAMETERS VERIFIED
```python
def test_defaults_competition_threshold():
    import inspect
    from src.discovery.hypothesis import generate_gap_exploit_hypotheses, GAP_COMPETITION_THRESHOLD
    sig = inspect.signature(generate_gap_exploit_hypotheses)
    assert sig.parameters['competition_threshold'].default == GAP_COMPETITION_THRESHOLD

def test_defaults_max_hypotheses():
    import inspect
    from src.discovery.hypothesis import generate_gap_exploit_hypotheses
    sig = inspect.signature(generate_gap_exploit_hypotheses)
    assert sig.parameters['max_hypotheses'].default == 10
```

## TASK 65 — COVERAGE AFTER ALL TESTS
```powershell
C:\Users\kevin\AppData\Local\Programs\Python\Python311\python.exe -m pytest -q `
    --cov=src/discovery/hypothesis --cov-report=term-missing --no-header tests/unit/ `
    2>&1 | Select-String "hypothesis" | Select -Last 5
```

## TASK 66 — FULL SUITE PASSES
```powershell
C:\Users\kevin\AppData\Local\Programs\Python\Python311\python.exe -m pytest -q `
    --cov=src --cov-fail-under=90 --no-header tests/unit/ | Select-Object -Last 5
```

## TASK 67 — VERIFY S7.4 FUNCTION LIST IN MODULE
```python
import ast
tree = ast.parse(open('src/discovery/hypothesis.py').read())
gap_fns = [n.name for n in ast.walk(tree) if isinstance(n, ast.FunctionDef) and 'gap' in n.name.lower()]
assert 'generate_gap_exploit_hypotheses' in gap_fns
assert '_identify_gap_keywords' in gap_fns
assert '_score_gap_hypothesis_confidence' in gap_fns
print(f"PASS: all 3 S7.4 functions present: {gap_fns}")
```

## TASK 68 — RECORD HYPOTHESIS.py FINAL LINE COUNT
```python
n = len(open('src/discovery/hypothesis.py').readlines())
print(f"hypothesis.py post-B: {n} lines (expected 600-750)")
assert 550 <= n <= 800, f"Unexpected size: {n}"
```

## TASK 69 — VERIFY TEST CLASS STRUCTURE
```python
import ast
tree = ast.parse(open('tests/unit/test_gap_exploit_hypotheses.py').read())
classes = [n.name for n in ast.walk(tree) if isinstance(n, ast.ClassDef)]
tests = [n.name for n in ast.walk(tree) if isinstance(n, ast.FunctionDef) and n.name.startswith('test_')]
assert len(tests) >= 30, f"Need >= 30 tests, got {len(tests)}"
print(f"PASS: {len(tests)} tests across {len(classes)} classes")
```

## TASK 70 — ZONE SELF-VERIFY + FINAL COMMIT
```powershell
$base = (Invoke-Exe $git 'merge-base origin/develop HEAD').Out.Trim()
(Invoke-Exe $git "log --oneline $base..HEAD").Out
Invoke-Exe $git 'add src/ tests/ docs/cycle_reports/CYCLE_068_AGENT_B.md'
Invoke-Exe $git 'diff --cached --name-only'  # ONLY src/ + tests/ + B.md
Invoke-Exe $git 'commit -m "feat(discovery): C068 Wave 10 S7.4 -- gap opportunity hypothesis mode"'
Invoke-Exe $git 'push origin cycle/068/integration'
```


## SUPPLEMENTAL TESTS FOR B — FINAL BLOCK

## TEST: VERIFY GAP EXPLOIT WITH ALL 9 NICHES
```python
def test_gap_exploit_all_9_niches():
    from src.discovery.hypothesis import generate_gap_exploit_hypotheses
    from src.analysis.result_set_validator import NICHE_VALIDATION_CONFIG
    scores = [{'keyword': 'gap keyword', 'demand_score': 0.75,
               'competition_score': 0.25, 'opportunity_score': 0.80}]
    for niche in sorted(NICHE_VALIDATION_CONFIG.keys()):
        results = generate_gap_exploit_hypotheses(niche, scores, [])
        assert isinstance(results, list)
        for r in results:
            assert r.niche_id == niche
    print("PASS: S7.4 works for all 9 configured niches")
```

## TEST: VERIFY CONSTANTS MODULE-LEVEL
```python
def test_gap_constants_are_module_level():
    import ast
    tree = ast.parse(open('src/discovery/hypothesis.py').read())
    top_level_assigns = [n.targets[0].id for n in tree.body
        if isinstance(n, ast.Assign) and isinstance(n.targets[0], ast.Name)]
    required = ['GAP_DEMAND_THRESHOLD', 'GAP_COMPETITION_THRESHOLD',
                'GAP_DEMAND_WEIGHT', 'GAP_OPPORTUNITY_WEIGHT']
    for c in required:
        assert c in top_level_assigns, f"{c} not at module level"
    print(f"PASS: all 4 gap constants at module level: {required}")
```

## TEST: VERIFY ACCEPTED ITEMS HAVE CONFIDENCE >= THRESHOLD
```python
def test_accepted_items_meet_threshold():
    from src.discovery.hypothesis import generate_gap_exploit_hypotheses
    scores = [{'keyword': f'kw{i}', 'demand_score': 0.80, 'competition_score': 0.20, 'opportunity_score': 0.75}
              for i in range(5)]
    min_conf = 0.55
    results = generate_gap_exploit_hypotheses('python_automation', scores, [], min_confidence=min_conf)
    for r in results:
        if r.accepted:
            assert r.specificity_score >= min_conf, f"Accepted item conf={r.specificity_score:.3f} < {min_conf}"
    print(f"PASS: all accepted items have confidence >= {min_conf}")
```

## TEST: REJECTED ITEMS BELOW THRESHOLD
```python
def test_rejected_items_below_threshold():
    from src.discovery.hypothesis import generate_gap_exploit_hypotheses
    scores = [{'keyword': 'weak_gap', 'demand_score': 0.62,
               'competition_score': 0.38, 'opportunity_score': 0.20}]
    # conf = 0.60*0.62 + 0.40*0.20 = 0.372 + 0.080 = 0.452 < 0.50
    results = generate_gap_exploit_hypotheses('python_automation', scores, [])
    accepted = [r for r in results if r.accepted]
    assert len(accepted) == 0, f"Expected 0 accepted (conf~0.45 < 0.50), got {len(accepted)}"
    print("PASS: weak gap rejected by default threshold (conf~0.45 < 0.50)")
```

## VERIFY COMPLETE S7.4 DELIVERABLE CHECKLIST
```
[ ] HypothesisMode.GAP_EXPLOIT = 'gap_exploit' in contracts.py
[ ] GAP_DEMAND_THRESHOLD = 0.60 (module-level constant)
[ ] GAP_COMPETITION_THRESHOLD = 0.40 (module-level constant)
[ ] GAP_DEMAND_WEIGHT = 0.60 (module-level constant)
[ ] GAP_OPPORTUNITY_WEIGHT = 0.40 (module-level constant)
[ ] _identify_gap_keywords(keyword_scores, *, demand_threshold, competition_threshold)
[ ] _score_gap_hypothesis_confidence(kw_data, *, demand_weight, opportunity_weight)
[ ] generate_gap_exploit_hypotheses(source_niche_id, keyword_scores, existing, *,
     max_hypotheses=10, min_confidence=0.50, demand_threshold=0.60, competition_threshold=0.40)
[ ] test_gap_exploit_hypotheses.py: >= 30 tests in 3 classes
[ ] S7.2 + S7.3 functions INTACT (no regression)
[ ] Wave 9 pricing INTACT
[ ] Golden: 62.7/1.0/CONDITIONAL_GO
[ ] Coverage >= 90%, hypothesis.py >= 80%
[ ] Pages=9, demo=0, scrapfly=false
[ ] Zone: ONLY src/ + tests/ + B.md committed
```

## S7.4 BUSINESS RATIONALE (for B report)
Market gaps are time-sensitive. Unlike adjacent keywords/niches (S7.2/S7.3),
which are stable category relationships, gap opportunities emerge as:
1. Buyer demand grows for a category (demand_score rises)
2. Few quality sellers exist (competition_score stays low)
By using live scoring data, S7.4 automatically surfaces gaps that are
relevant to the CURRENT market state, not a historical snapshot.
This makes S7.4 the most commercially valuable of the Wave 10 hypothesis modes.


## FINAL B VERIFICATION BLOCK

## VERIFY GAP OPPORTUNITY MOST COMMERCIALLY VALUABLE MODE
S7.4 identifies the highest-value market opportunities:
- High demand = buyers actively looking for this service
- Low competition = few quality sellers = easier to rank and win orders
- Unlike S7.2/S7.3 (category exploration), S7.4 = immediate monetizable gaps
Document in B report: commercial rationale for S7.4 implementation priority.

## VERIFY CONFIDENCE FORMULA MATCHES COMMERCIAL INTUITION
confidence = 0.60 × demand_score + 0.40 × opportunity_score
Demand weighted higher (0.60) because:
- Without demand, a low-competition niche is just empty, not an opportunity
- Demand = buyers exist = revenue potential confirmed
- Opportunity amplifies the signal but demand is primary
Document in B report: "demand_weight (0.60) > opportunity_weight (0.40) by design."

## ADDITIONAL REGRESSION SUBSET FOR B REPORT
```powershell
C:\Users\kevin\AppData\Local\Programs\Python\Python311\python.exe -m pytest -q tests/unit/ `
    -k "test_ghost_market_excluded_from_go_tag or test_discovery_core_loop_budget_gate or test_discovery_hypothesis_confidence_threshold or test_golden_anchor_kw110_62_7 or test_dashboard_opportunities_renders_empty_db_gracefully or test_external_signal_raw_value_stored_and_retrieved" `
    --no-header 2>&1 | Select-Object -Last 3
```

## B REPORT MINIMUM REQUIRED SECTIONS
1. SHA: [B commit SHA]
2. Zone verification: git show --name-only [B SHA]
3. Files modified: src/discovery/hypothesis.py, src/discovery/contracts.py
4. Files created: tests/unit/test_gap_exploit_hypotheses.py
5. Test count: N total, all pass
6. Coverage: hypothesis.py X%, overall Y%
7. S7.4 functions: generate_gap_exploit_hypotheses(), _identify_gap_keywords(), _score_gap_hypothesis_confidence()
8. Constants: GAP_DEMAND_THRESHOLD=0.60, GAP_COMPETITION_THRESHOLD=0.40, weights=0.60+0.40
9. Golden: 62.7/1.0/CONDITIONAL_GO
10. S7.2+S7.3+Wave9 intact confirmed

## B FINAL CLOSURE — S7.4 COMPLETE
S7.4 Gap Opportunity: generate_gap_exploit_hypotheses() committed.
Data-driven. No static map. No LLM. No new tables. Budget gate 0.50.

## B DONE: 55 tasks complete. S7.4 implemented. Floor met.

END OF PROMPT
