"""
tests/unit/test_synthesis_critic_2_2.py

Item 2.2 — the agent-report synthesis critic must stop collapsing real
markdown reports to NO_REPORT (0/6).

A real agent report is plain markdown (## Summary, ## Files Created or Modified
with `path (created|modified)` bullets, ## Validation, ## Blockers, …) and
carries NO ARSF:MANIFEST block. Such a report must parse into a populated
ClaimedAgentReport so its verdict is NOT NO_REPORT. A genuinely missing or
empty (title-only) report still yields NO_REPORT. A report that DOES carry a
manifest block is still preferred (parse_source == "manifest").

All writes stay in tmp via reports_dir= / runs_dir= and a monkeypatched
synthesizer.REPO_ROOT, so the live repo docs/cycle_reports and C:/AI_Runner are
never touched (the 0.4 write-guard is active).
"""
from __future__ import annotations

import json
import sys
from pathlib import Path
from textwrap import dedent
from unittest.mock import patch

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))


# ── Realistic fixtures (NO manifest) ─────────────────────────────────────────

REALISTIC_MARKDOWN_REPORT = dedent(
    """
    # CYCLE_120_AGENT_B REPORT

    ## Summary

    Implemented the SCRUM-1088 runtime slice in src/ and tests/ with typed
    stage observation contracts, a domain exception hierarchy, and bounded
    retry logic. Added unit and integration coverage for happy path, empty
    input, schema behavior, and DB failure handling.

    ## Files Created or Modified

    - `C:/Fiverr/Fiverr/src/cycle_story_runtime.py` (created)
    - `C:\\Fiverr\\Fiverr\\src\\cycle_083_automation_runn.py` (modified)
    - `tests/unit/test_cycle_083_automation_runn.py` (modified)

    ## Validation Results

    Command execution was blocked in this session.
    - `python -m ruff check src/ tests/ automation/` -> BLOCKED
    - `python -m pytest tests/ -q` -> BLOCKED

    ## Blockers Encountered

    1. Shell command execution rejected by session tooling.

    AGENT_COMPLETE
    """
)

MANIFEST_REPORT = dedent(
    """
    <!-- ARSF:MANIFEST v1 -->
    ```json
    {
      "cycle": 120,
      "agent": "B",
      "verdict": "PASS",
      "files_created": ["src/foo.py"],
      "files_modified": [],
      "committed": true,
      "tasks": [{"id": "TASK 1", "status": "DONE", "evidence": "x"}],
      "non_claims": [],
      "carryover": []
    }
    ```

    ## Summary
    Did the thing.

    ## Files Created or Modified
    - `src/foo.py` (created)
    """
)


def _write(reports_dir: Path, cycle: int, agent: str, body: str) -> Path:
    p = reports_dir / f"CYCLE_{cycle:03d}_AGENT_{agent}.md"
    p.write_text(body, encoding="utf-8")
    return p


# ── test_markdown_report_parses_not_no_report ────────────────────────────────

def test_markdown_report_parses_not_no_report(tmp_path):
    """A realistic markdown report (no manifest) → populated report, not NO_REPORT."""
    from automation.report_synthesis.report_parser import parse_report
    from automation.report_synthesis.evidence_crosscheck import (
        crosscheck_agent,
        ActualEvidence,
    )
    from automation.report_synthesis.schemas import AgentVerdict

    p = _write(tmp_path, 120, "B", REALISTIC_MARKDOWN_REPORT)
    r = parse_report(p)

    assert r.parse_source == "markdown"
    # 3 claimed files, normalized to repo-relative posix paths.
    claimed = r.files_created + r.files_modified
    assert len(claimed) == 3
    assert "src/cycle_story_runtime.py" in r.files_created
    assert "src/cycle_083_automation_runn.py" in r.files_modified
    assert "tests/unit/test_cycle_083_automation_runn.py" in r.files_modified
    assert r.summary  # populated from ## Summary
    assert not r.is_empty()
    # MANIFEST_MISSING is still recorded (real format gap) but must NOT force NO_REPORT.
    assert any("MANIFEST" in v for v in r.format_violations)

    synth = crosscheck_agent(
        r, 120, actual=ActualEvidence(actual_commits=[], actual_files=[])
    )
    assert synth.verdict != AgentVerdict.NO_REPORT.value


# ── test_missing_report_is_no_report ─────────────────────────────────────────

def test_missing_report_is_no_report(tmp_path):
    """No file at all → NO_REPORT."""
    from automation.report_synthesis.report_parser import parse_report
    from automation.report_synthesis.evidence_crosscheck import (
        crosscheck_agent,
        ActualEvidence,
    )
    from automation.report_synthesis.schemas import AgentVerdict

    r = parse_report(tmp_path / "CYCLE_120_AGENT_Z.md")  # does not exist
    assert r.parse_source == "none"
    assert r.is_empty()
    synth = crosscheck_agent(r, 120, actual=ActualEvidence())
    assert synth.verdict == AgentVerdict.NO_REPORT.value


# ── test_empty_report_is_no_report ───────────────────────────────────────────

def test_empty_report_is_no_report(tmp_path):
    """A file with only a title and no content/files → NO_REPORT."""
    from automation.report_synthesis.report_parser import parse_report
    from automation.report_synthesis.evidence_crosscheck import (
        crosscheck_agent,
        ActualEvidence,
    )
    from automation.report_synthesis.schemas import AgentVerdict

    p = _write(tmp_path, 120, "Y", "# CYCLE_120_AGENT_Y REPORT\n")
    r = parse_report(p)
    assert r.parse_source == "markdown"
    assert not (r.files_created or r.files_modified)
    assert not r.summary.strip()
    assert r.is_empty()
    synth = crosscheck_agent(r, 120, actual=ActualEvidence())
    assert synth.verdict == AgentVerdict.NO_REPORT.value


# ── test_manifest_report_still_preferred ─────────────────────────────────────

def test_manifest_report_still_preferred(tmp_path):
    """A report WITH an ARSF:MANIFEST json block → parse_source == 'manifest'."""
    from automation.report_synthesis.report_parser import parse_report

    p = _write(tmp_path, 120, "A", MANIFEST_REPORT)
    r = parse_report(p)
    assert r.parse_source == "manifest"
    assert r.files_created == ["src/foo.py"]
    assert r.committed is True
    # Manifest present → no MANIFEST_MISSING violation.
    assert not any("MANIFEST" in v for v in r.format_violations)


# ── test_synthesize_cycle_6_of_6 ─────────────────────────────────────────────

def test_synthesize_cycle_6_of_6(tmp_path, monkeypatch):
    """6 realistic markdown reports → 6 agents parsed, none NO_REPORT; JSON persisted."""
    from automation.report_synthesis.synthesizer import synthesize_cycle
    from automation.report_synthesis.schemas import AgentVerdict

    reports_dir = tmp_path / "reports"
    reports_dir.mkdir()
    docs_root = tmp_path / "repo"
    runs_dir = tmp_path / "runs" / "CYCLE_121"

    for agent in ["A", "B", "E", "C", "F", "D"]:
        body = REALISTIC_MARKDOWN_REPORT.replace("AGENT_B", f"AGENT_{agent}")
        _write(reports_dir, 121, agent, body)

    # Redirect synthesizer.REPO_ROOT so the tracked docs/cycle_reports write
    # lands in tmp, not the live repo.
    monkeypatch.setattr(
        "automation.report_synthesis.synthesizer.REPO_ROOT", docs_root, raising=False
    )

    with patch(
        "automation.report_synthesis.evidence_crosscheck.gather_actual_evidence"
    ) as mock_ev:
        from automation.report_synthesis.evidence_crosscheck import ActualEvidence

        mock_ev.return_value = ActualEvidence(actual_commits=[], actual_files=[])
        cs = synthesize_cycle(121, reports_dir=reports_dir, runs_dir=runs_dir)

    assert len(cs.agents) == 6
    no_report = [
        a for a, s in cs.agents.items() if s.verdict == AgentVerdict.NO_REPORT.value
    ]
    assert no_report == [], f"agents collapsed to NO_REPORT: {no_report}"
    # parsed_ok reflects content health, not manifest conformance.
    assert cs.parsed_ok == "6/6"

    # CYCLE_121_SYNTHESIS.json persisted (primary runs_dir + tracked docs copy).
    assert (runs_dir / "CYCLE_121_SYNTHESIS.json").exists()
    docs_json = docs_root / "docs/cycle_reports" / "CYCLE_121_SYNTHESIS.json"
    assert docs_json.exists()
    data = json.loads(docs_json.read_text(encoding="utf-8"))
    assert data["parsed_ok"] == "6/6"
    assert set(data["agents"].keys()) == {"A", "B", "E", "C", "F", "D"}
    # Per-agent claimed_files are surfaced in the machine output.
    assert data["agents"]["B"]["claimed_files"], "expected claimed files for B"


# ── markdown report must NOT be NO_REPORT even when format_health is 0/6 ──────

def test_markdown_cycle_format_health_low_but_parsed_full(tmp_path, monkeypatch):
    """format_health (manifest) may be 0/6 while parsed_ok is 6/6 — the gate
    keys on parsed content, not manifest presence."""
    from automation.report_synthesis.synthesizer import synthesize_cycle

    reports_dir = tmp_path / "reports"
    reports_dir.mkdir()
    monkeypatch.setattr(
        "automation.report_synthesis.synthesizer.REPO_ROOT", tmp_path / "repo", raising=False
    )
    for agent in ["A", "B", "E", "C", "F", "D"]:
        body = REALISTIC_MARKDOWN_REPORT.replace("AGENT_B", f"AGENT_{agent}")
        _write(reports_dir, 122, agent, body)

    with patch(
        "automation.report_synthesis.evidence_crosscheck.gather_actual_evidence"
    ) as mock_ev:
        from automation.report_synthesis.evidence_crosscheck import ActualEvidence

        mock_ev.return_value = ActualEvidence(actual_commits=[], actual_files=[])
        cs = synthesize_cycle(122, reports_dir=reports_dir, runs_dir=tmp_path / "runs")

    assert cs.format_health == "0/6"  # no manifest blocks
    assert cs.parsed_ok == "6/6"  # but all parsed to real content


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(pytest.main([__file__, "-q"]))


# ── Codex P2 regressions (#116) ──────────────────────────────────────────────
def test_root_level_abs_paths_normalize_to_repo_relative():
    """Root-level abs Windows paths normalize to repo-relative regardless of the
    current checkout (Codex P2: don't leave a Fiverr/Fiverr/ prefix)."""
    from automation.report_synthesis.report_parser import _normalize_repo_path
    assert _normalize_repo_path("`C:/Fiverr/Fiverr/.github/workflows/ci.yml`") == ".github/workflows/ci.yml"
    assert _normalize_repo_path("C:\Fiverr\Fiverr\config.yaml") == "config.yaml"
    assert _normalize_repo_path("`C:/Fiverr/Fiverr/pyproject.toml`") == "pyproject.toml"
    # a path already under a known dir is unchanged
    assert _normalize_repo_path("`src/foo/bar.py`") == "src/foo/bar.py"


def test_evidence_only_mentions_not_claimed_as_modified(tmp_path):
    """A report WITHOUT a Files section must NOT turn read-only 'Evidence Files
    Reviewed' path mentions into modified-file claims (Codex P2 #116)."""
    from automation.report_synthesis.report_parser import parse_report
    md = (
        "# CYCLE_205_AGENT_C REPORT\n\n"
        "## Summary\nReviewed routing and control logic for SCRUM-1.\n\n"
        "## Evidence Files Reviewed\n"
        "- `automation/provider_router.py`\n"
        "- `src/discovery/orchestrator.py`\n\n"
        "AGENT_COMPLETE\n"
    )
    p = tmp_path / "CYCLE_205_AGENT_C.md"
    p.write_text(md, encoding="utf-8")
    r = parse_report(p)
    assert r.files_created == [], r.files_created
    assert r.files_modified == [], r.files_modified
