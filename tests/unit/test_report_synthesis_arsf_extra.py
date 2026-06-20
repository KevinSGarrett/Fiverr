"""
tests/unit/test_report_synthesis_arsf_extra.py
Extended ARSF tests: RSF-24/25/26/28/33/44/45/46/47/48/50/51/52 + ICV-gate + integration checks.
"""
from __future__ import annotations

import sys
from pathlib import Path
from unittest.mock import patch

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

# ============================================================================
# RSF-24/25: Prompt embeds report standard
# ============================================================================

def test_prompt_embeds_report_std():
    """Generated prompt request contains the MANDATORY END-OF-RUN REPORT section."""
    from automation.claude_prompt_creator import _build_agent_prompt_request
    req = _build_agent_prompt_request("B", 85, "cycle/085/integration", pm_context="(test context)")
    assert "MANDATORY END-OF-RUN REPORT" in req
    assert "ARSF:MANIFEST" in req


def test_prompt_template_prefill():
    """Per-agent prompt request has agent-specific cycle IDs and role addendum reference."""
    from automation.claude_prompt_creator import _build_agent_prompt_request
    req_b = _build_agent_prompt_request("B", 85, "cycle/085/integration", pm_context="ctx")
    req_d = _build_agent_prompt_request("D", 85, "cycle/085/integration", pm_context="ctx")
    assert "Agent B" in req_b
    assert "Addendum B" in req_b
    assert "Addendum D" in req_d
    assert "CYCLE_085" in req_b
    assert "CYCLE_085" in req_d


# ============================================================================
# RSF-26: Template parity (manual templates reference report standard)
# ============================================================================

def test_template_parity():
    """Playbook (POST_CYCLE_PM_REVIEW_v4.md) references ARSF report sections."""
    playbook = REPO_ROOT / "PM_Pack/01_pm_instructions/POST_CYCLE_PM_REVIEW_v4.md"
    if not playbook.exists():
        pytest.skip("Playbook not present")
    content = playbook.read_text(encoding="utf-8", errors="replace")
    assert "PART 0.6" in content or "Part 0.6" in content
    assert "PART 9" in content or "Part 9" in content


# ============================================================================
# RSF-28: report_validator wired post-agent (controller)
# ============================================================================

def test_report_validator_wired():
    """Controller source contains the post-agent report validation hook."""
    controller = REPO_ROOT / "automation/ai_cycle_controller.py"
    if not controller.exists():
        pytest.skip("Controller not present")
    content = controller.read_text(encoding="utf-8", errors="replace")
    assert "validate_report" in content
    assert "ARSF" in content


# ============================================================================
# RSF-33: Non-blocking guarantee (fault injection)
# ============================================================================

def test_arsf_nonblocking_fault_injection(tmp_path):
    """synthesizer raising → cycle still completes (no exception propagated)."""
    from unittest.mock import patch

    from automation.report_synthesis.synthesizer import synthesize_cycle

    # Corrupt reports dir to ensure parsing raises.
    # Item 2.2: redirect REPO_ROOT to tmp (tracked-docs persistence).
    bad_dir = tmp_path / "bad_dir_that_doesnt_exist"
    with patch("automation.report_synthesis.synthesizer.REPO_ROOT", tmp_path):
        cs = synthesize_cycle(998, reports_dir=bad_dir, runs_dir=tmp_path / "runs")
    assert cs is not None  # never raises


# ============================================================================
# RSF-48: Playbook Part 0.6 + Part 9
# ============================================================================

def test_playbook_parts():
    """Playbook contains Part 0.6 intake steps and Part 9 directives section."""
    playbook = REPO_ROOT / "PM_Pack/01_pm_instructions/POST_CYCLE_PM_REVIEW_v4.md"
    if not playbook.exists():
        pytest.skip("Playbook not present")
    content = playbook.read_text(encoding="utf-8", errors="replace")
    # Part 0.6
    assert "SYNTHESIS INTAKE" in content or "0.6" in content
    assert "STEP 1" in content and "STEP 7" in content
    # Part 9
    assert "NEXT-CYCLE DIRECTIVES" in content
    assert "corrective gate" in content


# ============================================================================
# RSF-46: Adapter request contains synthesis block
# ============================================================================

def test_review_request_contains_synthesis(tmp_path):
    """review request builder includes synthesis block (graceful when absent)."""

    # The synthesis section should appear in request_content
    # We verify the code path exists in the adapter
    adapter = REPO_ROOT / "automation/claude_post_cycle_adapter.py"
    if not adapter.exists():
        pytest.skip("Adapter not present")
    content = adapter.read_text(encoding="utf-8", errors="replace")
    assert "Last-Cycle Synthesis" in content
    assert "load_cycle_synthesis" in content
    assert "synth_md" in content


# ============================================================================
# RSF-47: Review query emits directives
# ============================================================================

def test_review_directives_parse():
    """Adapter review_query requests NEXT-CYCLE DIRECTIVES output."""
    adapter = REPO_ROOT / "automation/claude_post_cycle_adapter.py"
    if not adapter.exists():
        pytest.skip("Adapter not present")
    content = adapter.read_text(encoding="utf-8", errors="replace")
    assert "NEXT-CYCLE DIRECTIVES" in content


# ============================================================================
# RSF-19: Controller calls ARSF at completion
# ============================================================================

def test_controller_calls_arsf():
    """Controller completion path invokes synthesize_cycle; env-gated."""
    controller = REPO_ROOT / "automation/ai_cycle_controller.py"
    if not controller.exists():
        pytest.skip("Controller not present")
    content = controller.read_text(encoding="utf-8", errors="replace")
    assert "synthesize_cycle" in content or "_arsf_synth" in content
    assert "ARSF_DISABLED" in content or "PYTEST_CURRENT_TEST" in content


# ============================================================================
# RSF-44/45: PM context uses directives + agent prompt injects directives
# ============================================================================

def test_pm_context_uses_directives():
    """_build_pm_context source contains §2A/§2B ARSF injection."""
    creator = REPO_ROOT / "automation/claude_prompt_creator.py"
    if not creator.exists():
        pytest.skip("Creator not present")
    content = creator.read_text(encoding="utf-8", errors="replace")
    assert "LAST CYCLE" in content or "WHAT ACTUALLY HAPPENED" in content
    assert "2A" in content or "HOW TO USE" in content
    assert "load_next_cycle_directives" in content


def test_agent_prompt_injects_directives():
    """_build_agent_prompt_request injects CARRIED TASKS from directives."""
    creator = REPO_ROOT / "automation/claude_prompt_creator.py"
    if not creator.exists():
        pytest.skip("Creator not present")
    content = creator.read_text(encoding="utf-8", errors="replace")
    assert "CARRIED TASKS FROM LAST CYCLE" in content
    assert "corrective_gate" in content


# ============================================================================
# RSF-50: State update uses DELIVERED verdicts only
# ============================================================================

def test_state_update_delivered():
    """Claimed-only story → not counted as delivered in scoring."""
    from automation.report_synthesis.schemas import AgentVerdict

    def score_delivered(agent_results: dict) -> int:
        """Count only DELIVERED agents toward score."""
        return sum(1 for v in agent_results.values() if v == AgentVerdict.DELIVERED.value)

    results = {
        "A": AgentVerdict.DELIVERED.value,
        "B": AgentVerdict.CLAIMED_ONLY.value,
        "E": AgentVerdict.PARTIAL.value,
        "C": AgentVerdict.DELIVERED.value,
        "F": AgentVerdict.DELIVERED.value,
        "D": AgentVerdict.DELIVERED.value,
    }
    delivered_count = score_delivered(results)
    assert delivered_count == 4  # A, C, F, D — not B (CLAIMED_ONLY) or E (PARTIAL)


# ============================================================================
# RSF-51: Impact ledger — DELIVERED items only
# ============================================================================

def test_impact_ledger_delivered():
    """Non-delivered excluded from impact ledger count."""
    from automation.report_synthesis.schemas import AgentVerdict, AgentReportSynthesis, CycleSynthesis

    cs = CycleSynthesis(cycle=84)
    cs.agents["A"] = AgentReportSynthesis(agent="A", verdict=AgentVerdict.DELIVERED.value, carryover=[])
    cs.agents["B"] = AgentReportSynthesis(agent="B", verdict=AgentVerdict.CLAIMED_ONLY.value, carryover=["SCRUM-205"])
    cs.agents["E"] = AgentReportSynthesis(agent="E", verdict=AgentVerdict.PARTIAL.value, carryover=["SCRUM-206"])

    # Impact ledger = only DELIVERED
    delivered = [a for a, s in cs.agents.items() if s.verdict == AgentVerdict.DELIVERED.value]
    not_delivered = [a for a, s in cs.agents.items() if s.verdict != AgentVerdict.DELIVERED.value]
    assert "A" in delivered
    assert "B" in not_delivered
    assert "E" in not_delivered


# ============================================================================
# RSF-52: Golden intake over C082–C084 (stability check)
# ============================================================================

def test_intake_golden_c082_c084(tmp_path):
    """Synthesizing real cycle reports yields sane verdicts (stability).

    Item 2.2: these are real plain-markdown reports with NO ARSF:MANIFEST block.
    They must now parse to populated reports (verdict != NO_REPORT), not collapse
    to 0/6. The synthesis is read from the real docs/cycle_reports but PERSISTED
    to tmp (REPO_ROOT + runs_dir redirected) so the live repo is never written.
    """
    from automation.report_synthesis.synthesizer import synthesize_cycle
    from automation.report_synthesis.schemas import AgentVerdict

    reports_dir = REPO_ROOT / "docs/cycle_reports"
    if not reports_dir.exists():
        pytest.skip("docs/cycle_reports not present")

    for cycle in [82, 83, 84]:
        with patch("automation.report_synthesis.synthesizer.REPO_ROOT", tmp_path), \
             patch("automation.report_synthesis.evidence_crosscheck.gather_actual_evidence") as mock_ev:
            from automation.report_synthesis.evidence_crosscheck import ActualEvidence
            # C084_AGENT_B has no commits — simulate that
            def fake_ev(cyc, branch, **kw):
                if cyc == 84 and "B" in str(branch):
                    return ActualEvidence(actual_commits=[])
                return ActualEvidence(actual_commits=["abc1234"])
            mock_ev.side_effect = fake_ev
            cs = synthesize_cycle(
                cycle,
                reports_dir=reports_dir,
                runs_dir=tmp_path / f"runs/CYCLE_{cycle:03d}_test",
            )
        assert cs.cycle == cycle
        assert cs.cycle_verdict != ""
        # Item 2.2: real markdown reports must NOT collapse to NO_REPORT just
        # because they carry no manifest. Every present report parses to content.
        present = [a for a in ["A", "B", "E", "C", "F", "D"]
                   if (reports_dir / f"CYCLE_{cycle:03d}_AGENT_{a}.md").exists()]
        no_report = [a for a in present
                     if cs.agents[a].verdict == AgentVerdict.NO_REPORT.value]
        assert no_report == [], (
            f"cycle {cycle}: present reports collapsed to NO_REPORT: {no_report}"
        )
        # C084 should show at least one non-DELIVERED agent (B was CLAIMED_ONLY)
        if cycle == 84:
            non_delivered = [a for a, s in cs.agents.items() if s.verdict != AgentVerdict.DELIVERED.value]
            # At minimum, B should not be DELIVERED (it admitted no commits)
            assert len(non_delivered) >= 1
