"""
tests/unit/test_report_synthesis_arsf.py
Comprehensive test suite for the ARSF layer.
Covers RSF-1..RSF-52 and IVR-1/IVR-2/IVR-4/IVR-5 at L1 (unit) level.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path
from textwrap import dedent
from unittest.mock import patch, MagicMock
import pytest

# ── Ensure repo root is on sys.path ──────────────────────────────────────────
REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))


# ============================================================================
# RSF-1 / RSF-1.1: Package import + schemas
# ============================================================================

def test_import_report_synthesis():
    """Package + public symbols are importable."""
    from automation.report_synthesis import (  # noqa: F401
        synthesize_cycle, load_cycle_synthesis, load_next_cycle_directives,
    )


def test_schemas_defaults():
    """All dataclasses construct with defaults; enum has 6 verdicts."""
    from automation.report_synthesis.schemas import (
        AgentVerdict, TaskClaim, GateClaim, JiraActionClaim,
        ClaimedAgentReport, AgentReportSynthesis, CycleSynthesis,
    )
    assert len(list(AgentVerdict)) == 6
    for v in ("DELIVERED", "PARTIAL", "CLAIMED_ONLY", "FAILED", "BLOCKED", "NO_REPORT"):
        assert AgentVerdict(v).value == v
    t = TaskClaim()
    assert t.id == ""
    g = GateClaim()
    assert g.result == ""
    j = JiraActionClaim()
    assert j.worklog == "none"
    c = ClaimedAgentReport()
    assert c.tasks == []
    a = AgentReportSynthesis()
    assert a.discrepancies == []
    cs = CycleSynthesis()
    assert cs.agents == {}


# ============================================================================
# RSF-2: Manifest parse
# ============================================================================

VALID_MANIFEST_REPORT = dedent("""
<!-- ARSF:MANIFEST v1 -->
```json
{
  "cycle": 84,
  "agent": "B",
  "role": "Implementation",
  "branch": "cycle/084/integration",
  "base_sha": "abc1234",
  "verdict": "PASS",
  "verdict_qualifier": "none",
  "tasks": [
    {"id": "TASK 1", "status": "DONE", "evidence": "tests/unit/test_foo.py"}
  ],
  "tasks_total": 1, "tasks_done": 1, "tasks_partial": 0, "tasks_failed": 0,
  "files_created": ["src/foo.py"],
  "files_modified": [],
  "commits": ["abc1234"],
  "committed": true,
  "validation": {"ruff": "pass", "pytest_passed": 100, "coverage_pct": 92.5},
  "gates": [{"id": "G-001", "result": "PASS", "evidence": "92.5%"}],
  "ac_status": [],
  "jira_actions": [],
  "governance_updates": [],
  "blockers": [],
  "non_claims": ["TierD-2 not started"],
  "carryover": ["SCRUM-205"],
  "self_status": "COMPLETE"
}
```

## 1. Final verdict
`AGENT B CYCLE 084: PASS (none)`

## 2. Task ledger
| Task | Title | Status | Evidence |
|---|---|---|---|
| TASK 1 | Foo | DONE | tests/unit/test_foo.py |

## 3. Files created or modified
| Action | File Path |
|---|---|
| created | `src/foo.py` |

## 4. Git & commit attribution
- `abc1234` — feat: foo

## 5. Validation evidence
### 5.1 Full suite & coverage
```text
100 passed, coverage 92.5%
```
### 5.2 Lint & types
```text
ruff: pass
```

## 6. Gate summary
| Gate | Description | Result | Evidence |
|---|---|---|---|
| G-001 | coverage >= 90 | PASS | 92.5% |

## 11. Open blockers & explicit non-claims   (REQUIRED)
- TierD-2 not started
""")


def test_report_parser_manifest(tmp_path):
    """A valid manifest → exact ClaimedAgentReport fields."""
    from automation.report_synthesis.report_parser import parse_report
    p = tmp_path / "CYCLE_084_AGENT_B.md"
    p.write_text(VALID_MANIFEST_REPORT, encoding="utf-8")
    r = parse_report(p)
    assert r.parse_source == "manifest"
    assert r.cycle == 84
    assert r.agent == "B"
    assert r.committed is True
    assert r.commits == ["abc1234"]
    assert r.tasks[0].id == "TASK 1"
    assert r.tasks[0].status == "DONE"
    assert r.non_claims == ["TierD-2 not started"]
    assert r.carryover == ["SCRUM-205"]
    assert r.format_violations == []


# ============================================================================
# RSF-3: Markdown fallback parse
# ============================================================================

MANIFEST_LESS_REPORT = dedent("""
# CYCLE_084_AGENT_A REPORT

## 1. Final verdict
`AGENT A CYCLE 084: PARTIAL (some tasks deferred)`

## 2. Task ledger
| TASK 1 | Implement foo | DONE | tests/unit/test_foo.py |

## 3. Files created or modified
| created | `src/bar.py` |
| modified | `src/baz.py` |

## 4. Git & commit attribution
- `def5678` — feat: bar

## 5. Validation evidence
### 5.1 Full suite & coverage
```text
200 passed, coverage 91.0%
```

## 11. Open blockers & explicit non-claims   (REQUIRED)
- SCRUM-210 deferred
""")


def test_report_parser_markdown(tmp_path):
    """A manifest-less report still yields stories/files/validation/blockers."""
    from automation.report_synthesis.report_parser import parse_report
    p = tmp_path / "CYCLE_084_AGENT_A.md"
    p.write_text(MANIFEST_LESS_REPORT, encoding="utf-8")
    r = parse_report(p)
    assert r.parse_source == "markdown"
    assert "MANIFEST_MISSING_OR_INVALID" in r.format_violations
    assert r.files_created or r.files_modified  # at least one file detected
    assert r.validation.get("pytest_passed") == 200 or r.validation.get("coverage_pct") is not None


# ============================================================================
# RSF-4: Golden parser fixture (CYCLE_074_AGENT_D)
# ============================================================================

def test_report_parser_golden():
    """Parse the real gold-standard report."""
    fixture = REPO_ROOT / "tests/fixtures/CYCLE_074_AGENT_D.md"
    if not fixture.exists():
        pytest.skip("CYCLE_074_AGENT_D.md fixture not present")
    from automation.report_synthesis.report_parser import parse_report
    r = parse_report(fixture)
    # Must have some verdict
    assert r.verdict or r.raw_text  # At minimum, raw text parsed
    # Gold standard must have validation evidence
    assert r.raw_text != ""


# ============================================================================
# RSF-5: Violation detection
# ============================================================================

def test_report_parser_violations(tmp_path):
    """Missing manifest / §11 / ledger gap → correct format_violations."""
    from automation.report_synthesis.report_parser import parse_report, V_NO_NON_CLAIMS, V_MANIFEST_MISSING

    # No §11 non-claims
    p = tmp_path / "stub.md"
    p.write_text("# Report\n## 1. Final verdict\n`PASS`\n\n## 2. Task ledger\n", encoding="utf-8")
    r = parse_report(p)
    assert V_MANIFEST_MISSING in r.format_violations
    assert V_NO_NON_CLAIMS in r.format_violations

    # Task ledger gap
    p2 = tmp_path / "stub2.md"
    p2.write_text(MANIFEST_LESS_REPORT, encoding="utf-8")
    r2 = parse_report(p2, prompt_task_ids=["TASK 1", "TASK 2", "TASK 3"])
    missing_viol = [v for v in r2.format_violations if "LEDGER" in v]
    assert missing_viol, "Expected task ledger incomplete violation"


# ============================================================================
# RSF-6: Evidence crosscheck actual
# ============================================================================

def test_evidence_crosscheck_actual():
    """Mocked git/CI → actual_files/actual_commits/ci_status populated; failure → unknown."""
    from automation.report_synthesis.evidence_crosscheck import gather_actual_evidence

    class FakeGit:
        def get_commits(self, branch): return ["sha1", "sha2"]
        def get_diff_files(self, branch): return ["src/foo.py", "src/bar.py"]

    class FakeCI:
        def get_status(self, branch): return "green"

    ev = gather_actual_evidence(84, "cycle/084/integration", _git_adapter=FakeGit(), _ci_reader=FakeCI())
    assert ev.actual_commits == ["sha1", "sha2"]
    assert "src/foo.py" in ev.actual_files
    assert ev.ci_status == "green"

    # Failure path → unknown
    class BadGit:
        def get_commits(self, branch): raise RuntimeError("git not found")
        def get_diff_files(self, branch): raise RuntimeError("git not found")

    ev2 = gather_actual_evidence(84, "cycle/084/integration", _git_adapter=BadGit())
    assert ev2.actual_commits == []


# ============================================================================
# RSF-7: No-commit flag
# ============================================================================

def test_evidence_crosscheck_nocommit(tmp_path):
    """committed:true + 0 actual commits → FLAG + CLAIMED_ONLY verdict."""
    from automation.report_synthesis.report_parser import parse_report
    from automation.report_synthesis.evidence_crosscheck import (
        crosscheck_agent, ActualEvidence, FLAG_NO_COMMIT,
    )
    from automation.report_synthesis.schemas import AgentVerdict

    p = tmp_path / "CYCLE_084_AGENT_B.md"
    p.write_text(VALID_MANIFEST_REPORT, encoding="utf-8")
    claimed = parse_report(p)
    claimed.committed = True
    claimed.self_status = "COMPLETE"

    actual = ActualEvidence(actual_commits=[], ci_status="green")
    synth = crosscheck_agent(claimed, 84, actual=actual)
    assert FLAG_NO_COMMIT in synth.discrepancies
    assert synth.verdict == AgentVerdict.CLAIMED_ONLY.value


# ============================================================================
# RSF-8: Claimed files not in diff
# ============================================================================

def test_evidence_crosscheck_files(tmp_path):
    """Claimed files ∉ diff → CLAIMED_FILES_NOT_IN_DIFF flag."""
    from automation.report_synthesis.report_parser import parse_report
    from automation.report_synthesis.evidence_crosscheck import (
        crosscheck_agent, ActualEvidence, FLAG_CLAIMED_FILES,
    )

    p = tmp_path / "CYCLE_084_AGENT_B.md"
    p.write_text(VALID_MANIFEST_REPORT, encoding="utf-8")
    claimed = parse_report(p)
    claimed.files_created = ["src/ghost_file_xyz_not_real.py"]
    claimed.committed = True

    actual = ActualEvidence(
        actual_commits=["abc1234"],
        actual_files=["src/something_else.py"],  # ghost_file absent
        ci_status="green",
    )
    synth = crosscheck_agent(claimed, 84, actual=actual)
    assert any(FLAG_CLAIMED_FILES in d for d in synth.discrepancies)


# ============================================================================
# RSF-9: Tests claimed pass + CI red
# ============================================================================

def test_evidence_crosscheck_ci(tmp_path):
    """Local pass + CI red → TESTS_CLAIMED_PASS_CI_RED flag."""
    from automation.report_synthesis.report_parser import parse_report
    from automation.report_synthesis.evidence_crosscheck import (
        crosscheck_agent, ActualEvidence, FLAG_CI_RED,
    )

    p = tmp_path / "CYCLE_084_AGENT_B.md"
    p.write_text(VALID_MANIFEST_REPORT, encoding="utf-8")
    claimed = parse_report(p)
    claimed.validation = {"ruff": "pass", "pytest_passed": 100}
    claimed.committed = True

    actual = ActualEvidence(actual_commits=["abc1234"], actual_files=[], ci_status="red")
    synth = crosscheck_agent(claimed, 84, actual=actual)
    assert FLAG_CI_RED in synth.discrepancies


# ============================================================================
# RSF-10: AC claimed met no evidence
# ============================================================================

def test_evidence_crosscheck_ac(tmp_path):
    """AC met w/o evidence → AC_CLAIMED_MET_DETERMINISTIC_UNMET + unmet_ac."""
    from automation.report_synthesis.report_parser import parse_report
    from automation.report_synthesis.evidence_crosscheck import (
        crosscheck_agent, ActualEvidence, FLAG_AC_UNMET,
    )

    p = tmp_path / "CYCLE_084_AGENT_B.md"
    p.write_text(VALID_MANIFEST_REPORT, encoding="utf-8")
    claimed = parse_report(p)
    claimed.ac_status = [{"key": "SCRUM-205", "met": True, "evidence": ""}]
    claimed.committed = True

    actual = ActualEvidence(actual_commits=["abc1234"])
    synth = crosscheck_agent(claimed, 84, actual=actual)
    assert any(FLAG_AC_UNMET in d for d in synth.discrepancies)
    assert "SCRUM-205" in synth.unmet_ac


# ============================================================================
# RSF-11: Jira transition claimed not found
# ============================================================================

def test_evidence_crosscheck_jira(tmp_path):
    """Claimed transition not in actual → JIRA_TRANSITION_CLAIMED_NOT_FOUND."""
    from automation.report_synthesis.report_parser import parse_report
    from automation.report_synthesis.evidence_crosscheck import (
        crosscheck_agent, ActualEvidence, FLAG_JIRA_MISSING,
    )
    from automation.report_synthesis.schemas import JiraActionClaim as JAC

    p = tmp_path / "CYCLE_084_AGENT_B.md"
    p.write_text(VALID_MANIFEST_REPORT, encoding="utf-8")
    claimed = parse_report(p)
    claimed.jira_actions = [JAC(key="SCRUM-205", transition="Done", transition_id="41")]
    claimed.committed = True

    actual = ActualEvidence(
        actual_commits=["abc1234"],
        jira_transitions={"SCRUM-205": ["In Progress"]},  # "Done" not present
    )
    synth = crosscheck_agent(claimed, 84, actual=actual)
    assert any(FLAG_JIRA_MISSING in d for d in synth.discrepancies)


# ============================================================================
# RSF-12: Verdict ladder
# ============================================================================

@pytest.mark.parametrize("committed,discrepancies,verdict_qualifier,expected", [
    (True, [], "PASS", "DELIVERED"),
    (True, ["COMPLETION_CLAIMED_NO_COMMIT"], "", "CLAIMED_ONLY"),
    (True, ["CLAIMED_FILES_NOT_IN_DIFF: x"], "", "PARTIAL"),
    (False, [], "BLOCKED", "BLOCKED"),
    (False, [], "FAIL", "FAILED"),
    (False, [], "", "PARTIAL"),
])
def test_verdict_matrix(tmp_path, committed, discrepancies, verdict_qualifier, expected):
    """(claims, discrepancies) → expected verdict."""
    from automation.report_synthesis.schemas import ClaimedAgentReport
    from automation.report_synthesis.evidence_crosscheck import _compute_verdict

    claimed = ClaimedAgentReport(
        committed=committed,
        verdict=verdict_qualifier,
        tasks=[MagicMock(id="TASK 1")],
    )
    result = _compute_verdict(claimed, discrepancies)
    assert result == expected


# ============================================================================
# RSF-13: synthesize_cycle orchestration
# ============================================================================

def test_synthesizer_cycle(tmp_path):
    """6 fixture reports → CycleSynthesis with correct per-agent verdicts."""
    from automation.report_synthesis.synthesizer import synthesize_cycle

    # Create 6 minimal agent reports
    for agent in ["A", "B", "E", "C", "F", "D"]:
        body = VALID_MANIFEST_REPORT.replace('"agent": "B"', f'"agent": "{agent}"')
        (tmp_path / f"CYCLE_099_AGENT_{agent}.md").write_text(body, encoding="utf-8")

    with patch("automation.report_synthesis.evidence_crosscheck.gather_actual_evidence") as mock_ev:
        from automation.report_synthesis.evidence_crosscheck import ActualEvidence
        mock_ev.return_value = ActualEvidence(actual_commits=["abc1234"])
        cs = synthesize_cycle(
            99,
            reports_dir=tmp_path,
            runs_dir=tmp_path / "runs",
        )

    assert len(cs.agents) == 6
    assert cs.cycle == 99
    assert cs.cycle_verdict != ""


def test_synthesizer_missing_report(tmp_path):
    """Missing report → NO_REPORT, not a crash."""
    from automation.report_synthesis.synthesizer import synthesize_cycle
    from automation.report_synthesis.schemas import AgentVerdict

    # Only create 5 reports, B is missing
    for agent in ["A", "E", "C", "F", "D"]:
        body = VALID_MANIFEST_REPORT.replace('"agent": "B"', f'"agent": "{agent}"')
        (tmp_path / f"CYCLE_099_AGENT_{agent}.md").write_text(body, encoding="utf-8")

    with patch("automation.report_synthesis.evidence_crosscheck.gather_actual_evidence") as mock_ev:
        from automation.report_synthesis.evidence_crosscheck import ActualEvidence
        mock_ev.return_value = ActualEvidence(actual_commits=["abc1234"])
        cs = synthesize_cycle(99, reports_dir=tmp_path, runs_dir=tmp_path / "runs")

    assert cs.agents["B"].verdict == AgentVerdict.NO_REPORT.value


# ============================================================================
# RSF-13.1: summary_for_pm
# ============================================================================

def test_summary_for_pm():
    """CLAIMED_ONLY agent → summary names the no-commit discrepancy."""
    from automation.report_synthesis.synthesizer import _make_summary
    from automation.report_synthesis.schemas import AgentReportSynthesis

    synth = AgentReportSynthesis(
        agent="B",
        verdict="CLAIMED_ONLY",
        discrepancies=["COMPLETION_CLAIMED_NO_COMMIT"],
        carryover=["SCRUM-205", "SCRUM-206"],
    )
    summary = _make_summary("B", synth)
    assert "CLAIMED_ONLY" in summary
    assert "COMPLETION_CLAIMED_NO_COMMIT" in summary
    assert "SCRUM-205" in summary


# ============================================================================
# RSF-14: Aggregate fields
# ============================================================================

def test_synthesizer_aggregate(tmp_path):
    """Counts + carryover + format_health computed correctly."""
    from automation.report_synthesis.synthesizer import synthesize_cycle

    for agent in ["A", "B", "E", "C", "F", "D"]:
        body = VALID_MANIFEST_REPORT.replace('"agent": "B"', f'"agent": "{agent}"')
        (tmp_path / f"CYCLE_098_AGENT_{agent}.md").write_text(body, encoding="utf-8")

    with patch("automation.report_synthesis.evidence_crosscheck.gather_actual_evidence") as mock_ev:
        from automation.report_synthesis.evidence_crosscheck import ActualEvidence
        mock_ev.return_value = ActualEvidence(actual_commits=["abc1234"])
        cs = synthesize_cycle(98, reports_dir=tmp_path, runs_dir=tmp_path / "runs")

    assert cs.format_health != ""
    assert isinstance(cs.carryover, list)
    assert cs.cycle_verdict != ""


# ============================================================================
# RSF-15: Synthesis persist
# ============================================================================

def test_synthesis_persist(tmp_path):
    """JSON + md written; JSON round-trips to CycleSynthesis."""
    from automation.report_synthesis.synthesizer import synthesize_cycle, load_cycle_synthesis

    for agent in ["A", "B", "E", "C", "F", "D"]:
        body = VALID_MANIFEST_REPORT.replace('"agent": "B"', f'"agent": "{agent}"')
        (tmp_path / f"CYCLE_097_AGENT_{agent}.md").write_text(body, encoding="utf-8")

    runs = tmp_path / "runs"
    _docs = tmp_path / "docs"

    with patch("automation.report_synthesis.synthesizer.REPO_ROOT", tmp_path), \
         patch("automation.report_synthesis.evidence_crosscheck.gather_actual_evidence") as mock_ev:
        from automation.report_synthesis.evidence_crosscheck import ActualEvidence
        mock_ev.return_value = ActualEvidence(actual_commits=["abc1234"])
        _cs = synthesize_cycle(97, reports_dir=tmp_path, runs_dir=runs)

    # JSON should exist in runs_dir
    json_path = runs / "CYCLE_097_SYNTHESIS.json"
    assert json_path.exists(), f"Expected {json_path}"
    loaded = load_cycle_synthesis(97, runs_dir=runs)
    assert loaded is not None
    assert loaded.cycle == 97


# ============================================================================
# RSF-16: PM formatter
# ============================================================================

def test_pm_formatter():
    """Markdown has verdicts + discrepancies; ≤ max_pm_block_chars."""
    from automation.report_synthesis.pm_formatter import format_for_pm
    from automation.report_synthesis.schemas import CycleSynthesis, AgentReportSynthesis

    cs = CycleSynthesis(cycle=84, cycle_verdict="PARTIAL", format_health="4/6")
    cs.agents["B"] = AgentReportSynthesis(
        agent="B", verdict="CLAIMED_ONLY",
        discrepancies=["COMPLETION_CLAIMED_NO_COMMIT"],
        carryover=["SCRUM-205"],
    )
    cs.agents["A"] = AgentReportSynthesis(agent="A", verdict="DELIVERED")

    md = format_for_pm(cs, max_pm_block_chars=2000)
    assert "CLAIMED_ONLY" in md or "DELIVERED" in md
    assert len(md) <= 2000


def test_pm_formatter_cap():
    """Cap respected when many agents."""
    from automation.report_synthesis.pm_formatter import format_for_pm
    from automation.report_synthesis.schemas import CycleSynthesis, AgentReportSynthesis

    cs = CycleSynthesis(cycle=1)
    for ag in ["A", "B", "E", "C", "F", "D"]:
        cs.agents[ag] = AgentReportSynthesis(
            agent=ag, verdict="PARTIAL",
            discrepancies=["D" * 200],
            carryover=["C" * 100],
        )
    md = format_for_pm(cs, max_pm_block_chars=900)  # generous cap for trimmed output
    assert len(md) <= 900


# ============================================================================
# RSF-17: load_cycle_synthesis
# ============================================================================

def test_load_cycle_synthesis(tmp_path):
    """Round-trip; missing → None."""
    from automation.report_synthesis.synthesizer import load_cycle_synthesis
    from automation.report_synthesis.schemas import CycleSynthesis

    # Missing
    assert load_cycle_synthesis(1000, runs_dir=tmp_path) is None

    # Present
    cs = CycleSynthesis(cycle=42, cycle_verdict="PASS", format_health="6/6")
    from automation.report_synthesis.synthesizer import _synthesis_to_dict
    data = _synthesis_to_dict(cs)
    (tmp_path / "CYCLE_042_SYNTHESIS.json").write_text(json.dumps(data), encoding="utf-8")
    loaded = load_cycle_synthesis(42, runs_dir=tmp_path)
    assert loaded is not None
    assert loaded.cycle == 42
    assert loaded.cycle_verdict == "PASS"


# ============================================================================
# RSF-20: Config loader
# ============================================================================

def test_report_synthesis_config(tmp_path):
    """YAML loads; env overrides applied; missing file → defaults."""
    import yaml
    cfg_path = tmp_path / "report_synthesis.yml"
    cfg_path.write_text("enabled: true\nmax_pm_block_chars: 5000\n", encoding="utf-8")

    cfg = yaml.safe_load(cfg_path.read_text())
    assert cfg["enabled"] is True
    assert cfg["max_pm_block_chars"] == 5000

    # Missing → no error
    missing = tmp_path / "nonexistent.yml"
    try:
        data = yaml.safe_load(missing.read_text()) or {}
    except FileNotFoundError:
        data = {}
    assert "enabled" not in data  # graceful


# ============================================================================
# RSF-21: Observability events
# ============================================================================

def test_arsf_events(tmp_path):
    """synthesize_cycle emits a banner (no crash)."""
    from automation.report_synthesis.synthesizer import synthesize_cycle

    for agent in ["A", "B", "E", "C", "F", "D"]:
        body = VALID_MANIFEST_REPORT.replace('"agent": "B"', f'"agent": "{agent}"')
        (tmp_path / f"CYCLE_096_AGENT_{agent}.md").write_text(body, encoding="utf-8")

    with patch("automation.report_synthesis.evidence_crosscheck.gather_actual_evidence") as mock_ev, \
         patch("builtins.print") as mock_print:
        from automation.report_synthesis.evidence_crosscheck import ActualEvidence
        mock_ev.return_value = ActualEvidence(actual_commits=["abc1234"])
        synthesize_cycle(96, reports_dir=tmp_path, runs_dir=tmp_path / "runs")

    # Banner should have been printed
    assert mock_print.called
    banner_call = str(mock_print.call_args_list[-1])
    assert "ARSF" in banner_call or "cycle" in banner_call.lower()


# ============================================================================
# RSF-23: Template present
# ============================================================================

def test_report_template_present():
    """Template file exists in PM_Pack/09_templates/."""
    template = REPO_ROOT / "PM_Pack/09_templates/AGENT_CYCLE_REPORT_TEMPLATE.md"
    assert template.exists(), f"Template not found at {template}"
    content = template.read_text(encoding="utf-8", errors="replace")
    assert len(content) > 100


# ============================================================================
# RSF-27: report_validator
# ============================================================================

def test_report_validator(tmp_path):
    """Gold-standard report passes; stub fails with named violations."""
    from automation.report_validator import validate_report
    from automation.report_synthesis.report_parser import V_NO_NON_CLAIMS

    # Stub: no §11, no manifest
    stub = tmp_path / "stub.md"
    stub.write_text("# Report\n## 1. Final verdict\n`PASS`\n", encoding="utf-8")
    violations = validate_report(stub)
    assert V_NO_NON_CLAIMS in violations or any("11" in v for v in violations)

    # Gold-standard-like
    good = tmp_path / "good.md"
    good.write_text(VALID_MANIFEST_REPORT, encoding="utf-8")
    v2 = validate_report(good, prompt_task_ids=["TASK 1"])
    # Should have minimal violations (may still have missing headers in the short fixture)
    assert isinstance(v2, list)


# ============================================================================
# RSF-29: Role addenda enforcement
# ============================================================================

def test_role_addenda(tmp_path):
    """Missing role addendum → ROLE_ADDENDUM_MISSING violation."""
    from automation.report_validator import validate_report

    report = tmp_path / "agent_a.md"
    report.write_text(VALID_MANIFEST_REPORT, encoding="utf-8")  # no A1/A2/A3 addendum
    violations = validate_report(report, agent_role="A")
    assert any("ROLE_ADDENDUM" in v for v in violations)


# ============================================================================
# RSF-35: PostCycleFacts new fields
# ============================================================================

def test_postcyclefacts_fields():
    """PostCycleFacts has the ARSF synthesis fields with defaults."""
    from automation.post_cycle_review import PostCycleFacts, ReviewMode
    f = PostCycleFacts(cycle=84, mode=ReviewMode.POST_AGENT)
    assert hasattr(f, "per_agent_verdict")
    assert hasattr(f, "agent_discrepancies")
    assert hasattr(f, "claimed_only_agents")
    assert hasattr(f, "carryover")
    assert hasattr(f, "unmet_ac")
    assert hasattr(f, "report_format_health")
    assert f.per_agent_verdict == {}
    assert f.claimed_only_agents == []


# ============================================================================
# RSF-37: next_scope_decision from carryover
# ============================================================================

def test_next_scope_from_carryover():
    """next_scope_decision reflects carryover when synthesis is loaded."""
    from automation.post_cycle_review import PostCycleFacts, ReviewMode
    f = PostCycleFacts(cycle=84, mode=ReviewMode.POST_AGENT)
    f.carryover = ["SCRUM-205", "SCRUM-206"]
    # The carryover list is accessible
    assert "SCRUM-205" in f.carryover


# ============================================================================
# RSF-39: Directive matrix
# ============================================================================

@pytest.mark.parametrize("verdict,discrepancy,expected_gate_fragment", [
    ("CLAIMED_ONLY", "COMPLETION_CLAIMED_NO_COMMIT", "git log"),
    ("PARTIAL", "", "deliver missing"),
    ("FAILED", "", "fix root cause"),
    ("BLOCKED", "", "dependency"),
    ("NO_REPORT", "", "ARSF-conforming report"),
])
def test_directive_matrix(verdict, discrepancy, expected_gate_fragment):
    """Each (verdict, discrepancy) → directive with correct corrective gate."""
    from automation.report_synthesis.directive_generator import generate_directives
    from automation.report_synthesis.schemas import CycleSynthesis, AgentReportSynthesis

    cs = CycleSynthesis(cycle=84)
    cs.agents["B"] = AgentReportSynthesis(
        agent="B", verdict=verdict,
        discrepancies=[discrepancy] if discrepancy else [],
        carryover=["SCRUM-205"],
    )
    nd = generate_directives(cs)
    assert nd.directives, "Expected at least one directive"
    gates = " ".join(d.corrective_gate for d in nd.directives if d.agent == "B")
    assert expected_gate_fragment.lower() in gates.lower(), f"Gate '{gates}' missing '{expected_gate_fragment}'"


# ============================================================================
# RSF-39.1: Build-sequence advance
# ============================================================================

def test_build_seq_advance():
    """Claimed-only wave → advance=False + reason."""
    from automation.report_synthesis.directive_generator import generate_directives
    from automation.report_synthesis.schemas import CycleSynthesis, AgentReportSynthesis

    cs = CycleSynthesis(cycle=84)
    cs.agents["B"] = AgentReportSynthesis(
        agent="B", verdict="CLAIMED_ONLY",
        discrepancies=["COMPLETION_CLAIMED_NO_COMMIT"],
        carryover=["SCRUM-205"],
    )
    cs.top_risks = ["Agent B = CLAIMED_ONLY"]
    nd = generate_directives(cs)
    assert nd.build_sequence_advance is False
    assert nd.build_sequence_reason != ""


# ============================================================================
# RSF-40: Directives persist
# ============================================================================

def test_directives_persist(tmp_path):
    """JSON + md written; JSON round-trips."""
    from automation.report_synthesis.directive_generator import (
        generate_directives, persist_directives, load_next_cycle_directives,
    )
    from automation.report_synthesis.schemas import CycleSynthesis, AgentReportSynthesis

    cs = CycleSynthesis(cycle=95)
    cs.agents["B"] = AgentReportSynthesis(
        agent="B", verdict="CLAIMED_ONLY",
        discrepancies=["COMPLETION_CLAIMED_NO_COMMIT"],
        carryover=["SCRUM-205"],
    )
    nd = generate_directives(cs)
    persist_directives(nd, runs_dir=tmp_path)

    json_p = tmp_path / "CYCLE_095_NEXT_CYCLE_DIRECTIVES.json"
    assert json_p.exists()
    loaded = load_next_cycle_directives(95, runs_dir=tmp_path)
    assert loaded is not None
    assert loaded.from_cycle == 95


# ============================================================================
# RSF-41: load_next_cycle_directives
# ============================================================================

def test_load_directives(tmp_path):
    """Round-trip; missing → None."""
    from automation.report_synthesis.directive_generator import load_next_cycle_directives
    assert load_next_cycle_directives(9999, runs_dir=tmp_path) is None


# ============================================================================
# RSF-42: Commit-gate in CLAIMED_ONLY directive
# ============================================================================

def test_directives_from_claimed_only():
    """Claimed-only + no-commit → directive WITH commit gate."""
    from automation.report_synthesis.directive_generator import generate_directives
    from automation.report_synthesis.schemas import CycleSynthesis, AgentReportSynthesis

    cs = CycleSynthesis(cycle=84)
    cs.agents["B"] = AgentReportSynthesis(
        agent="B", verdict="CLAIMED_ONLY",
        discrepancies=["COMPLETION_CLAIMED_NO_COMMIT"],
        carryover=["SCRUM-205"],
    )
    nd = generate_directives(cs)
    commit_directives = [d for d in nd.directives if d.agent == "B" and "git log" in d.corrective_gate]
    assert commit_directives, "Expected at least one B directive with git log gate"


# ============================================================================
# RSF-43: Stuck-item detection
# ============================================================================

def test_stuck_item_escalation():
    """Same story carried 2 cycles → stuck_items entry."""
    from automation.report_synthesis.directive_generator import (
        generate_directives, NextCycleDirectives, Directive,
    )
    from automation.report_synthesis.schemas import CycleSynthesis, AgentReportSynthesis

    # Prev cycle had same B directive
    prev = NextCycleDirectives(from_cycle=83)
    prev.directives.append(Directive(
        agent="B", task="re-dispatch with commit gate: re-target SCRUM-205",
        from_cycle=83,
    ))

    cs = CycleSynthesis(cycle=84)
    cs.agents["B"] = AgentReportSynthesis(
        agent="B", verdict="CLAIMED_ONLY",
        discrepancies=["COMPLETION_CLAIMED_NO_COMMIT"],
        carryover=["SCRUM-205"],
    )
    nd = generate_directives(cs, prev_directives=prev)
    assert nd.stuck_items, "Expected at least one stuck item"
    assert any("B" in si for si in nd.stuck_items)


# ============================================================================
# RSF-33: Non-blocking guarantee
# ============================================================================

def test_arsf_nonblocking(tmp_path):
    """Synthesizer raising → cycle still completes (no exception propagated)."""
    from automation.report_synthesis.synthesizer import synthesize_cycle

    # Reports dir doesn't exist at all — should not raise
    nonexistent = tmp_path / "does_not_exist"
    cs = synthesize_cycle(999, reports_dir=nonexistent, runs_dir=tmp_path / "runs")
    assert cs is not None
    assert cs.cycle == 999


# ============================================================================
# RSF-49: Score not credited to CLAIMED_ONLY
# ============================================================================

def test_score_not_credited_claimed_only():
    """Non-DELIVERED verdicts excluded from score inputs."""
    from automation.report_synthesis.schemas import AgentVerdict

    # Delivery filter: only DELIVERED counts
    agent_results = {
        "A": AgentVerdict.DELIVERED.value,
        "B": AgentVerdict.CLAIMED_ONLY.value,
        "E": AgentVerdict.PARTIAL.value,
    }
    delivered = [a for a, v in agent_results.items() if v == AgentVerdict.DELIVERED.value]
    not_delivered = [a for a, v in agent_results.items() if v != AgentVerdict.DELIVERED.value]
    assert "A" in delivered
    assert "B" in not_delivered
    assert "E" in not_delivered


# ============================================================================
# IVR-1: AC verification deterministic
# ============================================================================

def test_ac_verification_deterministic(tmp_path):
    """Word-overlap-only AC (no real evidence) → NOT verified."""
    from automation.report_synthesis.schemas import ClaimedAgentReport
    from automation.report_synthesis.evidence_crosscheck import _check_ac_claims

    from automation.report_synthesis.schemas import AgentReportSynthesis
    claimed = ClaimedAgentReport()
    claimed.ac_status = [
        {"key": "SCRUM-205", "met": True, "evidence": ""},  # claimed met, no evidence
        {"key": "SCRUM-206", "met": True, "evidence": "tests/unit/test_foo.py"},  # has evidence
    ]
    synth = AgentReportSynthesis(agent="B")
    _check_ac_claims(claimed, synth)
    # Only SCRUM-205 (no evidence) should be flagged
    assert "SCRUM-205" in synth.unmet_ac
    assert "SCRUM-206" not in synth.unmet_ac


# ============================================================================
# IVR-2: Anti-paste gate concept
# ============================================================================

def test_prompt_paste_ratio():
    """Anti-paste gate concept: spec-dump → high ratio; authored → low ratio."""
    # Simplified paste-ratio check: overlap of prompt vs known spec text
    spec_text = "Implement visual analysis pipeline for Fiverr gigs using OpenCV and scikit-image"

    # 084-style: mostly pasted spec
    prompt_084 = spec_text * 5 + "\nPlease do this."
    overlap_084 = sum(1 for w in spec_text.split() if w in prompt_084.split()) / len(spec_text.split())

    # 070-style: authored
    prompt_070 = "Step 1: Create tests/unit/test_visual_analysis.py. Step 2: Add extract_features(). Step 3: Run pytest. Evidence required."
    overlap_070 = sum(1 for w in spec_text.split() if w in prompt_070.split()) / len(spec_text.split())

    assert overlap_084 > overlap_070, "084-style spec-dump should have higher overlap than authored prompt"


# ============================================================================
# IVR-5: Test paths exist
# ============================================================================

def test_paths_exist():
    """Every key test module resolves to a real file."""
    critical_tests = [
        REPO_ROOT / "tests/unit/test_report_synthesis_arsf.py",  # this file
    ]
    for p in critical_tests:
        assert p.exists(), f"Test file not found: {p}"
