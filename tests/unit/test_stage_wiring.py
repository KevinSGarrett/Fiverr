from __future__ import annotations

import json
from pathlib import Path

from automation import stage_executor as stage_module
from automation.stage_executor import AgentRunResult, StageExecutor, _ControllerAdapter
from click.testing import CliRunner


def _seed_committed_run_records(cycle: int) -> None:
    """ITEM 2.1: write per-agent run-records with a non-empty commit_sha so the
    run-cycle work-proof gate sees real committed work and reaches AGENT_COMPLETE.

    Without this, the hard work-proof gate (correctly) refuses to advance a
    do-nothing cycle and writes CYCLE_NO_WORK instead.
    """
    from automation import runner_paths

    for agent in ("A", "B", "E", "C", "F", "D"):
        d = runner_paths.runs_dir() / f"CYCLE_{cycle:03d}" / "agent_runs" / agent
        d.mkdir(parents=True, exist_ok=True)
        (d / f"agent_{agent}_run_record.json").write_text(
            json.dumps({
                "agent": agent, "cycle": cycle,
                "status": "COMPLETE", "commit_sha": f"sha_{agent}",
            }),
            encoding="utf-8",
        )


def test_stage_executor_called_after_run_cycle(monkeypatch) -> None:
    from automation.ai_cycle_controller import cli

    calls = {"advance": 0}

    class _FakeStageExecutor:
        def __init__(self, controller, config) -> None:
            _ = controller, config

        def advance_if_ready(self) -> bool:
            calls["advance"] += 1
            return True

        def get_current_stage(self) -> int:
            return 3

    monkeypatch.setattr("automation.ai_cycle_controller._run_shell_command", lambda args: (0, "ok"))
    monkeypatch.setattr("automation.stage_executor.StageExecutor", _FakeStageExecutor)

    _seed_committed_run_records(82)
    result = CliRunner().invoke(cli, ["run-cycle", "--cycle", "82"])
    assert result.exit_code == 0
    assert calls["advance"] == 1


def test_stage_advances_without_human_input(monkeypatch) -> None:
    from automation.ai_cycle_controller import cli

    class _FakeStageExecutor:
        def __init__(self, controller, config) -> None:
            _ = controller, config

        def advance_if_ready(self) -> bool:
            return True

        def get_current_stage(self) -> int:
            return 4

    monkeypatch.setattr("automation.ai_cycle_controller._run_shell_command", lambda args: (0, "ok"))
    monkeypatch.setattr("automation.stage_executor.StageExecutor", _FakeStageExecutor)

    _seed_committed_run_records(82)
    result = CliRunner().invoke(cli, ["run-cycle", "--cycle", "82"])
    assert result.exit_code == 0
    assert "Stage advanced automatically to 4" in result.output


def test_stage_state_json_updated_after_advance(tmp_path: Path, monkeypatch) -> None:
    stage_state_path = tmp_path / "stage_state.json"
    stage_evidence_dir = tmp_path / "stages"
    monkeypatch.setattr("automation.stage_executor.STAGE_STATE_PATH", stage_state_path)
    monkeypatch.setattr("automation.stage_executor.STAGE_EVIDENCE_DIR", stage_evidence_dir)
    monkeypatch.setattr("automation.stage_executor.StageExecutor._active_cycle", lambda self: 82)

    class _FakeController:
        def run_agent(self, cycle: int, agent: str, safe_docs_only: bool = False) -> AgentRunResult:
            _ = cycle, agent, safe_docs_only
            return AgentRunResult(
                cursor_invoked=True,
                agent_complete=True,
                duration_seconds=1,
                files_changed=["PM_Pack/automation/prompts/smoke/cursor_docs_smoke_target.md"],
            )

    executor = StageExecutor(controller=_FakeController(), config={})
    advanced = executor.advance_if_ready()
    assert advanced is True
    state_payload = json.loads(stage_state_path.read_text(encoding="utf-8"))
    assert state_payload.get("current_stage") == 3
    assert (stage_evidence_dir / "STAGE2_EVIDENCE.json").exists()


def test_post_cycle_review_autonomous(monkeypatch) -> None:
    calls = {"post_cycle": 0}

    class _FakeController:
        def run_post_cycle_review(self, cycle: int) -> bool:
            _ = cycle
            calls["post_cycle"] += 1
            return True

    monkeypatch.setattr("automation.stage_executor.StageExecutor._active_cycle", lambda self: 82)
    result = StageExecutor(controller=_FakeController(), config={})._execute_stage_5()
    assert result["status"] == "PASS"
    assert calls["post_cycle"] == 1


def test_post_cycle_review_no_human_trigger(monkeypatch) -> None:
    calls = {"post_cycle": 0}

    class _FakeController:
        def run_post_cycle_review(self, cycle: int) -> bool:
            _ = cycle
            calls["post_cycle"] += 1
            return True

    monkeypatch.setattr("automation.stage_executor.StageExecutor._active_cycle", lambda self: 82)
    executor = StageExecutor(controller=_FakeController(), config={})
    payload = executor._execute_stage_5()
    assert payload["post_cycle_review_passed"] is True
    assert calls["post_cycle"] == 1


def test_safe_docs_only_invokes_cursor_adapter(tmp_path: Path, monkeypatch) -> None:
    import automation.ai_cycle_controller as ctrl
    from automation.ai_cycle_controller import cli

    repo_root = tmp_path / "repo"
    prompt_path = repo_root / "PM_Pack/automation/prompts/CYCLE_082_AGENT_A_PROMPT.md"
    prompt_path.parent.mkdir(parents=True, exist_ok=True)
    prompt_path.write_text("AGENT A PROMPT", encoding="utf-8")
    monkeypatch.setattr(ctrl, "REPO_ROOT", repo_root)
    monkeypatch.setattr(ctrl, "_record_nonblocking_error", lambda message: None)

    class _Gate:
        passed = True

        @staticmethod
        def summary() -> str:
            return "OK"

    class _PromptValidation:
        passed = True

        @staticmethod
        def summary() -> str:
            return "PROMPT PASS"

    class _CursorResult:
        status = "complete"
        exit_code = 0
        stdout_tail = ""
        error_message = None

    class _Lifecycle:
        status = "COMPLETE"
        errors: list[str] = []
        commit_sha = ""

    invoked = {"cursor": 0}
    touched_calls = [set(), {"PM_Pack/automation/prompts/smoke/cursor_docs_smoke_target.md"}]

    def _fake_cursor_run(*args, **kwargs):
        _ = args, kwargs
        invoked["cursor"] += 1
        return _CursorResult()

    monkeypatch.setattr("automation.model_gate.check", lambda **kwargs: _Gate())
    monkeypatch.setattr("automation.prompt_validator.validate", lambda *args, **kwargs: _PromptValidation())
    monkeypatch.setattr("automation.cursor_adapter.run_agent", _fake_cursor_run)
    monkeypatch.setattr("automation.state_writer.make_run_dir", lambda cycle, run_id: repo_root / "run")
    monkeypatch.setattr("automation.state_writer.write_controller_state", lambda *args, **kwargs: None)
    monkeypatch.setattr("automation.state_writer.write_heartbeat", lambda *args, **kwargs: None)
    monkeypatch.setattr(
        "automation.run_agent_lifecycle.run_post_agent_lifecycle",
        lambda agent_id, cycle, run_id, run_dir,
               jira_keys=None, contract=None, dry_run=False, pre_dispatch_sha=None: _Lifecycle(),
    )
    monkeypatch.setattr(
        ctrl,
        "_current_repo_touched_files",
        lambda: touched_calls.pop(0) if touched_calls else set(),
    )

    result = CliRunner().invoke(
        cli,
        ["run-agent", "--agent", "A", "--cycle", "82", "--safe-docs-only"],
    )
    assert result.exit_code == 0
    assert invoked["cursor"] == 1


def test_stage_executor_unknown_stage_fails(tmp_path: Path, monkeypatch) -> None:
    stage_state_path = tmp_path / "stage_state.json"
    stage_evidence_dir = tmp_path / "stages"
    stage_state_path.write_text(json.dumps({"current_stage": 99}), encoding="utf-8")
    monkeypatch.setattr("automation.stage_executor.STAGE_STATE_PATH", stage_state_path)
    monkeypatch.setattr("automation.stage_executor.STAGE_EVIDENCE_DIR", stage_evidence_dir)
    executor = StageExecutor(controller=None, config={})
    result = executor.execute_stage(99)
    assert result.status == "FAIL"


def test_stage_executor_stage7_reports_daily_files(tmp_path: Path, monkeypatch) -> None:
    stage_state_path = tmp_path / "stage_state.json"
    stage_evidence_dir = tmp_path / "stages"
    stage_state_path.write_text(json.dumps({"current_stage": 7}), encoding="utf-8")
    stage_evidence_dir.mkdir(parents=True, exist_ok=True)
    (stage_evidence_dir / "DAILY_STAGE6_001.json").write_text("{}", encoding="utf-8")
    monkeypatch.setattr("automation.stage_executor.STAGE_STATE_PATH", stage_state_path)
    monkeypatch.setattr("automation.stage_executor.STAGE_EVIDENCE_DIR", stage_evidence_dir)
    executor = StageExecutor(controller=None, config={})
    payload = executor._execute_stage_7()
    assert payload["daily_reports_collected"] == 1


def test_controller_adapter_paths_and_stage_helpers(tmp_path: Path, monkeypatch) -> None:
    run_results = [
        type("Proc", (), {"returncode": 0, "stdout": "AGENT_COMPLETE", "stderr": ""})(),
        type("Proc", (), {"returncode": 0, "stdout": "foo.py\n", "stderr": ""})(),
        type("Proc", (), {"returncode": 0, "stdout": "", "stderr": ""})(),
        type("Proc", (), {"returncode": 0, "stdout": "", "stderr": ""})(),
        type("Proc", (), {"returncode": 0, "stdout": "", "stderr": ""})(),
        type("Proc", (), {"returncode": 0, "stdout": "", "stderr": ""})(),
        type("Proc", (), {"returncode": 0, "stdout": "", "stderr": ""})(),
        type("Proc", (), {"returncode": 0, "stdout": "", "stderr": ""})(),
        type("Proc", (), {"returncode": 0, "stdout": "PASS", "stderr": ""})(),
    ]

    def fake_run(*args, **kwargs):  # type: ignore[no-untyped-def]
        _ = args, kwargs
        return run_results.pop(0)

    monkeypatch.setattr(stage_module.subprocess, "run", fake_run)
    ctrl_state = tmp_path / "controller_state.json"
    ctrl_state.parent.mkdir(parents=True, exist_ok=True)
    ctrl_state.write_text(json.dumps({"active_cycle": 82}), encoding="utf-8")
    monkeypatch.setattr(stage_module, "RUNNER_ROOT", tmp_path)
    adapter = _ControllerAdapter()
    agent_res = adapter.run_agent(cycle=82, agent="A", safe_docs_only=True)
    assert agent_res.agent_complete is True
    full = adapter.run_full_cycle(auto_merge=False)
    assert full.all_agents_complete is True
    assert adapter.run_post_cycle_review(82) is True


def test_stage_executor_error_branches(tmp_path: Path, monkeypatch) -> None:
    stage_state_path = tmp_path / "stage_state.json"
    stage_evidence_dir = tmp_path / "stages"
    stage_state_path.parent.mkdir(parents=True, exist_ok=True)
    stage_state_path.write_text("{bad json", encoding="utf-8")
    monkeypatch.setattr(stage_module, "STAGE_STATE_PATH", stage_state_path)
    monkeypatch.setattr(stage_module, "STAGE_EVIDENCE_DIR", stage_evidence_dir)
    executor = StageExecutor(controller=None, config={})
    assert executor._read_stage_state() == {"current_stage": 2}
    stage_state_path.write_text(
        json.dumps({"current_stage": 2, "stage_2": "BAD", "stage_3": {"status": "LOCKED"}}),
        encoding="utf-8",
    )
    executor._apply_stage_transition(stage_num=2, status="PASS")
    assert executor._execute_stage_4()["repair_succeeded"] is True
    assert executor._execute_stage_6()["unattended_cycle_hours"] == 24
