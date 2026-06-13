"""Expanded coverage tests for ai_cycle_controller command flows."""

from __future__ import annotations

import subprocess

import json
from pathlib import Path
from types import SimpleNamespace

import automation.ai_cycle_controller as ctrl
from click.testing import CliRunner


def _brain_result(ok: bool) -> SimpleNamespace:
    return SimpleNamespace(
        passed=["p1"],
        warnings=[],
        failed=[] if ok else ["f1"],
        cycle_detected=77,
        wave_detected="Wave 11",
        blockers_detected=["B1"],
        cursor_model_status="VERIFIED",
        claude_model_status="SUBSCRIPTION_VERIFIED",
        post_cycle_prompt_present=True,
        ok=ok,
    )


def test_brain_check_pass_and_fail(monkeypatch) -> None:
    runner = CliRunner()
    monkeypatch.setattr(ctrl, "brain_check", lambda *_: _brain_result(True))
    monkeypatch.setitem(
        __import__("sys").modules,
        "automation.claude_sub_gate",
        SimpleNamespace(check_api_key_absent=lambda: {"passed": True}),
    )
    result = runner.invoke(ctrl.cli, ["brain-check"])
    assert result.exit_code == 0
    assert "BRAIN CHECK PASS" in result.output

    monkeypatch.setattr(ctrl, "brain_check", lambda *_: _brain_result(False))
    fail = runner.invoke(ctrl.cli, ["brain-check"])
    assert fail.exit_code == 1
    assert "BRAIN CHECK FAIL" in fail.output


def test_compile_policy_and_status(monkeypatch, tmp_path: Path) -> None:
    runner = CliRunner()
    monkeypatch.setattr(ctrl, "compile_policy", lambda *_: {"cycle_current": 77, "active_wave": "W11", "e2e_score_pct": 53, "active_agent_lanes": ["A"], "cursor_model": {"status": "VERIFIED"}})
    monkeypatch.setattr(ctrl, "REPO_ROOT", tmp_path)
    state_path = tmp_path / "state.json"
    monkeypatch.setattr(ctrl, "RUNNER_STATE", state_path)
    ctrl._write_runner_state(
        {
            "runner": "r",
            "active_cycle": 77,
            "active_branch": "cycle/077/integration",
            "active_pr": 88,
            "status": "AGENT_DISPATCH",
            "last_heartbeat": "now",
            "last_run_id": "run",
        }
    )
    (Path("C:/AI_Runner/state")).mkdir(parents=True, exist_ok=True)
    (Path("C:/AI_Runner/state/cursor_model_state.json")).write_text(
        json.dumps({"observed_model": "Codex 5.3", "status": "VERIFIED"}),
        encoding="utf-8",
    )
    (tmp_path / "PM_Pack/automation").mkdir(parents=True, exist_ok=True)
    (tmp_path / "PM_Pack/automation/current_policy_snapshot.json").write_text(
        json.dumps({"cycle_current": 77, "active_wave": "W11"}), encoding="utf-8"
    )
    monkeypatch.setattr(
        subprocess,
        "run",
        lambda *a, **k: SimpleNamespace(stdout="Running\n"),
    )
    result = runner.invoke(ctrl.cli, ["compile-policy"])
    assert result.exit_code == 0
    status = runner.invoke(ctrl.cli, ["status"])
    assert status.exit_code == 0
    assert "Active cycle" in status.output


def test_jira_inventory_and_validate_prompts(monkeypatch, tmp_path: Path) -> None:
    runner = CliRunner()
    monkeypatch.setattr(ctrl, "get_secret", lambda key: "token" if key == "JIRA_API_TOKEN" else "x")
    monkeypatch.setitem(
        __import__("sys").modules,
        "automation.jira_client",
        SimpleNamespace(board_inventory=lambda project="SCRUM": {"total": 1, "issues": [{"status": "In Progress", "key": "SCRUM-1", "summary": "s"}]}),
    )
    monkeypatch.setattr(ctrl, "REPO_ROOT", tmp_path)
    result = runner.invoke(ctrl.cli, ["jira-inventory", "--dry-run"])
    assert result.exit_code == 0
    assert "Total non-Done issues : 1" in result.output

    monkeypatch.setitem(
        __import__("sys").modules,
        "automation.prompt_validator",
        SimpleNamespace(
            validate_all=lambda *a, **k: {
                "A": SimpleNamespace(passed=True, prompt_path="a.md", errors=[], warnings=[]),
                "B": SimpleNamespace(passed=False, prompt_path="b.md", errors=["x"], warnings=[]),
            }
        ),
    )
    fail = runner.invoke(ctrl.cli, ["validate-prompts", "--cycle", "77", "--agents", "A,B"])
    assert fail.exit_code == 1
    assert "PROMPT VALIDATION FAIL" in fail.output


def test_plan_cycle_dry_and_live(monkeypatch, tmp_path: Path) -> None:
    runner = CliRunner()
    monkeypatch.setattr(ctrl, "REPO_ROOT", tmp_path)
    (tmp_path / "PM_Pack/automation").mkdir(parents=True, exist_ok=True)
    (tmp_path / "PM_Pack/automation/current_policy_snapshot.json").write_text(
        json.dumps({"cycle_current": 77, "active_agent_lanes": ["A", "B"]}),
        encoding="utf-8",
    )
    dry = runner.invoke(ctrl.cli, ["plan-cycle", "--dry-run"])
    assert dry.exit_code == 0
    assert "PLAN CYCLE DRY RUN COMPLETE" in dry.output
    monkeypatch.setitem(
        __import__("sys").modules,
        "automation.jira_client",
        SimpleNamespace(board_inventory=lambda: {"issues": [{"key": "SCRUM-1"}]}),
    )
    monkeypatch.setitem(
        __import__("sys").modules,
        "automation.prompt_generator",
        SimpleNamespace(write_prompts=lambda **k: {"A": tmp_path / "A.md", "B": tmp_path / "B.md"}),
    )
    (tmp_path / "A.md").write_text("a", encoding="utf-8")
    (tmp_path / "B.md").write_text("b", encoding="utf-8")
    live = runner.invoke(ctrl.cli, ["plan-cycle", "--live"])
    assert live.exit_code == 0
    assert "PLAN CYCLE COMPLETE" in live.output


def test_run_agent_dry_run(monkeypatch, tmp_path: Path) -> None:
    runner = CliRunner()
    monkeypatch.setattr(ctrl, "REPO_ROOT", tmp_path)
    prompt = tmp_path / "PM_Pack/automation/prompts/CYCLE_077_AGENT_F_PROMPT.md"
    prompt.parent.mkdir(parents=True, exist_ok=True)
    prompt.write_text("prompt", encoding="utf-8")
    monkeypatch.setitem(
        __import__("sys").modules,
        "automation.model_gate",
        SimpleNamespace(check=lambda **k: SimpleNamespace(passed=True, summary=lambda: "ok")),
    )
    monkeypatch.setitem(
        __import__("sys").modules,
        "automation.state_writer",
        SimpleNamespace(
            make_run_dir=lambda *a, **k: tmp_path / "run",
            write_controller_state=lambda *a, **k: None,
            write_heartbeat=lambda *a, **k: None,
        ),
    )
    monkeypatch.setitem(
        __import__("sys").modules,
        "automation.prompt_validator",
        SimpleNamespace(validate=lambda *a, **k: SimpleNamespace(passed=True, summary=lambda: "ok")),
    )
    result = runner.invoke(ctrl.cli, ["run-agent", "--agent", "F", "--cycle", "77", "--dry-run"])
    assert result.exit_code == 0
    assert "RUN AGENT DRY RUN COMPLETE" in result.output


def test_cursor_smoke_recover_status_tick_and_pm_audit(monkeypatch, tmp_path: Path) -> None:
    runner = CliRunner()
    monkeypatch.setattr(ctrl, "REPO_ROOT", tmp_path)
    (tmp_path / "PM_Pack/automation/prompts").mkdir(parents=True, exist_ok=True)
    monkeypatch.setitem(
        __import__("sys").modules,
        "automation.cursor_adapter",
        SimpleNamespace(discover=lambda: None, check_version=lambda: "1.0"),
    )
    smoke = runner.invoke(ctrl.cli, ["cursor-smoke"])
    assert smoke.exit_code == 0
    assert "Cursor CLI is reachable" in smoke.output

    lock_dir = tmp_path / "PM_Pack/automation/locks"
    lock_dir.mkdir(parents=True, exist_ok=True)
    (lock_dir / "x.lock").write_text("x", encoding="utf-8")
    recover = runner.invoke(ctrl.cli, ["recover"])
    assert recover.exit_code == 0
    assert "RECOVER COMPLETE" in recover.output

    monkeypatch.setitem(__import__("sys").modules, "automation.freeze_gate", SimpleNamespace(is_frozen=lambda *_: False))
    monkeypatch.setattr(
        subprocess,
        "run",
        lambda *a, **k: SimpleNamespace(stdout="", returncode=0),
    )
    monkeypatch.setitem(
        __import__("sys").modules,
        "automation.state_writer",
        SimpleNamespace(write_heartbeat=lambda *a, **k: None),
    )
    ctrl._write_runner_state({"status": "PLANNED", "active_cycle": 77})
    st = runner.invoke(ctrl.cli, ["status-tick"])
    assert st.exit_code == 0
    assert "Next action: VALIDATE_PROMPTS" in st.output

    monkeypatch.setitem(
        __import__("sys").modules,
        "automation.pm_pack_consistency_audit",
        SimpleNamespace(run_audit=lambda: SimpleNamespace(passed=True, summary=lambda: "PM_PACK_AUDIT PASS", sources={"a": 1})),
    )
    audit = runner.invoke(ctrl.cli, ["pm-pack-audit"])
    assert audit.exit_code == 0
    assert "PM_PACK_AUDIT PASS" in audit.output

