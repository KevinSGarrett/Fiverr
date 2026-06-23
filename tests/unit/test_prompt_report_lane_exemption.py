"""The generated-prompt request must tell every agent that its end-of-run report at
docs/cycle_reports/CYCLE_NNN_AGENT_X.md is a MANDATORY deliverable and an EXPLICIT
EXCEPTION to its file-ownership lane.

Observed live (cycle-84 agent B): B built and committed a real Wave-11 feature, but its
prompt stated the lane as src/**+tests/** only, so B (correctly obeying the lane) skipped
its required report — the runner then failed the run with NO_REPORT and committed nothing.
The instruction must make the report an explicit lane exception so the agent writes it.
"""
from __future__ import annotations

from automation.claude_prompt_creator import (
    _build_agent_prompt_request,
    _build_scaffold_head,
    _build_scaffold_tail,
)


def _hybrid_prompt(agent: str, cycle: int = 84) -> str:
    """The ACTUAL delivered prompt under GEN_HYBRID (default): scaffold head + tail
    bracket the Claude-authored task bodies. Codex #135 P1: the exemption must live
    HERE, not only in the (non-default) _build_agent_prompt_request path."""
    head = _build_scaffold_head(agent, cycle, f"cycle/{cycle:03d}/integration", ["SCRUM-205"])
    tail = _build_scaffold_tail(agent, cycle)
    return head + "\n" + tail


def test_report_path_is_in_the_request():
    req = _build_agent_prompt_request("B", 84, "cycle/084/integration", "PM CONTEXT")
    assert "docs/cycle_reports/CYCLE_084_AGENT_B.md" in req


def test_report_is_declared_a_lane_exemption():
    req = _build_agent_prompt_request("B", 84, "cycle/084/integration", "PM CONTEXT")
    low = req.lower()
    assert "lane exemption" in low or "exception to the agent's file-ownership" in low, (
        "the request must state the report is an explicit exception to the ownership lane"
    )
    # And it must warn that omitting it fails the run (so the agent treats it as required).
    assert "no_report" in low


def test_exemption_present_for_implementation_agents():
    # Implementation agents (src/tests lanes) are the ones that previously skipped the
    # report; the exemption must render for them too.
    for agent in ("B", "F"):
        req = _build_agent_prompt_request(agent, 84, "cycle/084/integration", "ctx")
        assert f"docs/cycle_reports/CYCLE_084_AGENT_{agent}.md" in req
        assert "lane exemption" in req.lower()


# --- The DEFAULT (GEN_HYBRID) delivered prompt must carry the exemption (Codex #135 P1) ---

def test_hybrid_scaffold_has_report_path_and_exemption_for_B_and_F():
    for agent in ("B", "F"):
        prompt = _hybrid_prompt(agent)
        assert f"docs/cycle_reports/CYCLE_084_AGENT_{agent}.md" in prompt
        low = prompt.lower()
        # PQ-2 head must declare the report a required exception to the lane,
        assert "required exception" in low
        # the tail must reiterate it's an explicit exception with the NO_REPORT consequence.
        assert "explicit exception to your file-ownership lane" in low
        assert "no_report" in low


def test_hybrid_scaffold_pq2_no_longer_says_only_these_paths():
    # The old PQ-2 wording ("create/modify ONLY these paths") is what made B treat the
    # report as out-of-lane; ensure it's been reframed as an implementation lane.
    prompt = _hybrid_prompt("B")
    assert "create/modify ONLY these paths" not in prompt
    assert "IMPLEMENTATION lane" in prompt
