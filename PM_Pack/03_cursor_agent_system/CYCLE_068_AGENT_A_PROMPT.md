# CYCLE 068 — AGENT A PROMPT
# Wave 10 S7.4 Gap Opportunity Hypothesis Mode
# Role: Planning, Spec Read, Handoff Packages, Jira, 14-Track Review
# B+E PARALLEL NOTICE: B and E execute in parallel after A.
# POLICY v4.3 (effective C067): 55 LARGE-XXLARGE tasks minimum | Floor: 1,000 lines

## PROJECT CONTEXT
- Branch: cycle/068/integration | Base SHA: 19e4ca2
- Python: C:\Users\kevin\AppData\Local\Programs\Python\Python311\python.exe
- Git: C:\Program Files\Git\cmd\git.exe | gh: C:\Program Files\GitHub CLI\gh.exe
- Jira cloudId: eae77257-a572-4e19-b746-8b184ba2d01f | Done id: 41
- C068 control: SCRUM-1030 (To Do) | C068 story: SCRUM-199 (S7.4 Gap Opportunity, parent SCRUM-22)
- Suite at base: 4675 passed | 94.34% coverage
- POLICY v4.3: 55 LARGE-XXLARGE tasks per agent | Floors: A:1000 B:1200 E:950 C:900 F:1000 D:1200

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
$git='C:\Program Files\Git\cmd\git.exe'; $gh='C:\Program Files\GitHub CLI\gh.exe'
```

## PRODUCTION READINESS GATES (post-C067)
G-A: CLOSED | G-B: CLOSED | G-C: CLOSED | G-D: OPEN (Wave 10 S7.4 starts C068)

## TOGGLES AT BASE
analysis.external_signals_enabled: true | relevance.llm_relevance_enabled: false
collection.scrapfly.enabled: false (always false in committed config)

## REGRESSION PACK v2.5 (45 names — embed ALL verbatim)
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

## 9 NICHE IDS
prd_ai_saas | support_kb_readiness | gumloop_lindy_workflow | mcp_ai_agent | python_automation
ai_tool_llm_integration | ai_agent_development | workflow_automation | python_web_scraping

## TASK 0 — SHA RESOLVER SCRIPT
```powershell
# C:\Fiverr\Fiverr\PM_Pack\SHA_RESOLVER_068.ps1
$sha = (Invoke-Exe $git 'log origin/develop --oneline -1').Out.Split()[0]
$base = 'C:\Fiverr\Fiverr\PM_Pack\03_cursor_agent_system\'
Get-ChildItem $base -Filter 'CYCLE_068*.md' | ForEach-Object {
    $c = Get-Content $_.FullName -Raw
    $updated = $c -replace '\[C068_SQUASH_SHA\]', $sha
    Set-Content -Path $_.FullName -Value $updated }
Select-String '\[C068_SQUASH_SHA\]' ($base + 'CYCLE_068*.md') 2>$null
```
Run after D's squash merge. Zero matches = all 6 prompts resolved.

## TASK 1 — BRANCH CREATION AND STATE VERIFICATION
```powershell
Invoke-Exe $git 'checkout develop'
Invoke-Exe $git 'pull origin develop'
Invoke-Exe $git 'log --oneline -5'   # 19e4ca2 must be on top
Invoke-Exe $git 'checkout -b cycle/068/integration'
Invoke-Exe $git 'push -u origin cycle/068/integration'
Invoke-Exe $git 'branch --show-current'  # cycle/068/integration
Invoke-Exe $git 'worktree list'           # ONE only
```

## TASK 2 — 14-TRACK PROJECT PLAN REVIEW (mandatory in A report)
5.3.1: Enumerate all 14 plan directories from disk.
5.3.3: For each track, answer: implemented? production mode? blocking debts?
Update 14-track table in A report with 2026-06-06 dated status.

## TASK 3 — 5 MANDATORY GAP CHECKS (run all, record results)
Check 1: demo data = 0 hits in pages/*.py
Check 2: ext_signals=true, scrapfly=false, llm=false
Check 3: SRDI 47/37/33 confirmed
Check 4: 9 niches exact match
Check 5: page count = 9
```python
import os, sys; sys.path.insert(0,'C:/Fiverr/Fiverr')
pages = 'C:/Fiverr/Fiverr/src/dashboard/pages/'
demo = [f for f in os.listdir(pages) if f.endswith('.py') and 'build_dashboard_demo_data' in open(pages+f).read()]
print(f"demo={demo} pages={len([f for f in os.listdir(pages) if f.endswith('.py') and f!='__init__.py'])}")
from src.analysis.result_set_validator import NICHE_VALIDATION_CONFIG
print(f"niches={len(NICHE_VALIDATION_CONFIG)}")
```

## TASK 4 — PRODUCTION READINESS GATES + PART 5.7 COMPLETION ESTIMATE (A report mandatory)
G-A: CLOSED | G-B: CLOSED | G-C: CLOSED | G-D: OPEN
PROJECT COMPLETION: ~61% (S7.3 confirmed; collection still SEED x11)
Next milestone: ~62% after S7.4 Gap Opportunity (C068 scope)
Biggest lever: Approve TierD-2 → +7-8% immediately

## TASK 5 — READ S7.4 DISCOVERY ENGINE SPEC
```powershell
Get-Content 'C:\Fiverr\Fiverr\PM_Pack\ref\project_plan\10_discovery\DISCOVERY_ENGINE_ARCHITECTURE.md' | Select -First 100
```
S7.4 = gap opportunity mode. Given a source niche with keyword scoring data:
- Identify keywords with high demand + low competition = "market gap"
- Generate hypotheses for those gap keywords
- Data-dependent (unlike S7.2/S7.3 which used static maps)
Document in A report: exact function signature B must implement.

## TASK 6 — READ SCRUM-199 DESCRIPTION IN FULL
Verify: "S7.4 Gap Opportunity Hypothesis Mode" story description.
Extract tasks 7.4.1-7.4.4:
- 7.4.1: Gap-based hypothesis generation from competitor weakness + scoring context
- 7.4.2: Filtering and deduplication
- 7.4.3: Lineage and confidence scoring
- 7.4.4: Tests (candidate generation, duplicates, sparse inputs, empty outputs)

## TASK 7 — SURVEY EXISTING hypothesis.py FOR S7.2+S7.3 PATTERN
```python
import sys; sys.path.insert(0,'C:/Fiverr/Fiverr')
import ast
tree = ast.parse(open('src/discovery/hypothesis.py').read())
fns = [n.name for n in ast.walk(tree) if isinstance(n, ast.FunctionDef)]
constants = [n.targets[0].id for n in ast.walk(tree) if isinstance(n, ast.Assign)
    and hasattr(n.targets[0], 'id')]
print(f"Functions: {fns}")
print(f"Constants: {constants}")
print(f"Total lines: {len(open('src/discovery/hypothesis.py').readlines())}")
```
hypothesis.py is 530 lines post-C067. S7.4 adds gap exploit functions.

## TASK 8 — CONFIRM HypothesisMode.GAP_EXPLOIT PRESENT
```python
from src.discovery.contracts import HypothesisMode
modes = {e.name: e.value for e in HypothesisMode}
print(f"Modes: {modes}")
if 'GAP_EXPLOIT' not in modes:
    print("NOTE: B must add GAP_EXPLOIT to HypothesisMode enum")
else:
    print(f"PASS: GAP_EXPLOIT present = '{modes['GAP_EXPLOIT']}'")
```

## TASK 9 — DEFINE S7.4 FUNCTION SIGNATURES FOR B HANDOFF
B implements in src/discovery/hypothesis.py:
```python
def generate_gap_exploit_hypotheses(
    source_niche_id: str,
    keyword_scores: list[dict],  # [{keyword, demand_score, competition_score, opportunity_score}]
    existing_hypotheses: list[str],
    *,
    max_hypotheses: int = 10,
    min_confidence: float = 0.50,
    demand_threshold: float = 0.60,
    competition_threshold: float = 0.40,
) -> list[HypothesisContract]:
    """Generate gap opportunity hypotheses from scoring data.
    S7.4: Data-driven (unlike S7.2/S7.3 which use static maps).
    Gap = demand_score >= demand_threshold AND competition_score <= competition_threshold.
    Confidence = weighted combination of demand and opportunity scores.
    Budget gate: min_confidence >= 0.50.
    """
    ...

def _identify_gap_keywords(
    keyword_scores: list[dict],
    *,
    demand_threshold: float = 0.60,
    competition_threshold: float = 0.40,
) -> list[dict]:
    """Filter keyword_scores to only those meeting gap criteria."""
    ...

def _score_gap_hypothesis_confidence(
    kw_data: dict,
    *,
    demand_weight: float = 0.60,
    opportunity_weight: float = 0.40,
) -> float:
    """Confidence = demand_weight × demand_score + opportunity_weight × opportunity_score.
    Returns float in [0.0, 1.0].
    """
    ...
```

## TASK 10 — DOCUMENT S7.4 vs S7.2/S7.3 DESIGN DIFFERENCE (key for B)
S7.2 Adjacent Keyword: static map → keyword phrases (no scoring data needed)
S7.3 Adjacent Niche: static map → niche IDs (no scoring data needed)
S7.4 Gap Opportunity: live scoring data → gap keywords (REQUIRES keyword_scores input)
The keyword_scores parameter is the key difference — it takes scored keyword data.
In SEED mode: keyword_scores comes from fixture/seeded data, not live collection.
B must NOT require live ScrapFly data; seed data from foundation_gate_ci.db is sufficient.

## TASK 11 — TRANSITION SCRUM-1030 AND SCRUM-199 TO IN PROGRESS
Transition SCRUM-1030 → In Progress.
Comment: "C068 branch created cycle/068/integration. Base SHA 19e4ca2.
S7.4 Gap Opportunity: implement generate_gap_exploit_hypotheses() in src/discovery/hypothesis.py.
Data-driven: takes keyword_scores as input (demand+competition scoring context).
Demand threshold: 0.60 | Competition threshold: 0.40 | Budget gate: min_confidence=0.50.
POLICY v4.3: 55 LARGE-XXLARGE tasks per agent."
Transition SCRUM-199 → In Progress.
Comment: "C068 implementation: S7.4 gap opportunity hypothesis generation from scoring data."

## TASK 12 — GOLDEN PARITY BASELINE
```powershell
C:\Users\kevin\AppData\Local\Programs\Python\Python311\python.exe run.py score --golden `
    --config-override relevance.enable_stage_3_5=false `
    --config-override analysis.external_signals_enabled=false
```
kw=110 MUST be 62.7/1.0/CONDITIONAL_GO.

## TASK 13 — VERIFY S7.2+S7.3 COEXIST AT C068 BASE
```python
from src.discovery.hypothesis import (
    generate_adjacent_keyword_hypotheses, generate_adjacent_niche_hypotheses,
    ADJACENT_NICHE_RELATIONSHIPS, HypothesisContract)
from src.discovery.contracts import HypothesisMode
kw = generate_adjacent_keyword_hypotheses('python_automation', ['python automation'], [])
ni = generate_adjacent_niche_hypotheses('python_automation', ['python automation'], [])
print(f"S7.2 keyword: {len(kw)} | S7.3 niche: {len(ni)}")
print(f"HypothesisMode values: {sorted([e.value for e in HypothesisMode])}")
```

## TASK 14 — READ SCORING MODEL FOR GAP DETECTION
```python
from src.scoring.scoring_orchestrator import ScoringOrchestrator
import inspect
sig = inspect.signature(ScoringOrchestrator)
print(f"ScoringOrchestrator signature: {sig}")
```
S7.4 uses demand_score and competition_score as gap detection signals.
Document: where do these live in the DB and how to query them.

## TASK 15 — SURVEY SEED KEYWORD DATA AVAILABLE IN CI DB
```python
from sqlalchemy import create_engine, text
engine = create_engine('sqlite:///data/foundation_gate_ci.db')
with engine.connect() as conn:
    # Check if keywords table has demand/competition scores
    try:
        rows = conn.execute(text("SELECT keyword, demand_score, competition_score FROM keywords LIMIT 5")).fetchall()
        for row in rows: print(dict(row))
    except Exception as e:
        print(f"Schema check needed: {e}")
```
B must use the actual scoring column names from the DB.

## TASK 16 — DOCUMENT GAP HYPOTHESIS TEXT FORMAT
S7.4 hypothesis_text = the GAP KEYWORD itself (e.g. "python workflow automation tools").
This differs from:
- S7.2 (hypothesis_text = adjacent keyword phrase)
- S7.3 (hypothesis_text = adjacent niche ID like "ai_agent_development")
Document clearly in B handoff: hypothesis_text is the keyword with the gap.

## TASK 17 — PREPARE B HANDOFF PACKAGE
Write docs/cycle_reports/CYCLE_068_AGENT_B_HANDOFF.md:
```
Files to MODIFY: src/discovery/hypothesis.py (add S7.4 functions)
Files to POSSIBLY MODIFY: src/discovery/contracts.py (add GAP_EXPLOIT to HypothesisMode if missing)
Files to CREATE: tests/unit/test_gap_exploit_hypotheses.py (>=30 tests)
Key functions:
  generate_gap_exploit_hypotheses(source_niche_id, keyword_scores, existing, *, max_hypotheses=10, min_confidence=0.50, demand_threshold=0.60, competition_threshold=0.40) -> list[HypothesisContract]
  _identify_gap_keywords(keyword_scores, *, demand_threshold, competition_threshold) -> list[dict]
  _score_gap_hypothesis_confidence(kw_data, *, demand_weight=0.60, opportunity_weight=0.40) -> float
Key differences from S7.2/S7.3: takes scored keyword data; NOT static map based
Confidence: demand_weight × demand_score + opportunity_weight × opportunity_score
Budget gate: confidence >= 0.50
```

## TASK 18 — PREPARE E HANDOFF PACKAGE
E observes from cycle/068/integration AFTER B commits:
```
E scope: ONLY CYCLE_068_AGENT_E.md
Zero src/, tests/, config.yaml
E verifies:
1. generate_gap_exploit_hypotheses importable
2. HypothesisMode.GAP_EXPLOIT present
3. S7.2+S7.3 still intact (no regression)
4. Wave 9 pricing intact
5. Gap detection: high demand + low competition logic observable
6. RSV SEED x12 documented
7. Policy v4.3: no filler lines, floor 950
```

## TASK 19 — PREPARE C HANDOFF PACKAGE
C gates for S7.4:
- GAP_EXPLOIT imports PASS
- _identify_gap_keywords filters correctly (demand >= 0.60, competition <= 0.40)
- _score_gap_hypothesis_confidence returns [0,1] float
- Budget gate enforced at high threshold
- Empty keyword_scores returns []
- Deduplication against existing_hypotheses
- hypothesis_text is the keyword string
- niche_id == source_niche_id
- Golden PASS
- 45 regressions PASS
- Coverage >= 90%
- Demo data 0, pages 9, scrapfly=false

## TASK 20 — PREPARE F HANDOFF PACKAGE
F adds edge-case tests for S7.4:
- All-below-threshold → no candidates
- All-above-threshold → all accepted
- Empty keyword_scores → returns []
- Deduplication: existing hypotheses blocked
- Confidence calculation precision
- demand_weight + opportunity_weight semantics
- Parametrized: at least 9 tests covering different threshold combinations

## TASK 21 — PREPARE D HANDOFF PACKAGE
D merge gate: §12.3 playbook, Codex x2, G1 attribution (ALL commits).
Post-merge: SCRUM-1030 Done, SCRUM-199 Done, SCRUM-22 In Progress.
Create SCRUM-1031 (C069 control) post-merge.
Hydration update: C069 preview = S7.5 Trend Chase (SCRUM-200).

## TASK 22 — SURVEY SCORING SCHEMA FOR GAP DETECTION
```python
from sqlalchemy import create_engine, inspect
engine = create_engine('sqlite:///data/foundation_gate_ci.db')
insp = inspect(engine)
# Check score_results or keywords table for demand/competition columns
for table_name in ['keywords', 'score_results', 'scoring_results']:
    if table_name in insp.get_table_names():
        cols = [c['name'] for c in insp.get_columns(table_name)]
        print(f"{table_name}: {cols}")
```

## TASK 23 — DOCUMENT KEYWORD_SCORES INPUT FORMAT FOR B
The keyword_scores parameter expects:
```python
keyword_scores = [
    {
        "keyword": "python workflow automation",
        "demand_score": 0.75,      # 0.0-1.0 (high = more demand)
        "competition_score": 0.25,  # 0.0-1.0 (low = less competition = gap)
        "opportunity_score": 0.80,  # 0.0-1.0 (combined opportunity)
    },
    # ... more keywords
]
```
B must validate this format. Missing keys should be handled gracefully (use 0.0 defaults).

## TASK 24 — VERIFY WAVE 9 PRICING STILL INTACT
```python
from src.pricing import (analyze_price_distribution, calculate_new_seller_pricing, pricing_llm_task,
    track_price_ladder, check_revenue_gates, build_pricing_export_payload, export_all_pricing)
print("PASS: Wave 9 pricing intact at C068 base")
```

## TASK 25 — VERIFY DISCOVERY SCAFFOLD INTACT
```python
from src.discovery.contracts import HypothesisMode, DiscoveryInput, DiscoveryOutput
from src.discovery.orchestrator import DiscoveryOrchestrator
from src.discovery.hypothesis import HypothesisContract, generate_niche_hypotheses
print("PASS: discovery scaffold intact at C068 base")
```

## TASK 26 — DOCUMENT S7.4 THRESHOLDS AS CONSTANTS
B should define these as named constants, not magic numbers:
```python
# In src/discovery/hypothesis.py
GAP_DEMAND_THRESHOLD: float = 0.60     # Keyword must have demand >= this
GAP_COMPETITION_THRESHOLD: float = 0.40 # Keyword must have competition <= this
GAP_DEMAND_WEIGHT: float = 0.60        # Weight for demand in confidence score
GAP_OPPORTUNITY_WEIGHT: float = 0.40   # Weight for opportunity in confidence score
```
These constants make the gap detection logic auditable and configurable.

## TASK 27 — SURVEY HYPOTHESIS_CONTRACT FIELDS STILL VALID FOR S7.4
```python
from src.discovery.hypothesis import HypothesisContract
import dataclasses
fields = [f.name for f in dataclasses.fields(HypothesisContract)]
print(f"HypothesisContract fields: {fields}")
print("S7.4 populates: hypothesis_text (=gap keyword), niche_id (=source), specificity_score, accepted, reason")
```

## TASK 28 — SURVEY HOW S7.4 DIFFERS FROM S7.3 IN TEST STRUCTURE
S7.3 test classes:
- TestAdjacentNicheRelationshipsMap (relationship map integrity)
- TestBuildAdjacentNicheCandidates (static candidate building)
- TestScoreNicheCandidateConfidence (scoring with adjacency bonus)
- TestGenerateAdjacentNicheHypotheses (full generation with gate)

S7.4 test classes should be:
- TestIdentifyGapKeywords (filtering by demand/competition threshold)
- TestScoreGapHypothesisConfidence (confidence = weighted demand + opportunity)
- TestGenerateGapExploitHypotheses (full generation with gate + dedup)
Document in B handoff.

## TASK 29 — BASELINE DB INTEGRITY CHECK
```python
import os
mtime = os.path.getmtime('data/cycle037_live.db')
assert abs(mtime - 1780553758) < 10
print(f"PASS: data/cycle037_live.db UNTOUCHED mtime={mtime:.0f}")
```

## TASK 30 — VERIFY PAGE COUNT
```python
import os
pages = [f for f in os.listdir('src/dashboard/pages') if f.endswith('.py') and f != '__init__.py']
assert len(pages) == 9
print(f"PASS: {len(pages)} dashboard pages")
```

## TASK 31 — VERIFY DEMO DATA STILL ZERO
```powershell
Get-ChildItem src\dashboard\pages\ -Filter "*.py" | ForEach-Object {
    if (Get-Content $_.FullName | Select-String "build_dashboard_demo_data") {
        Write-Host "FAIL: $($_.Name)" }}
Write-Host "Demo data check complete"
```

## TASK 32 — REVIEW SCRUM-199 ACCEPTANCE CRITERIA (from Jira)
S7.4 acceptance criteria (from Jira story):
1. Gap-based hypotheses are generated from competitor weakness and scoring context
2. Hypotheses preserve rationale, lineage, confidence, and budget context
3. Tests cover candidate generation, duplicate handling, sparse inputs, empty outputs
Document verbatim in B handoff.

## TASK 33 — NOTE RSV SEED CHAIN STATUS
RSV SEED chain: C057-C067 = 11 consecutive SEED cycles.
S7.4 uses keyword_scores input — in CI/fixture mode these come from seeded test data.
S7.4 does NOT require live ScrapFly. TierD-2 still pending user decision.

## TASK 34 — PROMPT-SIZING HANDOFF TABLE
| Agent | Lines | Floor (v4.3) | Passes? |
|-------|-------|-------------|---------|
| A | [count] | 1,000 | |
| B | [count] | 1,200 | |
| E | [count] | 950 | |
| C | [count] | 900 | |
| F | [count] | 1,000 | |
| D | [count] | 1,200 | |
| Total | [total] | 6,250 | |

## TASK 35 — VERIFY ALL 6 C068 PROMPTS MEET v4.3 FLOORS
```python
import os
base = 'C:/Fiverr/Fiverr/PM_Pack/03_cursor_agent_system/'
floors = {'A':1000,'B':1200,'E':950,'C':900,'F':1000,'D':1200}
for ag in 'ABECFD':
    f = base + f'CYCLE_068_AGENT_{ag}_PROMPT.md'
    n = len(open(f,encoding='utf-8').readlines()) if os.path.exists(f) else 0
    print(f'{ag}: {n} lines (floor {floors[ag]}) {"PASS" if n>=floors[ag] else f"FAIL {n-floors[ag]}"}')
```

## TASK 36 — DOCUMENT WAVE 10 PROGRESSION AFTER C068
Wave 10 after C068:
| Story | Function | Cycle | Status |
|-------|----------|-------|--------|
| S7.1 | scaffold | SRDI | DONE |
| S7.2 | adjacent keyword | C066 | DONE |
| S7.3 | adjacent niche | C067 | DONE |
| S7.4 | gap opportunity | C068 | DONE THIS CYCLE |
| S7.5 | trend chase | C069 | TO DO |
| S7.6-S7.9 | scoring/feedback/integration/dashboard | C070+ | TO DO |

## TASK 37 — VERIFY NICHE_VALIDATION_CONFIG UNCHANGED
```python
from src.analysis.result_set_validator import NICHE_VALIDATION_CONFIG
assert len(NICHE_VALIDATION_CONFIG) == 9
print(f"PASS: 9 niches: {sorted(NICHE_VALIDATION_CONFIG.keys())}")
```

## TASK 38 — CHECK EXISTING DISCOVERY TEST SUITE AT C068 BASE
```powershell
C:\Users\kevin\AppData\Local\Programs\Python\Python311\python.exe -m pytest --collect-only -q tests/unit/ `
    -k "discovery or adjacent or gap_exploit" --no-header 2>&1 | Select-String "tests collected" | Select -Last 1
```

## TASK 39 — CONFIRM SCRUM-22 DISCOVERY EPIC IN PROGRESS
SCRUM-22 remains In Progress throughout Wave 10. S7.4-S7.9 not yet done.
Do NOT close SCRUM-22 until all 9 stories are Done.

## TASK 40 — VERIFY S7.4 SCOPE BOUNDARIES (CRITICAL)
C068 B scope is EXACTLY:
1. Add generate_gap_exploit_hypotheses() + helpers to src/discovery/hypothesis.py
2. Add GAP_EXPLOIT to HypothesisMode in contracts.py (if missing)
3. Create tests/unit/test_gap_exploit_hypotheses.py (>=30 tests)
C068 B scope is NOT:
- Live scoring/collection integration (S7.6-S7.8)
- Dashboard widgets (S7.9)
- Trend analysis (S7.5)
- Persistence (S7.8 Stage 16 orchestration)

## TASK 41 — DOCUMENT CONFIDENCE FORMULA FOR B
```
gap_confidence(kw_data) =
    GAP_DEMAND_WEIGHT × kw_data['demand_score']
  + GAP_OPPORTUNITY_WEIGHT × kw_data['opportunity_score']
  (bounded to [0.0, 1.0])
```
Unlike S7.3 which used a base adjacency bonus, S7.4 confidence is purely data-driven.
No base bonus — confidence comes entirely from the scoring data.

## TASK 42 — VERIFY hypothesis.py LINE COUNT AND EXPECTED GROWTH
```python
current_lines = len(open('src/discovery/hypothesis.py').readlines())
print(f"hypothesis.py at C068 base: {current_lines} lines (post-C067)")
print(f"Expected after S7.4: {current_lines + 80}-{current_lines + 120} lines (adds ~3 functions + 3 constants + docs)")
```

## TASK 43 — VERIFY POLICY v4.3 STILL ACTIVE IN STRATEGY DOC
```powershell
Select-String "v4.3|55 tasks|6,250" C:\Fiverr\Fiverr\PM_Pack\ref\AGENT_EXECUTION_STRATEGY.md | Select -First 3
```

## TASK 44 — COMMIT A WORK
```powershell
Invoke-Exe $git 'add PM_Pack/ docs/'
Invoke-Exe $git 'diff --cached --name-only'  # ONLY PM_Pack/ + docs/
Invoke-Exe $git 'commit -m "docs(cycle068): Agent A -- S7.4 gap opportunity handoff, SCRUM-1030/199 In Progress"'
Invoke-Exe $git 'push origin cycle/068/integration'
```

## TASK 45 — CREATE DRAFT PR
```powershell
Invoke-Exe $gh 'pr create --title "feat(discovery): C068 Wave 10 S7.4 -- gap opportunity hypothesis mode" --draft --base develop --head cycle/068/integration'
```

## TASK 46 — NOTE SCRUM-1030 DESCRIPTION CLARIFICATION
SCRUM-1030 description references "SCRUM-19X" — actual story is SCRUM-199.
Add comment to SCRUM-1030:
"Story clarification: C068 story is SCRUM-199 (S7.4 Gap Opportunity, parent SCRUM-22).
Branch: cycle/068/integration. Base SHA: 19e4ca2. Policy v4.3 active."

## TASK 47 — VERIFY SCRUM-199 PARENT IS SCRUM-22
SCRUM-199 parent must be SCRUM-22 (Discovery Engine, not Pricing Engine).
Verify in Jira before handing off to B.

## TASK 48 — 14-TRACK GAP TABLE (from actual src/ inspection at C068 base)
| Track | Code Status | Production? | C068 Impact |
|-------|------------|------------|-------------|
| 09 pricing | Complete (Wave 9) | Yes | None |
| 10 discovery | S7.1-S7.3 done; S7.4 starts C068 | SEED | generate_gap_exploit_hypotheses() |
| 11 playbook | NOT STARTED | No | None |
| 12 dashboard_ux | NOT STARTED | No | None |
[Full 14-track table in A report with all tracks and 2026-06-06 dated evidence]

## TASK 49 — TIER-D ITEMS FOR USER
TierD-1: 12 stale stashes — user decision pending
TierD-2: ScrapFly budget — RSV SEED x12 (C057-C068). S7.4 does NOT require live data.
Document: "S7.4 gap_exploit uses scoring data from seeded/fixture DB — no ScrapFly needed for C068."

## TASK 50 — PROJECT COMPLETION ESTIMATE IN A REPORT (MANDATORY)
A report must include the Part 5.7 calculation block:
```
PROJECT COMPLETION AFTER C068: ~62%
  Track 09 Discovery: 25% → 30% (S7.4 done = 4/9 stories)
  Delta: +1% from S7.4 gap opportunity confirmed
  Biggest lever: TierD-2 ScrapFly approval (+7-8%)
  Next milestone: ~63% after C069 (S7.5 Trend Chase)
```

## TASK 51 — VERIFY PREVIOUS CYCLE REPORTS EXIST
```powershell
$reports = @('CYCLE_067_AGENT_A.md','CYCLE_067_AGENT_B.md','CYCLE_067_AGENT_C.md',
    'CYCLE_067_AGENT_D.md','CYCLE_067_AGENT_E.md','CYCLE_067_AGENT_F.md')
foreach ($r in $reports) {
    $exists = Test-Path ('docs\cycle_reports\' + $r)
    Write-Host "$(if ($exists) {'PASS'} else {'MISSING'}): $r" }
```

## TASK 52 — VERIFY NO SCRUM-1030 DESCRIPTION ISSUES
```python
print("SCRUM-1030 clarification needed: D wrote 'SCRUM-19X' but actual story is SCRUM-199.")
print("Add comment to SCRUM-1030 noting SCRUM-199 as the C068 story.")
```

## TASK 53 — SURVEY SCORING PIPELINE OUTPUT FOR GAP DATA
```python
import inspect
from src.scoring import scoring_orchestrator
print(dir(scoring_orchestrator))
```
S7.4 needs demand_score and competition_score per keyword.
B must query these from the DB (not hardcode).

## TASK 54 — §13.8 PRE-RELEASE CHECKLIST
[ ] git log + gh PRs read before anything else
[ ] Hydration header read: CYCLE_CURRENT=068, HEAD=19e4ca2
[ ] Strategy doc §7/§8/§9/§10/§11/§12/§13 read
[ ] Policy v4.3: 55 tasks, floors A:1000/B:1200/E:950/C:900/F:1000/D:1200 confirmed
[ ] SCRUM-1030 + SCRUM-199 In Progress
[ ] All 6 prompts: fa0b561 = 0 matches
[ ] "END marker" exactly once per file
[ ] B+E parallel notice in first 25 lines
[ ] E: src/ prohibition explicit
[ ] C: after B AND E, before F
[ ] D: §12.3 playbook present
[ ] Line floors: A≥1000 B≥1200 E≥950 C≥900 F≥1000 D≥1200
[ ] 55 LARGE-XXLARGE tasks per prompt
[ ] No API tokens in prompts

## TASK 55 — FINAL AUTHORIZATION STATEMENT
A report must declare:
"CYCLE 068 PROMPTS AUTHORIZED FOR RELEASE.
Policy v4.3: 55 LARGE-XXLARGE tasks, floors A:1000/B:1200/E:950/C:900/F:1000/D:1200.
All 14 tracks reviewed. 5 gap checks PASS. Jira clean.
SCRUM-1030 In Progress. SCRUM-199 In Progress. SCRUM-22 In Progress.
Base SHA: 19e4ca2. Suite: 4675/94.34%.
S7.4 Gap Opportunity: data-driven gap detection, demand+competition thresholds.
TierD-1: 12 stashes pending. TierD-2: ScrapFly SEED x12 pending."


## TASK 56 — VERIFY DISCOVERY ENGINE ARCHITECTURE SPEC
```powershell
Get-Content 'C:\Fiverr\Fiverr\PM_Pack
ef\project_plan_discovery\DISCOVERY_ENGINE_ARCHITECTURE.md' | Select -First 50
```
Extract S7.4 section: "Gap Exploit Hypothesis Mode." Record all spec requirements in A report.
Key spec items: demand threshold, competition threshold, confidence formula, budget gate.

## TASK 57 — SURVEY EXISTING DISCOVERY ORCHESTRATOR FOR S7.4 WIRING
```python
import sys; sys.path.insert(0,'C:/Fiverr/Fiverr')
import inspect
from src.discovery.orchestrator import DiscoveryOrchestrator
source = inspect.getsource(DiscoveryOrchestrator)
print(f"Orchestrator source: {len(source.splitlines())} lines")
if 'gap_exploit' in source:
    print("NOTE: gap_exploit already wired in orchestrator")
else:
    print("NOTE: gap_exploit not yet wired — S7.8 scope (C072)")
```

## TASK 58 — VERIFY SCRUM-199 DESCRIPTION COMPLETENESS
SCRUM-199 must contain tasks 7.4.1-7.4.4:
7.4.1: Gap hypothesis generation from scoring context
7.4.2: Weakness/opportunity matching (demand >= 0.60, competition <= 0.40)
7.4.3: Persistence lineage and confidence scoring (data-driven, no base bonus)
7.4.4: Tests — candidate generation, duplicate handling, sparse inputs, empty outputs
Document in A report: any gaps between Jira spec and B handoff package.

## TASK 59 — REVIEW S7.5 SPEC FOR C069 PREVIEW
```powershell
Get-Content 'C:\Fiverr\Fiverr\PM_Pack
ef\project_plan_discovery\DISCOVERY_ENGINE_ARCHITECTURE.md' | Select-String -Context 0,10 "S7.5|Trend Chase"
```
S7.5 (C069) will need trend data — likely external_signals (Google Trends, Reddit).
Document in A report: "S7.5 Trend Chase will likely require external_signals data.
Consider TierD-2 (ScrapFly) approval before C069 to enable live trend collection."

## TASK 60 — VERIFY ALL 9 NICHES IN B HANDOFF NICHE_VALIDATION_CONFIG
```python
from src.analysis.result_set_validator import NICHE_VALIDATION_CONFIG
niches = sorted(NICHE_VALIDATION_CONFIG.keys())
print(f"9 niches for B handoff:")
for n in niches: print(f"  {n}")
assert len(niches) == 9
```
B handoff must document that generate_gap_exploit_hypotheses() must accept
any of these 9 niches as source_niche_id.

## TASK 61 — VERIFY E HANDOFF: EXPLICIT src/ PROHIBITION
E must understand: if a src/ module needs adding, E records the gap for B.
E NEVER adds src/ changes. E observation report only.
Document in E handoff: "CRITICAL: E commits ONLY CYCLE_068_AGENT_E.md.
If you observe a missing src/ symbol, record it in your report for B — DO NOT add it.
floor-line-NNN filler lines are PROHIBITED. Every line must be substantive."

## TASK 62 — VERIFY C HANDOFF: C RUNS BEFORE F
C handoff must contain in first 20 lines:
"C RUNS AFTER B AND E. C RUNS BEFORE F. DO NOT WAIT FOR AGENT F."
This prevents the historical failure mode where C waited for F unnecessarily.

## TASK 63 — VERIFY D HANDOFF: G1 ATTRIBUTION PROTOCOL
D must enumerate EVERY commit in cycle/068/integration range, not just those in C's report.
D must use: git log --oneline <base_sha>..HEAD to enumerate all commits.
Then: git show --name-only <SHA> for EACH commit individually.
B zone: src/ + tests/ + B report only.
E zone: ONLY E report file.
C zone: ONLY C report file.
F zone: tests/ + F report only.
ANY src/ in E or F commits = ZONE VIOLATION — stop merge.

## TASK 64 — A FINAL REPORT TEMPLATE
A report must include ALL of:
1. 14-track table (2026-06-06 dated, from actual src/ inspection)
2. 5 gap checks: all PASS (demo=0, ext=true, G-A 47/37/33, niches=9, pages=9)
3. Production readiness gates: G-A CLOSED, G-B CLOSED, G-C CLOSED, G-D OPEN
4. Part 5.7 completion: ~61% → ~62% after C068
5. All 6 handoff packages with file paths and function signatures
6. Prompt-sizing table: A≥1000 B≥1200 E≥950 C≥900 F≥1000 D≥1200
7. SCRUM-1030 In Progress, SCRUM-199 In Progress, SCRUM-22 In Progress
8. TierD-1: 12 stashes, TierD-2: ScrapFly SEED x12
9. S7.4 scope clarification: data-driven (not static map), uses keyword_scores
10. Policy v4.3 confirmation: 55 tasks, all floors met

## TASK 65 — VERIFY DISCOVERY CONTRACTS UNCHANGED
```python
from src.discovery.contracts import HypothesisMode, DiscoveryInput, DiscoveryOutput
import dataclasses
for cls in [DiscoveryInput, DiscoveryOutput]:
    fields = [f.name for f in dataclasses.fields(cls)]
    print(f"{cls.__name__}: {fields}")
print(f"HypothesisMode values: {[e.value for e in HypothesisMode]}")
```

## TASK 66 — VERIFY DISCOVERY CANDIDATES AND HYPOTHESIS CONTRACT
```python
from src.discovery.hypothesis import HypothesisContract
import dataclasses
fields = {f.name: f.default for f in dataclasses.fields(HypothesisContract)}
print(f"HypothesisContract fields: {list(fields.keys())}")
```
S7.4 uses: hypothesis_text=gap_keyword, niche_id=source, specificity_score=confidence,
accepted=bool, reason=string. Verify these fields exist.

## TASK 67 — VERIFY hypothesis.py FUNCTION SIGNATURES ARE CONSISTENT
All S7.X functions follow the same call signature pattern:
```python
def generate_adjacent_keyword_hypotheses(source_niche_id, keywords, existing, *, max_hypotheses=10, min_confidence=0.50) -> list
def generate_adjacent_niche_hypotheses(source_niche_id, keywords, existing, *, max_hypotheses=10, min_confidence=0.50) -> list
def generate_gap_exploit_hypotheses(source_niche_id, keyword_scores, existing, *, max_hypotheses=10, min_confidence=0.50, demand_threshold=0.60, competition_threshold=0.40) -> list
```
Document all 3 signatures in A report for consistency verification.

## TASK 68 — WAVE 10 SCORECARD IN A REPORT
A report must include:
| S7.1 | scaffold | SRDI | DONE |
| S7.2 | adjacent keyword | C066 | DONE |
| S7.3 | adjacent niche | C067 | DONE |
| S7.4 | gap opportunity | C068 | IN PROGRESS |
| S7.5-S7.9 | remaining | C069+ | TO DO |

## TASK 69 — RECORD RSV SEED CHAIN STATUS
RSV SEED x12: C057-C068 consecutive SEED cycles. No live ScrapFly data collected.
S7.4 uses keyword_scores parameter — in SEED mode these come from test fixtures.
S7.4 does NOT require live Fiverr data. TierD-2 remains pending.
Record in A report: "TierD-2 (ScrapFly): SEED x12. S7.4 does not require live data.
S7.5 (Trend Chase, C069) may benefit from live external_signals."

## TASK 70 — COMMIT A AND PUSH
After completing Tasks 0-69:
```powershell
Invoke-Exe $git 'add PM_Pack/03_cursor_agent_system/ PM_Pack/07_hydration/ docs/cycle_reports/CYCLE_068_AGENT_A.md'
Invoke-Exe $git 'diff --cached --name-only'  # Only PM_Pack/ and docs/
Invoke-Exe $git 'commit -m "docs(cycle068): Agent A -- S7.4 gap opportunity handoff, SCRUM-1030/199 In Progress"'
Invoke-Exe $git 'push origin cycle/068/integration'
```



## TASK 56 — VERIFY DISCOVERY ENGINE ARCHITECTURE SPEC
Read: `PM_Pack\ref\project_plan\10_discovery\DISCOVERY_ENGINE_ARCHITECTURE.md`
Focus on S7.4 section: gap exploit threshold criteria, confidence formula, budget gate.
Record in A report: spec items matched by B implementation.

## TASK 57 — SURVEY EXISTING DISCOVERY ORCHESTRATOR
```python
import sys; sys.path.insert(0,'C:/Fiverr/Fiverr')
from src.discovery.orchestrator import DiscoveryOrchestrator
import inspect
src = inspect.getsource(DiscoveryOrchestrator)
gap_wired = 'gap_exploit' in src
print(f"gap_exploit in orchestrator: {gap_wired} (False expected — S7.8 scope C072)")
```

## TASK 58 — S7.5 CONTEXT FOR C069 PREVIEW
S7.5 Trend Chase = generate_trend_chase_hypotheses() (C069 scope).
Unlike S7.2-S7.4, S7.5 needs external trend signals (Google Trends, Reddit).
Document: "TierD-2 (ScrapFly) may matter more for S7.5 than S7.4."
Include in A report as C069 planning note.

## TASK 59 — VERIFY SCRUM-199 SOURCE TASKS 7.4.1-7.4.4
Per Jira story SCRUM-199:
7.4.1: Generate gap hypotheses from competitor weakness + scoring context
7.4.2: Filter/dedup by weakness/opportunity matching (demand>=0.60, competition<=0.40)
7.4.3: Lineage, confidence, budget context (data-driven, no base bonus)
7.4.4: Tests — candidate gen, duplicates, sparse inputs, empty outputs
Match against B handoff package. Any spec gap → document as carry-forward.

## TASK 60 — VERIFY ALL 9 NICHE IDS IN B HANDOFF
```python
from src.analysis.result_set_validator import NICHE_VALIDATION_CONFIG
niches = sorted(NICHE_VALIDATION_CONFIG.keys())
print('\n'.join(f'  {n}' for n in niches))
assert len(niches) == 9
```
B must accept any of these 9 as source_niche_id. Document in handoff.

## TASK 61 — EXPLICIT E HANDOFF src/ PROHIBITION
E handoff package must state verbatim:
"HARD RULE: You commit ONLY CYCLE_068_AGENT_E.md.
If a src/ module is missing, record the gap for B — DO NOT add it.
floor-line-NNN filler lines are PROHIBITED. Every line must be substantive."

## TASK 62 — C HANDOFF: FIRST 20 LINES REQUIREMENT
C prompt must start with: "C RUNS AFTER B AND E. C RUNS BEFORE F. DO NOT WAIT FOR F."
Verify this is in the first 20 lines of CYCLE_068_AGENT_C_PROMPT.md.

## TASK 63 — D HANDOFF: G1 PROTOCOL
D must use `git log --oneline <base>..HEAD` for ALL commits.
Then `git show --name-only <SHA>` for each.
Zone: B=src+tests+B.md | E=E.md only | C=C.md | F=tests+F.md.
ANY src/ in E/F = ZONE VIOLATION, stop merge.

## TASK 64 — WAVE 10 PROGRESSION AFTER C068 (A report)
```
| S7.1 | scaffold    | SRDI | DONE |
| S7.2 | adj keyword | C066 | DONE |
| S7.3 | adj niche   | C067 | DONE |
| S7.4 | gap exploit | C068 | IN PROGRESS |
| S7.5-S7.9          | C069+ | TO DO |
```

## TASK 65 — VERIFY CONTRACTS.py UNCHANGED
```python
from src.discovery.contracts import HypothesisMode, DiscoveryInput, DiscoveryOutput
import dataclasses
for cls in [DiscoveryInput, DiscoveryOutput]:
    print(f"{cls.__name__}: {[f.name for f in dataclasses.fields(cls)]}")
print(f"HypothesisMode: {[e.value for e in HypothesisMode]}")
```

## TASK 66 — RECORD TIER-D ITEMS IN A REPORT
TierD-1: 12 stale stashes (user decision pending — confirm list before dropping)
TierD-2: ScrapFly credit budget (SEED x12: C057-C068; S7.4 does NOT require live data)
S7.5 (C069) may benefit from live trend signals — surface to user before C069.

## TASK 67 — VERIFY hypothesis.py FUNCTION SIGNATURES CONSISTENT
All S7.X functions share the same first 3 parameters:
  source_niche_id, keyword_data, existing_hypotheses
S7.4 adds: keyword_scores (dict list), demand_threshold, competition_threshold.
Document in A report as "S7.4 call signature deviates from S7.2/S7.3 signature."

## TASK 68 — PART 5.7 ESTIMATE IN A REPORT (REQUIRED)
A report must include Project Completion box:
```
PROJECT COMPLETION: ~61% (C067, 2026-06-06)
Post-C068 estimate: ~62% (Discovery Track: 25%→30%)
Biggest lever: TierD-2 (ScrapFly) → +7-8% immediately
Next: ~62% after C068 (S7.4 done), ~63% after C069 (S7.5)
```

## TASK 69 — RSV SEED x12 NOTE
RSV SEED chain: C057-C068 = 12 consecutive SEED-band cycles.
S7.4 uses keyword_scores parameter — in CI mode from fixture data.
S7.4 does NOT require live Fiverr data.
Document in A report; surface TierD-2 decision to user.

## TASK 70 — FINAL A AUTHORIZATION STATEMENT
A report must declare:
"CYCLE 068 PROMPTS AUTHORIZED. Policy v4.3: 55 tasks, floors A:1000/B:1200/E:950/C:900/F:1000/D:1200.
14 tracks reviewed. 5 gap checks PASS. SCRUM-1030/199 In Progress. SCRUM-22 In Progress.
Base SHA 19e4ca2. Suite 4675/94.34%. S7.4: data-driven gap detection."


## ADDITIONAL VERIFICATION TASKS — SUPPLEMENTAL PACK

## VERIFY S7.4 COMPLETE SYMBOL CHAIN IMPORTABLE
```python
import sys; sys.path.insert(0,'C:/Fiverr/Fiverr')
from src.discovery.hypothesis import (
    HypothesisContract, generate_niche_hypotheses,
    generate_adjacent_keyword_hypotheses, generate_adjacent_niche_hypotheses,
    generate_gap_exploit_hypotheses, _identify_gap_keywords,
    _score_gap_hypothesis_confidence, GAP_DEMAND_THRESHOLD,
    GAP_COMPETITION_THRESHOLD, GAP_DEMAND_WEIGHT, GAP_OPPORTUNITY_WEIGHT,
    ADJACENT_NICHE_RELATIONSHIPS, _WEIGHTS, GATE1_SPECIFICITY_THRESHOLD)
from src.discovery.contracts import HypothesisMode
assert HypothesisMode.GAP_EXPLOIT.value == 'gap_exploit'
assert GAP_DEMAND_THRESHOLD == 0.60
assert GAP_COMPETITION_THRESHOLD == 0.40
assert abs(GAP_DEMAND_WEIGHT + GAP_OPPORTUNITY_WEIGHT - 1.0) < 0.001
print("PASS: complete S7.4 symbol chain importable on develop HEAD")
```

## VERIFY BASELINE INTEGRITY (final check)
```python
import os
mtime = os.path.getmtime('data/cycle037_live.db')
assert abs(mtime - 1780553758) < 10, f"baseline disturbed: {mtime}"
print(f"PASS: data/cycle037_live.db mtime={mtime:.0f} UNTOUCHED")
```

## VERIFY FULL SUITE PASSES (final)
```powershell
C:\Users\kevin\AppData\Local\Programs\Python\Python311\python.exe -m pytest -q `
    --cov=src --cov-fail-under=90 --no-header tests/unit/ | Select-Object -Last 5
```

## VERIFY SCRAPFLY OFF (final)
```python
import yaml
cfg = yaml.safe_load(open('config.yaml'))
assert not cfg.get('collection',{}).get('scrapfly',{}).get('enabled')
print("PASS: scrapfly.enabled=false on develop HEAD post-merge")
```

## COMPLETE NICHE COVERAGE CHECK
```python
from src.analysis.result_set_validator import NICHE_VALIDATION_CONFIG
from src.discovery.hypothesis import generate_gap_exploit_hypotheses
scores = [{'keyword': 'gap test keyword', 'demand_score': 0.75,
           'competition_score': 0.25, 'opportunity_score': 0.80}]
for niche in sorted(NICHE_VALIDATION_CONFIG.keys()):
    results = generate_gap_exploit_hypotheses(niche, scores, [])
    assert isinstance(results, list)
    print(f"PASS: {niche} returns list ({len(results)} results)")
print("PASS: all 9 niches generate valid S7.4 results")
```

## POLICY v4.3 CONFIRMATION IN REPORT
This report confirms policy v4.3 compliance:
- 55 LARGE-XXLARGE tasks minimum per agent (effective C067+)
- Line floors: A:1000 | B:1200 | E:950 | C:900 | F:1000 | D:1200 | TOTAL:6,250
- XXXLARGE retired: decompose into 2-3 XXLARGE with individual acceptance criteria
- No filler lines ("floor-line-NNN: retained" is PROHIBITED)
- Every line in every prompt must be substantive content

## TIER-D ITEMS SUMMARY
TierD-1: 12 stale stashes — pending user confirmation before drop
TierD-2: ScrapFly credit budget — RSV SEED x12 (C057-C068)
  S7.4 does NOT require live ScrapFly data
  S7.5 Trend Chase (C069) MAY benefit from live trend signals
  Recommend user decision before C069 begins

## WAVE 10 PATH TO COMPLETION
4 stories done (44%). Remaining 5 stories:
S7.5 (C069): trend chase — needs trend signal data
S7.6 (C070): discovery scoring and feedback loop
S7.7 (C071): keyword promotion and integration
S7.8 (C072): Stage 16 orchestration wiring
S7.9 (C072+): discovery dashboard widgets
Estimated cycles to Wave 10 completion: ~5 more cycles (C069-C073)

## S7.4 DESIGN SUMMARY FOR D REPORT
S7.4 Gap Opportunity Hypothesis Mode:
- Input: keyword_scores list with demand_score, competition_score, opportunity_score per keyword
- Gap criteria: demand_score >= 0.60 AND competition_score <= 0.40 (both inclusive)
- Confidence: 0.60 × demand_score + 0.40 × opportunity_score (no base bonus)
- Budget gate: min_confidence >= 0.50 (default)
- Output: list[HypothesisContract] with hypothesis_text=keyword, niche_id=source
- Unlike S7.2/S7.3 (static maps): S7.4 is data-driven from scoring pipeline
- No new DB tables. No new migrations. No LLM required.
- Audit trail: includes both accepted and rejected hypotheses

## CONTEXT FOR SQUASH COMMIT MESSAGE
Squash commit subject for PR:
"feat(discovery): C068 Wave 10 S7.4 -- gap opportunity hypothesis mode (#N)"
Body:
- Implements generate_gap_exploit_hypotheses() in src/discovery/hypothesis.py
- Data-driven gap detection: demand >= 0.60 AND competition <= 0.40
- Confidence: 0.60*demand + 0.40*opportunity (no static map, no base bonus)
- HypothesisMode.GAP_EXPLOIT = 'gap_exploit' added to contracts
- Tests: test_gap_exploit_hypotheses.py (>= 30 tests)
- Wave 10: 4/9 stories complete after this merge


## FINAL GOVERNANCE COMMIT INSTRUCTIONS
After all 6 agents complete their work and D squash-merges PR:
```powershell
# SHA_RESOLVER_068.ps1 — run after D's squash merge
$sha = (Invoke-Exe $git 'log origin/develop --oneline -1').Out.Split()[0]
$base = 'C:\Fiverr\Fiverr\PM_Pack\03_cursor_agent_system\'
Get-ChildItem $base -Filter 'CYCLE_068*.md' | ForEach-Object {
    $c = Get-Content $_.FullName -Raw
    Set-Content $_.FullName ($c -replace '\[C068_SQUASH_SHA\]', $sha) }
Select-String '\[C068_SQUASH_SHA\]' ($base + 'CYCLE_068*.md') 2>$null
```
Zero matches = all 6 prompts resolved. Record squash SHA in hydration header.

END OF PROMPT
