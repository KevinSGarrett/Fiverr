"""ITEM 2.1 — Hard work-proof gate tests.

A no-op cycle (every agent committed nothing) must NEVER report AGENTS_COMPLETE.
These tests prove:
  * the run-cycle cross-check now finds the REAL run-record filename
    (agent_<agent>_run_record.json) — the old `run_record.json` glob matched
    nothing, so the cross-check was dead.
  * an rc==0 agent with empty commit_sha is treated as NO_WORK (not completed).
  * an agent with a non-empty commit_sha counts as completed.
  * a cycle where ALL agents committed nothing lands in CYCLE_NO_WORK (NOT
    AGENT_COMPLETE) and fires a blocked notification.
  * a cycle with at least one real commit still reaches AGENT_COMPLETE.
  * run_agent_lifecycle: zero approved/committed files → status NO_WORK +
    run-record no_work: true.

The autouse conftest fixtures (0.3/0.4) set AUTOPILOT_TEST_HARNESS, fake
``_run_and_stream`` to (0, "ok") WITHOUT a subprocess, and redirect all runner
state to a per-session tmp root. We monkeypatch ``board_inventory`` to stay
offline (the C3 AC-completion block calls it after each COMPLETE agent).
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest
from click.testing import CliRunner

import automation.ai_cycle_controller as ctrl
from automation import runner_paths
from automation.ai_cycle_controller import cli

AGENTS = ["A", "B", "E", "C", "F", "D"]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def _run_dir(cycle: int, agent: str) -> Path:
    return runner_paths.runs_dir() / f"CYCLE_{cycle:03d}" / "agent_runs" / agent


def _write_record(cycle: int, agent: str, *, commit_sha: str = "",
                  status: str = "COMPLETE", justified_no_op: bool = False) -> Path:
    """Write a fake per-agent run-record using the REAL filename convention."""
    d = _run_dir(cycle, agent)
    d.mkdir(parents=True, exist_ok=True)
    path = d / f"agent_{agent}_run_record.json"
    payload = {
        "agent": agent,
        "cycle": cycle,
        "status": status,
        "commit_sha": commit_sha,
        "no_work": (not commit_sha) and not justified_no_op,
        "justified_no_op": justified_no_op,
    }
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return path


@pytest.fixture
def offline(monkeypatch: pytest.MonkeyPatch):
    """Keep the controller offline.

    * No Jira board calls during the C3 AC gate.
    * No real ``run-agent`` subprocess from the post-cycle StageExecutor
      (advance_if_ready would otherwise shell out a live agent dispatch).
    """
    import automation.jira_client as jira
    monkeypatch.setattr(jira, "board_inventory", lambda *a, **k: {"issues": []})
    # Belt-and-braces: AC verifier never flags missing stories (no network).
    import automation.claude_prompt_creator as cpc
    monkeypatch.setattr(
        cpc, "verify_jira_ac_completion",
        lambda *a, **k: {"passed": True, "missing": [], "key": "NONE"},
    )
    # Stage advance after AGENT_COMPLETE must not spawn a real agent subprocess.
    import automation.stage_executor as se
    monkeypatch.setattr(se.StageExecutor, "advance_if_ready", lambda self: False)
    monkeypatch.setattr(se.StageExecutor, "get_current_stage", lambda self: 2)
    return monkeypatch


@pytest.fixture
def capture_notifications(monkeypatch: pytest.MonkeyPatch):
    """Capture notify_blocked calls fired by the controller."""
    calls: list[dict] = []
    import automation.notification_router as nr

    def _fake_blocked(title: str, body: str = "", incident_code: str = "",
                      cycle: int | None = None) -> None:
        calls.append({
            "title": title, "body": body,
            "incident_code": incident_code, "cycle": cycle,
        })

    monkeypatch.setattr(nr, "notify_blocked", _fake_blocked)
    return calls


# ---------------------------------------------------------------------------
# Cross-check / per-agent work-proof unit behaviour (via full run-cycle).
# ---------------------------------------------------------------------------
def test_crosscheck_finds_correctly_named_record(offline, capture_notifications):
    """A record named agent_A_run_record.json is now FOUND by the cross-check.

    The old glob looked for `run_record.json` (never written) so the cross-check
    was dead. We prove the new glob reads our record by giving agent A a real
    commit_sha while every other agent is NO_WORK: the cycle must NOT be all-no-op
    (agent A's commit is detected), so it reaches AGENT_COMPLETE.
    """
    cycle = 201
    _write_record(cycle, "A", commit_sha="deadbeef", status="COMPLETE")
    for ag in AGENTS[1:]:
        _write_record(cycle, ag, commit_sha="", status="COMPLETE")

    result = CliRunner().invoke(cli, ["run-cycle", "--cycle", str(cycle)])

    assert result.exit_code == 0, result.output
    state = json.loads(
        (runner_paths.state_dir() / "controller_state.json").read_text()
    )
    assert state["status"] == "AGENT_COMPLETE"


def test_zero_commit_agent_is_no_work(offline, capture_notifications):
    """rc==0 but commit_sha=='' → agent treated as NO_WORK, not in completed.

    Every agent has an empty commit_sha → the whole cycle is no-work, so the
    work-proof gate writes CYCLE_NO_WORK. The progress file records all six
    agents as NO_WORK (none completed).
    """
    cycle = 202
    for ag in AGENTS:
        _write_record(cycle, ag, commit_sha="", status="COMPLETE")

    result = CliRunner().invoke(cli, ["run-cycle", "--cycle", str(cycle)])

    assert result.exit_code == 1, result.output
    prog = json.loads(
        (runner_paths.state_dir() / "agent_progress.json").read_text()
    )
    assert prog["completed"] == []
    assert sorted(prog["no_work"]) == sorted(AGENTS)


def test_committed_agent_completes(offline, capture_notifications):
    """A run-record with a non-empty commit_sha → that agent counts as completed."""
    cycle = 203
    for ag in AGENTS:
        _write_record(cycle, ag, commit_sha=f"sha_{ag}", status="COMPLETE")

    result = CliRunner().invoke(cli, ["run-cycle", "--cycle", str(cycle)])

    assert result.exit_code == 0, result.output
    prog = json.loads(
        (runner_paths.state_dir() / "agent_progress.json").read_text()
    )
    assert sorted(prog["completed"]) == sorted(AGENTS)
    assert prog.get("no_work", []) == []


# ---------------------------------------------------------------------------
# Cycle-level gating.
# ---------------------------------------------------------------------------
def test_cycle_all_noop_does_not_reach_agents_complete(offline, capture_notifications):
    """All agents have empty commit_sha → state CYCLE_NO_WORK (NOT AGENT_COMPLETE).

    A blocked/alert notification (incident_code=CYCLE_NO_WORK) must fire.
    """
    cycle = 204
    for ag in AGENTS:
        _write_record(cycle, ag, commit_sha="", status="COMPLETE")

    result = CliRunner().invoke(cli, ["run-cycle", "--cycle", str(cycle)])

    assert result.exit_code == 1, result.output
    state = json.loads(
        (runner_paths.state_dir() / "controller_state.json").read_text()
    )
    assert state["status"] == "CYCLE_NO_WORK"
    assert state["status"] != "AGENT_COMPLETE"

    no_work_notes = [c for c in capture_notifications
                     if c["incident_code"] == "CYCLE_NO_WORK"]
    assert no_work_notes, "expected a CYCLE_NO_WORK blocked notification"
    assert no_work_notes[0]["cycle"] == cycle


def test_cycle_with_real_work_reaches_agents_complete(offline, capture_notifications):
    """At least one agent has a commit_sha → AGENT_COMPLETE written.

    The cycle summary uses gate_result AGENTS_COMPLETE; no CYCLE_NO_WORK
    notification fires.
    """
    cycle = 205
    _write_record(cycle, "B", commit_sha="cafef00d", status="COMPLETE")
    for ag in AGENTS:
        if ag != "B":
            _write_record(cycle, ag, commit_sha="", status="COMPLETE")

    result = CliRunner().invoke(cli, ["run-cycle", "--cycle", str(cycle)])

    assert result.exit_code == 0, result.output
    assert "RUN CYCLE COMPLETE" in result.output
    state = json.loads(
        (runner_paths.state_dir() / "controller_state.json").read_text()
    )
    assert state["status"] == "AGENT_COMPLETE"
    assert not [c for c in capture_notifications
                if c["incident_code"] == "CYCLE_NO_WORK"]


def test_justified_no_op_record_counts_as_committed_gate(offline, capture_notifications):
    """An agent run-record flagged justified_no_op is NOT treated as NO_WORK.

    (Even with empty commit_sha.) This keeps a legitimately doc-only / nothing
    -to-do agent from blocking the cycle. With at least one such justified agent
    and the rest committing, the cycle still completes.
    """
    cycle = 206
    _write_record(cycle, "D", commit_sha="", status="COMPLETE", justified_no_op=True)
    for ag in AGENTS:
        if ag != "D":
            _write_record(cycle, ag, commit_sha=f"sha_{ag}", status="COMPLETE")

    result = CliRunner().invoke(cli, ["run-cycle", "--cycle", str(cycle)])

    assert result.exit_code == 0, result.output
    prog = json.loads(
        (runner_paths.state_dir() / "agent_progress.json").read_text()
    )
    # Justified no-op agent D is completed (not NO_WORK), but not a committer.
    assert "D" in prog["completed"]
    assert prog.get("no_work", []) == []


# ---------------------------------------------------------------------------
# Tick recovery: CYCLE_NO_WORK is recoverable.
# ---------------------------------------------------------------------------
def test_cycle_no_work_in_status_explanation_map():
    """CYCLE_NO_WORK is explained in the autopilot status map (operator clarity)."""
    # The _STATUS_EXPLANATION map lives in the autopilot loop. Scan the module.
    mod_src = Path(ctrl.__file__).read_text(encoding="utf-8")
    assert '"CYCLE_NO_WORK": "Cycle produced no committed work' in mod_src


def test_cycle_no_work_tick_routes_to_redispatch(offline, monkeypatch):
    """A CYCLE_NO_WORK tick surfaces the state and routes to READY_TO_DISPATCH.

    This proves the do-nothing cycle is recoverable: a later tick can re-dispatch
    a fresh real run rather than being stuck or silently advancing.
    """
    # Keep the cycle-authority reconcile from rewriting the cycle / aborting tick.
    import automation.cycle_authority as ca
    monkeypatch.setattr(ca, "reconcile", lambda **k: {"action": "OK", "consensus": 207})

    from automation.state_writer import write_controller_state
    write_controller_state("CYCLE_NO_WORK", cycle=207)

    result = CliRunner().invoke(cli, ["tick"])
    assert result.exit_code == 0, result.output

    state = json.loads(
        (runner_paths.state_dir() / "controller_state.json").read_text()
    )
    assert state["status"] == "READY_TO_DISPATCH"


# ---------------------------------------------------------------------------
# run_agent_lifecycle: zero-file agent → NO_WORK.
# ---------------------------------------------------------------------------
def test_lifecycle_no_files_is_no_work(tmp_path, monkeypatch):
    """A lifecycle run with zero approved/committed files → status NO_WORK.

    The run-record persists no_work: true and an empty commit_sha. Under the test
    harness _get_changed_files returns [] (no real git), so no files are approved
    and commit_sha stays empty — exactly the no-op case the gate must catch.
    """
    from automation.run_agent_lifecycle import AgentLifecycle
    import automation.run_agent_lifecycle as ral

    # Isolate REPO_ROOT to tmp — ral.REPO_ROOT is a hardcoded "C:/Fiverr/Fiverr"
    # literal that is wrong on CI (ubuntu), which previously made the lifecycle
    # report-lookup miss and bail at NO_REPORT. Write the report where the
    # lifecycle actually reads it, and force zero changed files deterministically
    # (no git in tmp). No repo-tree pollution.
    monkeypatch.setattr(ral, "REPO_ROOT", tmp_path)
    monkeypatch.setattr(ral, "_run_validation", lambda agent_id: (True, "ok"))
    monkeypatch.setattr(ral, "_get_changed_files", lambda *a, **k: [])
    report = tmp_path / "docs/cycle_reports" / "CYCLE_299_AGENT_B.md"
    report.parent.mkdir(parents=True, exist_ok=True)
    report.write_text("# Cycle 299 Agent B\n\nAGENT_COMPLETE\n", encoding="utf-8")

    run_dir = tmp_path / "agent_runs" / "B"
    result = AgentLifecycle().run(
        agent_id="B", cycle=299, run_id="testrun",
        run_dir=run_dir, jira_keys=[], contract=None, dry_run=False,
    )

    assert result.status == "NO_WORK"
    assert result.no_work is True
    assert result.commit_sha == ""

    record = run_dir / "agent_B_run_record.json"
    assert record.exists()
    data = json.loads(record.read_text())
    assert data["no_work"] is True
    assert data["status"] == "NO_WORK"


def test_lifecycle_justified_no_op_stays_complete(tmp_path, monkeypatch):
    """A justified-no-op contract keeps status COMPLETE even with empty commit_sha."""
    from automation.run_agent_lifecycle import AgentLifecycle
    import automation.run_agent_lifecycle as ral

    monkeypatch.setattr(ral, "REPO_ROOT", tmp_path)
    monkeypatch.setattr(ral, "_run_validation", lambda agent_id: (True, "ok"))
    monkeypatch.setattr(ral, "_get_changed_files", lambda *a, **k: [])
    report = tmp_path / "docs/cycle_reports" / "CYCLE_298_AGENT_D.md"
    report.parent.mkdir(parents=True, exist_ok=True)
    report.write_text("# Cycle 298 Agent D\n\nAGENT_COMPLETE\n", encoding="utf-8")

    run_dir = tmp_path / "agent_runs" / "D"
    result = AgentLifecycle().run(
        agent_id="D", cycle=298, run_id="testrun",
        run_dir=run_dir, jira_keys=[],
        contract={"justified_no_op": True}, dry_run=False,
    )

    assert result.status == "COMPLETE"
    assert result.no_work is False
    assert result.justified_no_op is True


def test_crosscheck_finds_record_under_runid_subdir(offline, capture_notifications):
    """Codex P1 (#115): a real run writes the record under runs/CYCLE_NNN/<run_id>/,
    NOT runs/CYCLE_NNN/agent_runs/<agent>/. The broadened rglob over the whole cycle
    dir must still find it, else a genuinely-committed cycle is misread as CYCLE_NO_WORK.
    """
    cycle = 205
    cycle_dir = runner_paths.runs_dir() / f"CYCLE_{cycle:03d}"
    for ag in AGENTS:
        # Real make_run_dir layout: per-run-id subdir, not agent_runs/<agent>.
        d = cycle_dir / f"20990101T0000{ord(ag) % 10}0" / "agent_runs" / ag
        d.mkdir(parents=True, exist_ok=True)
        (d / f"agent_{ag}_run_record.json").write_text(
            json.dumps({"agent": ag, "cycle": cycle, "status": "COMPLETE",
                        "commit_sha": f"sha_{ag}", "no_work": False,
                        "justified_no_op": False}),
            encoding="utf-8",
        )
    result = CliRunner().invoke(cli, ["run-cycle", "--cycle", str(cycle)])
    assert result.exit_code == 0, result.output
    state = json.loads((runner_paths.state_dir() / "controller_state.json").read_text())
    assert state["status"] == "AGENT_COMPLETE", state
    # Not a single CYCLE_NO_WORK notification.
    assert not [c for c in capture_notifications if c["incident_code"] == "CYCLE_NO_WORK"]
