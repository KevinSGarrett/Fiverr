"""High-leverage coverage tests for automation utility modules."""

from __future__ import annotations

import json
import subprocess
import time
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import pytest
from automation import (
    branch_guard,
    check_dev_auto_readiness,
    ci_status_reader,
    drift_detector,
    failure_classifier,
    freeze_gate,
    git_adapter,
    github_client,
    jira_client,
    jira_sync,
    lock_manager,
    model_verifier,
    notification_router,
    pm_pack_consistency_audit,
    pm_pack_state_updater,
    pr_builder,
    report_generator,
    scorecard_calculator,
    state_writer,
    validation_runner,
)


def test_git_adapter_high_level_paths(monkeypatch: pytest.MonkeyPatch) -> None:
    calls: list[tuple[str, ...]] = []

    def fake_git(*args: str, cwd: Path = git_adapter.REPO_ROOT, check: bool = True) -> str:
        del cwd, check
        calls.append(args)
        if args == ("branch", "--show-current"):
            return "cycle/077/integration"
        if args == ("status", "--short"):
            return " M a.py\nA  b.py\n"
        if args == ("diff", "--stat"):
            return " 2 files changed"
        if args == ("diff", "--cached", "--name-only"):
            return "a.py\nb.py\n"
        if args == ("rev-parse", "HEAD"):
            return "abc123"
        if args[:2] == ("log", "--oneline"):
            return "abc x\nbcd y"
        return ""

    monkeypatch.setattr(git_adapter, "_git", fake_git)
    assert git_adapter.current_branch() == "cycle/077/integration"
    assert git_adapter.is_clean() is False
    assert git_adapter.changed_files() == ["a.py", "b.py"]
    assert git_adapter.diff_stat() == " 2 files changed"
    assert git_adapter.add_all() == 2
    commit_result = git_adapter.commit("msg")
    assert commit_result.sha == "abc123"
    assert git_adapter.head_sha() == "abc123"
    assert git_adapter.log_oneline(2) == ["abc x", "bcd y"]
    git_adapter.create_cycle_branch("cycle/078/integration")
    assert ("checkout", "-b", "cycle/078/integration") in calls


def test_git_adapter_secret_scan_and_guards(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        git_adapter,
        "_git",
        lambda *args, **kwargs: "secrets/.env\nsrc/app.py\nprivate_key.pem\n"
        if args == ("diff", "--cached", "--name-only")
        else "main",
    )
    findings = git_adapter.secret_scan()
    assert any(".env" in line for line in findings)
    with pytest.raises(ValueError):
        git_adapter.push_branch("main")
    with pytest.raises(ValueError):
        git_adapter.create_cycle_branch("x", base="main")


def test_lock_manager_acquire_release_and_stale(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(lock_manager, "LOCK_DIR", tmp_path / "locks")
    monkeypatch.setattr(lock_manager, "_process_alive", lambda pid: pid == 111)
    lock_path = lock_manager.acquire("runner", "r1", "cycle/077/integration", "run-1")
    assert lock_path.exists()
    assert lock_manager.is_locked("runner") is False  # pid is current process, _process_alive false
    # overwrite with active lock owned by pid 111
    lock_path.write_text(
        json.dumps(
            {"pid": 111, "heartbeat_ts": time.time(), "lock_id": "runner"},
            indent=2,
        ),
        encoding="utf-8",
    )
    with pytest.raises(lock_manager.LockError):
        lock_manager.acquire("runner", "r2", "cycle/077/integration", "run-2")
    # stale lock should be moved then replaced
    lock_path.write_text(
        json.dumps(
            {"pid": 222, "heartbeat_ts": time.time() - (13 * 3600), "lock_id": "runner"},
            indent=2,
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr(lock_manager, "_process_alive", lambda pid: False)
    new_lock = lock_manager.acquire("runner", "r3", "cycle/077/integration", "run-3")
    assert new_lock.exists()
    lock_manager.heartbeat("runner")
    lock_manager.release("runner")
    assert not new_lock.exists()


class _FakeResponse:
    def __init__(self, payload: dict[str, Any], status_code: int = 200) -> None:
        self._payload = payload
        self.status_code = status_code

    def raise_for_status(self) -> None:
        if self.status_code >= 400:
            raise RuntimeError("http error")

    def json(self) -> dict[str, Any]:
        return self._payload


def test_jira_client_endpoints(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        jira_client,
        "get_secret",
        lambda key, default=None: {
            "JIRA_EMAIL": "e@example.com",
            "JIRA_API_TOKEN": "tok",
            "JIRA_BASE_URL": "https://x.atlassian.net",
        }.get(key, default),
    )
    monkeypatch.setattr(
        jira_client.requests,
        "get",
        lambda *args, **kwargs: _FakeResponse(
            {
                "total": 1,
                "issues": [
                    {
                        "key": "SCRUM-1",
                        "fields": {
                            "summary": "s",
                            "status": {"name": "In Progress"},
                            "priority": {"name": "High"},
                            "labels": ["a"],
                            "issuetype": {"name": "Story"},
                        },
                    }
                ],
            }
        ),
    )
    monkeypatch.setattr(
        jira_client.requests,
        "post",
        lambda *args, **kwargs: _FakeResponse({"ok": True, "id": "123"}),
    )
    inv = jira_client.board_inventory()
    assert inv["total"] == 1
    assert inv["issues"][0]["key"] == "SCRUM-1"
    assert jira_client.add_comment("SCRUM-1", "hello")["ok"] is True
    assert jira_client.create_issue("SCRUM", "x", "y")["ok"] is True
    jira_client.transition_issue("SCRUM-1", "31")


def test_github_client_paths(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        github_client,
        "_gh",
        lambda *args, capture=True: (
            json.dumps({"name": "Fiverr"})
            if args[:2] == ("repo", "view")
            else json.dumps({"number": 88, "statusCheckRollup": [{"name": "CI / lint", "conclusion": "success"}]})
            if args[:2] == ("pr", "view")
            else json.dumps([{"name": "existing"}])
            if args[:2] == ("label", "list")
            else ""
        ),
    )
    calls: list[list[str]] = []

    def fake_run(cmd: list[str], **kwargs: Any) -> SimpleNamespace:
        del kwargs
        calls.append(cmd)
        return SimpleNamespace(stdout="cycle/077/integration\n", returncode=0)

    monkeypatch.setattr(github_client.subprocess, "run", fake_run)
    assert github_client.repo_info()["name"] == "Fiverr"
    assert github_client.current_branch() == "cycle/077/integration"
    github_client.create_branch("cycle/078/integration")
    github_client.push_branch("cycle/078/integration")
    assert github_client.get_ci_status(88)[0]["name"] == "CI / lint"
    github_client.ensure_labels(["existing", "new-label"])
    assert any(cmd[:3] == ["git", "checkout", "-b"] for cmd in calls)


def test_model_verifier_and_drift(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    cursor = tmp_path / "cursor_model_state.json"
    claude = tmp_path / "claude_model_state.json"
    cursor.write_text(
        json.dumps(
            {
                "status": "VERIFIED",
                "observed_model": "Codex 5.3",
                "observed_effort": "medium",
                "auto_model_disabled": True,
                "verified_at": "2099-01-01T00:00:00+00:00",
                "binary": "cursor",
            }
        ),
        encoding="utf-8",
    )
    claude.write_text(
        json.dumps({"billing_mode": "claude_subscription_only", "status": "OK"}),
        encoding="utf-8",
    )
    monkeypatch.setattr(model_verifier, "CURSOR_STATE", cursor)
    monkeypatch.setattr(model_verifier, "CLAUDE_STATE", claude)
    assert model_verifier.verify_cursor()["passed"] is True
    assert model_verifier.verify_claude()["passed"] is True
    assert model_verifier.verify_all()["all_passed"] is True

    candidate = tmp_path / "candidate.json"
    candidate.write_text(json.dumps({"model": "Other"}), encoding="utf-8")
    detector = drift_detector.DriftDetector(expected_state_path=cursor)
    assert detector.check_drift(candidate)["drift_detected"] is True


def test_freeze_gate_policy(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    policy_path = tmp_path / "PM_Pack/automation/policies/autonomy_freeze.yml"
    policy_path.parent.mkdir(parents=True, exist_ok=True)
    policy_path.write_text(
        "frozen: true\nreason: INCIDENT\nincident_ref: INC-1\npermitted_while_frozen:\n  - status\n",
        encoding="utf-8",
    )
    assert freeze_gate.load_freeze_policy(repo_root=tmp_path)["frozen"] is True
    freeze_gate.check_freeze("status", repo_root=tmp_path)
    with pytest.raises(freeze_gate.FreezeBlockedError):
        freeze_gate.check_freeze("run-agent", repo_root=tmp_path)
    assert freeze_gate.is_frozen(repo_root=tmp_path) is True


def test_ci_status_reader_and_wait(monkeypatch: pytest.MonkeyPatch) -> None:
    payload = {
        "statusCheckRollup": [
            {"name": "CI / lint", "conclusion": "success"},
            {"name": "CI / type-check", "conclusion": "success"},
            {"name": "CI / tests-coverage", "conclusion": "success"},
            {"name": "CI / smoke-gates", "conclusion": "success"},
            {"name": "codecov/project", "conclusion": "success"},
            {"name": "codecov/patch", "conclusion": "failure"},
        ]
    }

    monkeypatch.setattr(
        ci_status_reader.subprocess,
        "run",
        lambda *args, **kwargs: SimpleNamespace(returncode=0, stdout=json.dumps(payload)),
    )
    status = ci_status_reader.read_pr_ci_status(88)
    assert status.required_checks_passed() is True
    assert status.codecov_project == "SUCCESS"
    assert status.codecov_patch == "FAILURE"

    seq = [
        ci_status_reader.CIStatus(pr_number=1, checks=[{"state": "PENDING"}]),
        ci_status_reader.CIStatus(pr_number=1, checks=[{"state": "SUCCESS"}]),
    ]
    monkeypatch.setattr(ci_status_reader, "read_pr_ci_status", lambda *a, **k: seq.pop(0))
    monkeypatch.setattr(time, "sleep", lambda *_: None)
    finished = ci_status_reader.wait_for_ci(1, max_wait_minutes=1, poll_interval_seconds=1)
    assert finished.checks[0]["state"] == "SUCCESS"


def test_state_writer_and_pr_builder(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(state_writer, "RUNNER_STATE_DIR", tmp_path / "state")
    monkeypatch.setattr(state_writer, "RUNNER_RUNS_DIR", tmp_path / "runs")
    monkeypatch.setattr(state_writer, "HEARTBEAT_PATH", tmp_path / "state/heartbeat.json")
    monkeypatch.setattr(state_writer, "CONTROLLER_STATE_PATH", tmp_path / "state/controller_state.json")

    state_writer.write_heartbeat("OK", cycle=77, agent="F")
    state_writer.write_controller_state("AGENT_DISPATCH", cycle=77, branch="cycle/077/integration")
    run_dir = state_writer.make_run_dir(77, "run-x")
    rec = state_writer.write_agent_run_record(run_dir, "F", 77, "p.md", SimpleNamespace(status="ok"))
    assert rec.exists()
    summary = state_writer.write_run_summary(77, "run-x", {"F": {"status": "done"}}, run_dir)
    assert summary.exists()

    body = pr_builder.build_pr_body(
        cycle=77,
        branch="cycle/077/integration",
        agents=["A", "F"],
        jira_keys=["SCRUM-1"],
        validation_results={"ruff": True, "mypy": True, "pytest": False},
        changed_files=["a.py"],
    )
    assert "Cycle 077" in body
    assert pr_builder.validate_pr_body(body, ["SCRUM-1"])["passed"] is True
    body_path = pr_builder.write_pr_body(
        77,
        run_dir,
        branch="cycle/077/integration",
        agents=["A"],
        jira_keys=["SCRUM-1"],
        validation_results={},
        changed_files=[],
    )
    assert body_path.exists()


def test_pr_builder_create_update(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        subprocess,
        "run",
        lambda args, **kwargs: SimpleNamespace(
            returncode=0, stdout="https://github.com/x/y/pull/88\n", stderr=""
        ),
    )
    created = pr_builder.create_pr(77, "cycle/077/integration", body="x")
    assert created["created"] is True and created["pr_number"] == 88
    updated = pr_builder.update_pr(88, "body")
    assert updated["updated"] is True


def test_failure_classifier_and_validation_runner(monkeypatch: pytest.MonkeyPatch) -> None:
    timed_out = failure_classifier.classify(
        "F", 77, exit_code=None, timed_out=True, no_output=False, stdout="", stderr="", changed_files=[]
    )
    assert timed_out.failure_type == failure_classifier.FailureType.CURSOR_TIMEOUT
    val_fail = failure_classifier.classify(
        "F",
        77,
        exit_code=0,
        timed_out=False,
        no_output=False,
        stdout="",
        stderr="",
        changed_files=["x"],
        validation_results={"ruff": False},
    )
    assert val_fail.failure_type == failure_classifier.FailureType.RUFF_FAILURE

    class _RunResult:
        def __init__(self, code: int, out: str = "", err: str = "") -> None:
            self.returncode = code
            self.stdout = out
            self.stderr = err

    monkeypatch.setattr(
        validation_runner.subprocess,
        "run",
        lambda *args, **kwargs: _RunResult(0, "ok", ""),
    )
    gate = validation_runner.run_gate("ruff", ["python", "-V"])
    assert gate.passed is True
    full = validation_runner.run_full_validation(repo_root=Path("."))
    assert len(full.gates) == 6


def test_pm_pack_consistency_audit(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    runner = tmp_path / "runner"
    (repo / "PM_Pack/automation").mkdir(parents=True, exist_ok=True)
    (repo / "PM_Pack/07_hydration").mkdir(parents=True, exist_ok=True)
    (runner / "state").mkdir(parents=True, exist_ok=True)
    (runner / "status").mkdir(parents=True, exist_ok=True)
    (repo / "PM_Pack/automation/current_policy_snapshot.json").write_text(
        json.dumps({"cycle_current": 77, "last_completed_cycle": None}),
        encoding="utf-8",
    )
    (runner / "state/controller_state.json").write_text(
        json.dumps({"active_cycle": 77, "status": "AGENT_DISPATCH"}),
        encoding="utf-8",
    )
    (runner / "status/current_status.md").write_text("Status active", encoding="utf-8")
    (repo / "PM_Pack/07_hydration/HYDRATION_HEADER.md").write_text("CYCLE_CURRENT: 077", encoding="utf-8")
    (repo / "PM_Pack/07_hydration/STATE_SNAPSHOT.md").write_text("Cycle 077", encoding="utf-8")
    (repo / "PM_Pack/CURRENT_STATE_CANONICAL.md").write_text("Status ACTIVE", encoding="utf-8")
    result = pm_pack_consistency_audit.run_audit(repo_root=repo, runner_root=runner)
    assert result.passed is True
    assert "controller_cycle" in result.sources


def test_scorecard_calculator(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    repo = tmp_path / "repo"
    pm = repo / "PM_Pack/07_hydration"
    pm.mkdir(parents=True, exist_ok=True)
    (pm / "HYDRATION_HEADER.md").write_text(
        "INTERNAL_BUILD_PROGRESS: ~67%\nEND_TO_END_PRODUCTION_READINESS: ~48-50%\nTIER_D2: APPROVED\n",
        encoding="utf-8",
    )
    monkeypatch.setattr(scorecard_calculator, "REPO_ROOT", repo)
    monkeypatch.setattr(scorecard_calculator, "PM_PACK", repo / "PM_Pack")
    s1, s2 = scorecard_calculator.load_current_scores()
    assert s1 == 67.0 and s2 == 49.0
    card = scorecard_calculator.calculate_scorecard(77, score1_delta=10.0, score2_delta=10.0)
    assert card.score1_internal == 77.0
    assert card.score2_e2e <= card.score1_internal
    assert (repo / "PM_Pack/automation/post_cycle_reviews/CYCLE_077_scorecard.json").exists()


def test_branch_guard_guards(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    with pytest.raises(branch_guard.BranchGuardError):
        branch_guard.assert_safe_to_push("main")
    with pytest.raises(branch_guard.BranchGuardError):
        branch_guard.assert_not_force_push(["git", "push", "--force"])
    with pytest.raises(branch_guard.BranchGuardError):
        branch_guard.assert_cycle_branch("feature/x")

    monkeypatch.setattr(
        branch_guard.subprocess,
        "run",
        lambda args, **kwargs: SimpleNamespace(stdout=("x\n" if "--list" in args else ""), returncode=0),
    )
    assert branch_guard.assert_branch_exists("x", cwd=tmp_path) is True
    monkeypatch.setattr(
        branch_guard.subprocess,
        "run",
        lambda args, **kwargs: SimpleNamespace(stdout=" M a.py\n", returncode=0),
    )
    with pytest.raises(branch_guard.BranchGuardError):
        branch_guard.assert_clean_working_tree(cwd=tmp_path)


def test_notification_router_paths(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(notification_router, "RUNNER_ROOT", tmp_path)
    monkeypatch.setattr(notification_router, "NOTIFY_LOG", tmp_path / "logs/notifications.log")
    monkeypatch.setattr(notification_router, "INCIDENTS_DIR", tmp_path / "logs/incidents")
    # Ensure _load_notification_config returns no log_path so NOTIFY_LOG fallback is used
    monkeypatch.setattr(notification_router, "_load_notification_config", lambda: {"log_path": "", "slack_enabled": False, "slack_webhook_url": "", "rate_limit_per_hour": 10})
    monkeypatch.setitem(
        __import__("sys").modules,
        "automation.config_loader",
        SimpleNamespace(get_secret=lambda key, default="": "https://example.com" if key == "SLACK_WEBHOOK_URL" else default),
    )
    monkeypatch.setattr(
        notification_router.subprocess,
        "run",
        lambda *args, **kwargs: SimpleNamespace(returncode=0),
    )
    # Best effort slack call path
    class _DummyReq:
        def __init__(self, *args, **kwargs) -> None:
            pass

    import urllib.request

    monkeypatch.setattr(urllib.request, "Request", _DummyReq)
    monkeypatch.setattr(urllib.request, "urlopen", lambda *args, **kwargs: SimpleNamespace())
    notification_router.notify_blocked("Blocked", "Body", incident_code="AUTH_REQUIRED", cycle=77)
    assert (tmp_path / "logs/notifications.log").exists()
    assert any((tmp_path / "logs/incidents").iterdir())


def test_jira_sync_flow(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    fake_client = SimpleNamespace(
        add_comment=lambda *a, **k: {"ok": True},
        transition_issue=lambda *a, **k: None,
        create_issue=lambda **k: {"key": "SCRUM-999"},
    )
    monkeypatch.setitem(__import__("sys").modules, "automation.jira_client", fake_client)
    keys = ["SCRUM-1"]
    assert jira_sync.on_cycle_planned(77, "cycle/077/integration", ["A", "F"], keys)[0]["status"] == "ok"
    assert jira_sync.on_agent_complete(77, "F", "cycle/077/integration", 88, ["x.py"], True, keys)[0]["status"] == "ok"
    assert jira_sync.on_pr_opened(77, 88, "cycle/077/integration", keys)[0]["status"] == "ok"
    assert jira_sync.on_cycle_merged(77, "sha", keys)[0]["status"] == "ok"
    assert jira_sync.create_blocker_ticket(77, "F", "pytest_failure", "desc") == "SCRUM-999"
    out = jira_sync.write_jira_sync_log(tmp_path / "run", [{"k": 1}])
    assert out.exists()


def test_check_dev_auto_readiness(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    runner = tmp_path / "runner"
    (repo / "PM_Pack/automation/policies").mkdir(parents=True, exist_ok=True)
    (repo / "PM_Pack/automation").mkdir(parents=True, exist_ok=True)
    (runner / "state").mkdir(parents=True, exist_ok=True)
    (runner / "reports/validation").mkdir(parents=True, exist_ok=True)
    (repo / "PM_Pack/automation/policies/autonomy_freeze.yml").write_text("frozen: false\n", encoding="utf-8")
    (runner / "state/cursor_model_state.json").write_text(
        json.dumps({"status": "VERIFIED", "valid_until": "2099-01-01T00:00:00+00:00"}),
        encoding="utf-8",
    )
    (repo / "PM_Pack/automation/state_machine_policy.yml").write_text("ok", encoding="utf-8")
    (repo / "PM_Pack/automation/go_live_stage_gate.yml").write_text("ok", encoding="utf-8")
    monkeypatch.setattr(check_dev_auto_readiness, "REPO_ROOT", repo)
    monkeypatch.setattr(check_dev_auto_readiness, "RUNNER_ROOT", runner)
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)

    def fake_run(args: list[str], **kwargs: Any) -> SimpleNamespace:
        cmd = " ".join(args)
        if "pm-pack-audit" in cmd:
            return SimpleNamespace(stdout="PM_PACK_AUDIT PASS\n", stderr="", returncode=0)
        if "brain-check" in cmd:
            return SimpleNamespace(stdout="BRAIN CHECK PASS\n", stderr="", returncode=0)
        if "git status" in cmd:
            return SimpleNamespace(stdout="", stderr="", returncode=0)
        if "ruff check automation/" in cmd:
            return SimpleNamespace(stdout="", stderr="", returncode=0)
        if "sanitize_repo_export.ps1" in cmd:
            return SimpleNamespace(stdout="PASS\n", stderr="", returncode=0)
        return SimpleNamespace(stdout="", stderr="", returncode=0)

    monkeypatch.setattr(check_dev_auto_readiness.subprocess, "run", fake_run)
    result = check_dev_auto_readiness.check_all()
    assert result["ready_for_dev_auto"] is True


def test_report_generator_and_helpers(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    runner = tmp_path / "runner"
    repo = tmp_path / "repo"
    (runner / "state").mkdir(parents=True, exist_ok=True)
    (runner / "logs/watchdog").mkdir(parents=True, exist_ok=True)
    (runner / "logs").mkdir(parents=True, exist_ok=True)
    (runner / "backups/state_snapshots").mkdir(parents=True, exist_ok=True)
    (repo / "PM_Pack/06_state").mkdir(parents=True, exist_ok=True)
    (runner / "state/heartbeat.json").write_text("{}", encoding="utf-8")
    (runner / "state/controller_state.json").write_text(json.dumps({"status": "POST_CYCLE_PASS"}), encoding="utf-8")
    (runner / "state/cursor_model_state.json").write_text(json.dumps({"verified_at": "2099-01-01T00:00:00+00:00"}), encoding="utf-8")
    (runner / "state/claude_model_state.json").write_text(json.dumps({"verified_at": "2099-01-01T00:00:00+00:00", "billing_mode": "sub", "status": "ok"}), encoding="utf-8")
    (runner / "logs/watchdog/health_x.json").write_text(json.dumps({"health_level": "GREEN"}), encoding="utf-8")
    (repo / "PM_Pack/06_state/STATE_SNAPSHOT.md").write_text("- score1: 70\n- score2: 50\n- tierd2_cap: REMOVED\n", encoding="utf-8")
    (repo / "PM_Pack/06_state/BLOCKERS.md").write_text("## Open\n- blocker A\n## Closed\n- old", encoding="utf-8")
    (runner / "logs/notifications.log").write_text(
        json.dumps({"ts": "2099-01-01T00:00:00+00:00", "severity": "BLOCKED"}) + "\n",
        encoding="utf-8",
    )
    monkeypatch.setattr(report_generator, "RUNNER_ROOT", runner)
    monkeypatch.setattr(report_generator, "REPO_ROOT", repo)
    monkeypatch.setattr(report_generator, "REPORTS_DIR", runner / "reports")
    daily = report_generator.generate_daily_report(77)
    weekly = report_generator.generate_weekly_report()
    assert daily.exists() and weekly.exists()
    assert report_generator._extract_open_blockers("## Open\n- a\n## Closed\n- b") == ["a"]


def test_pm_pack_state_updater_functions(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    repo = tmp_path / "repo"
    pm = repo / "PM_Pack"
    (pm / "07_hydration").mkdir(parents=True, exist_ok=True)
    header = pm / "07_hydration/HYDRATION_HEADER.md"
    header.write_text(
        "CYCLE_CURRENT: 076\nCYCLE_NEXT: 077\nCYCLE_DONE: 075\nLAST_COMPLETED: C075\n## Updated: 2026-01-01\nINTERNAL_BUILD_PROGRESS: ~67%\nEND_TO_END_PRODUCTION_READINESS: ~50%\n",
        encoding="utf-8",
    )
    monkeypatch.setattr(pm_pack_state_updater, "REPO_ROOT", repo)
    monkeypatch.setattr(pm_pack_state_updater, "PM_PACK", pm)
    assert pm_pack_state_updater.update_hydration_header(77, "cycle/077/integration", 88, "sha", 80, 53, 78, []) is True
    log = pm_pack_state_updater.write_cycle_log(77, "cycle/077/integration", 88, "sha", ["A", "F"], True, 80, 53, "IN_PROGRESS", "PASS")
    assert log.exists()
    run_dir = tmp_path / "run"
    run_dir.mkdir(parents=True, exist_ok=True)
    assert pm_pack_state_updater.write_run_summary_full(run_dir, 77, ["A"], {"A": {"status": "done"}}, {"ruff": True}, 88, ["SCRUM-1"]).exists()
    assert pm_pack_state_updater.write_agent_summary(run_dir, 77, {"A": {"status": "done"}}).exists()
    val_obj = SimpleNamespace(gates=[SimpleNamespace(name="ruff", passed=True, output="ok")])
    assert pm_pack_state_updater.write_validation_summary(run_dir, 77, val_obj).exists()
    assert pm_pack_state_updater.write_jira_sync_summary(run_dir, 77, [{"key": "SCRUM-1", "action": "comment"}]).exists()
    assert pm_pack_state_updater.write_github_pr_summary(run_dir, 77, 88, "sha", True).exists()

    monkeypatch.setattr(
        pm_pack_state_updater.subprocess,
        "run",
        lambda args, **kwargs: (
            SimpleNamespace(stdout="PM_Pack/x.md\ndocs/y.md\n", returncode=0, stderr="")
            if args[:3] == ["git", "diff", "--cached"]
            else SimpleNamespace(stdout="headsha\n", returncode=0, stderr="")
        ),
    )
    assert pm_pack_state_updater.commit_governance_closeout(77, "msg") == "headsha"
