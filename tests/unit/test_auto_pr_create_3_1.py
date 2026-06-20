"""ITEM 3.1 — Deterministic autonomous PR-create in the loop.

The autonomous loop previously HALTED after agents committed (the orphaned
``pr_builder.create_pr`` was never called). This item wires a new idempotent,
fail-closed ``pr_builder.open_cycle_pr`` into ``cmd_run_cycle`` AFTER the
work-proof gate writes AGENT_COMPLETE.

These tests prove:
  * ``open_cycle_pr`` happy path: push ok + no existing PR + create ok + verify
    ok → ``{"created": True, "verified": True}``.
  * duplicate guard: an existing OPEN PR returns existing (no second create).
  * no token → fail closed (created False, error) and NO gh/git subprocess runs.
  * push rc!=0 → error, create_pr never called.
  * GH_TOKEN is exported from GH_AUTOMATION_TOKEN for the gh CLI.
  * a committed cycle calls open_cycle_pr exactly once and records the PR in
    controller_state, staying AGENT_COMPLETE.
  * a PR-create failure is FAIL CLOSED (PR_CREATE_FAILED + blocked notify), never
    a silent advance.
  * a no-work cycle never attempts a PR (stays CYCLE_NO_WORK).

ALL git/gh subprocess calls are mocked — no real push/PR/network happens. The
real ``open_cycle_pr`` is captured at import (``_REAL_OPEN_CYCLE_PR``) so the
autouse ``_fake_open_cycle_pr`` seam from conftest does not shadow it for the
unit tests that exercise the real function.
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest
from click.testing import CliRunner

from automation import pr_builder, runner_paths
from automation.ai_cycle_controller import cli

# Capture the REAL implementation before the autouse conftest seam patches the
# module attribute, so the unit tests below exercise genuine push/create/verify
# logic against mocked subprocess calls.
_REAL_OPEN_CYCLE_PR = pr_builder.open_cycle_pr

AGENTS = ["A", "B", "E", "C", "F", "D"]


@pytest.fixture(autouse=True)
def _clean_controller_state():
    """Remove the (session-persistent) controller_state.json after each test.

    The session-scoped tmp runner root persists controller_state.json across
    tests. These 3.1 tests write high active_cycle values (300+) to exercise the
    run-cycle / tick wiring; leaving them behind would trip the monotonic guard
    in later, alphabetically-following tests (e.g. cycle-authority writes 84).
    Cleaning up after each test keeps the suite order-independent.
    """
    yield
    try:
        (runner_paths.state_dir() / "controller_state.json").unlink()
    except OSError:
        pass


# ---------------------------------------------------------------------------
# subprocess fakes
# ---------------------------------------------------------------------------
class _FakeProc:
    def __init__(self, returncode: int = 0, stdout: str = "", stderr: str = "") -> None:
        self.returncode = returncode
        self.stdout = stdout
        self.stderr = stderr


def _install_subprocess(monkeypatch: pytest.MonkeyPatch, router) -> list[list[str]]:
    """Patch ``subprocess.run`` inside pr_builder; record every argv.

    ``router(argv)`` returns a ``_FakeProc`` for the matched command. Returns the
    list of recorded argvs so a test can assert which subprocesses ran.
    """
    calls: list[list[str]] = []
    import subprocess

    def _fake_run(args, *a, **k):  # noqa: ANN001, ANN002, ANN003
        calls.append(list(args))
        return router(list(args))

    monkeypatch.setattr(subprocess, "run", _fake_run)
    return calls


def _default_router(*, list_json: str = "[]", view_number: int = 42,
                    push_rc: int = 0, create_url: str = "") -> object:
    """Build a router covering git push / gh pr list / gh pr create / gh pr view."""
    url = create_url or "https://github.com/KevinSGarrett/Fiverr/pull/42"

    def _route(args):
        if args[0] == "git" and "push" in args:
            return _FakeProc(returncode=push_rc, stderr="" if push_rc == 0 else "denied")
        if args[:3] == ["gh", "pr", "list"]:
            return _FakeProc(returncode=0, stdout=list_json)
        if args[:3] == ["gh", "pr", "create"]:
            return _FakeProc(returncode=0, stdout=url)
        if args[:3] == ["gh", "pr", "view"]:
            return _FakeProc(returncode=0, stdout=json.dumps({"number": view_number, "state": "OPEN"}))
        return _FakeProc(returncode=1, stderr=f"unexpected argv: {args}")

    return _route


# ---------------------------------------------------------------------------
# open_cycle_pr unit behaviour (real function, mocked subprocess)
# ---------------------------------------------------------------------------
def test_open_cycle_pr_happy_path(monkeypatch):
    monkeypatch.setenv("GH_TOKEN", "tok")
    calls = _install_subprocess(
        monkeypatch, _default_router(list_json="[]", view_number=42)
    )

    res = _REAL_OPEN_CYCLE_PR(101)

    assert res["created"] is True
    assert res["existing"] is False
    assert res["verified"] is True
    assert res["pr_number"] == 42
    assert res["error"] == ""
    # push → list → create → view all ran.
    cmds = [c[:3] for c in calls]
    assert ["git", "push", "-u"] == calls[0][:3]
    assert ["gh", "pr", "list"] in cmds
    assert ["gh", "pr", "create"] in cmds
    assert ["gh", "pr", "view"] in cmds


def test_open_cycle_pr_duplicate_guard(monkeypatch):
    monkeypatch.setenv("GH_TOKEN", "tok")
    existing = json.dumps([{"number": 7, "url": "https://github.com/KevinSGarrett/Fiverr/pull/7"}])
    calls = _install_subprocess(monkeypatch, _default_router(list_json=existing))

    res = _REAL_OPEN_CYCLE_PR(102)

    assert res["created"] is False
    assert res["existing"] is True
    assert res["pr_number"] == 7
    assert res["url"].endswith("/pull/7")
    assert res["error"] == ""
    # create must NOT have run (idempotent).
    assert ["gh", "pr", "create"] not in [c[:3] for c in calls]


def test_open_cycle_pr_no_token_fails_closed(monkeypatch):
    for var in ("GH_AUTOMATION_TOKEN", "GH_TOKEN", "GITHUB_TOKEN"):
        monkeypatch.delenv(var, raising=False)
    calls = _install_subprocess(monkeypatch, _default_router())

    res = _REAL_OPEN_CYCLE_PR(103)

    assert res["created"] is False
    assert res["error"] == "no gh token"
    # No git/gh subprocess ran at all (fail closed before any call).
    assert calls == []


def test_open_cycle_pr_push_failure(monkeypatch):
    monkeypatch.setenv("GH_TOKEN", "tok")
    calls = _install_subprocess(monkeypatch, _default_router(push_rc=1))

    res = _REAL_OPEN_CYCLE_PR(104)

    assert res["created"] is False
    assert "push failed" in res["error"]
    # Only the push ran; no list/create/view.
    assert [c[:3] for c in calls] == [["git", "push", "-u"]]


def test_open_cycle_pr_sets_gh_token_from_automation_token(monkeypatch):
    """With only GH_AUTOMATION_TOKEN set, GH_TOKEN is exported for the gh CLI."""
    import os
    for var in ("GH_TOKEN", "GITHUB_TOKEN"):
        monkeypatch.delenv(var, raising=False)
    monkeypatch.setenv("GH_AUTOMATION_TOKEN", "automation-tok")
    _install_subprocess(monkeypatch, _default_router())

    res = _REAL_OPEN_CYCLE_PR(105)

    assert res["created"] is True
    assert os.environ.get("GH_TOKEN") == "automation-tok"


def test_open_cycle_pr_verify_mismatch_is_error(monkeypatch):
    """A create that gh pr view cannot confirm is reported as not-verified error."""
    monkeypatch.setenv("GH_TOKEN", "tok")
    # create returns pull/42 (number 42) but view confirms a different number.
    _install_subprocess(monkeypatch, _default_router(view_number=999))

    res = _REAL_OPEN_CYCLE_PR(106)

    assert res["created"] is False
    assert res["verified"] is False
    assert "verify mismatch" in res["error"]


# ---------------------------------------------------------------------------
# run-cycle wiring (open_cycle_pr mocked at the call site)
# ---------------------------------------------------------------------------
def _run_dir(cycle: int, agent: str) -> Path:
    return runner_paths.runs_dir() / f"CYCLE_{cycle:03d}" / "agent_runs" / agent


def _write_record(cycle: int, agent: str, *, commit_sha: str = "",
                  status: str = "COMPLETE") -> None:
    d = _run_dir(cycle, agent)
    d.mkdir(parents=True, exist_ok=True)
    (d / f"agent_{agent}_run_record.json").write_text(
        json.dumps({
            "agent": agent, "cycle": cycle, "status": status,
            "commit_sha": commit_sha, "no_work": (not commit_sha),
            "justified_no_op": False,
        }),
        encoding="utf-8",
    )


@pytest.fixture
def offline(monkeypatch: pytest.MonkeyPatch):
    """Keep the controller offline (mirrors the 2.1 offline fixture)."""
    import automation.jira_client as jira
    monkeypatch.setattr(jira, "board_inventory", lambda *a, **k: {"issues": []})
    import automation.claude_prompt_creator as cpc
    monkeypatch.setattr(
        cpc, "verify_jira_ac_completion",
        lambda *a, **k: {"passed": True, "missing": [], "key": "NONE"},
    )
    import automation.stage_executor as se
    monkeypatch.setattr(se.StageExecutor, "advance_if_ready", lambda self: False)
    monkeypatch.setattr(se.StageExecutor, "get_current_stage", lambda self: 2)
    return monkeypatch


@pytest.fixture
def capture_notifications(monkeypatch: pytest.MonkeyPatch):
    calls: list[dict] = []
    import automation.notification_router as nr

    def _fake_blocked(title: str, body: str = "", incident_code: str = "",
                      cycle: int | None = None) -> None:
        calls.append({"title": title, "body": body,
                      "incident_code": incident_code, "cycle": cycle})

    monkeypatch.setattr(nr, "notify_blocked", _fake_blocked)
    return calls


def test_run_cycle_opens_pr_on_committed_work(offline, capture_notifications, monkeypatch):
    """A cycle with committed agents calls open_cycle_pr once; PR recorded; state stays AGENT_COMPLETE."""
    cycle = 301
    for ag in AGENTS:
        _write_record(cycle, ag, commit_sha=f"sha_{ag}")

    seen: list[int] = []

    def _fake_open(c, *a, **k):  # noqa: ANN001
        seen.append(c)
        return {"created": True, "existing": False, "pr_number": 1234,
                "url": "https://github.com/KevinSGarrett/Fiverr/pull/1234",
                "verified": True, "error": ""}

    monkeypatch.setattr(pr_builder, "open_cycle_pr", _fake_open)

    result = CliRunner().invoke(cli, ["run-cycle", "--cycle", str(cycle)])

    assert result.exit_code == 0, result.output
    assert seen == [cycle], "open_cycle_pr must be called exactly once"
    state = json.loads((runner_paths.state_dir() / "controller_state.json").read_text())
    assert state["status"] == "AGENT_COMPLETE"
    assert state["active_pr"] == 1234
    # No PR_CREATE_FAILED notification on success.
    assert not [c for c in capture_notifications if c["incident_code"] == "PR_CREATE_FAILED"]


def test_run_cycle_pr_failure_is_fail_closed(offline, capture_notifications, monkeypatch):
    """open_cycle_pr returning created False → PR_CREATE_FAILED + blocked notify, not silent advance."""
    cycle = 302
    for ag in AGENTS:
        _write_record(cycle, ag, commit_sha=f"sha_{ag}")

    monkeypatch.setattr(
        pr_builder, "open_cycle_pr",
        lambda c, *a, **k: {"created": False, "existing": False, "pr_number": None,
                            "url": "", "verified": False, "error": "no gh token"},
    )

    result = CliRunner().invoke(cli, ["run-cycle", "--cycle", str(cycle)])

    assert result.exit_code == 1, result.output
    state = json.loads((runner_paths.state_dir() / "controller_state.json").read_text())
    assert state["status"] == "PR_CREATE_FAILED"
    assert state["status"] != "AGENT_COMPLETE"
    pr_fail = [c for c in capture_notifications if c["incident_code"] == "PR_CREATE_FAILED"]
    assert pr_fail, "expected a PR_CREATE_FAILED blocked notification"
    assert pr_fail[0]["cycle"] == cycle


def test_run_cycle_existing_pr_is_not_failure(offline, capture_notifications, monkeypatch):
    """An idempotent 'existing' PR is treated as success (no fail-closed)."""
    cycle = 303
    for ag in AGENTS:
        _write_record(cycle, ag, commit_sha=f"sha_{ag}")

    monkeypatch.setattr(
        pr_builder, "open_cycle_pr",
        lambda c, *a, **k: {"created": False, "existing": True, "pr_number": 55,
                            "url": "https://github.com/KevinSGarrett/Fiverr/pull/55",
                            "verified": False, "error": ""},
    )

    result = CliRunner().invoke(cli, ["run-cycle", "--cycle", str(cycle)])

    assert result.exit_code == 0, result.output
    state = json.loads((runner_paths.state_dir() / "controller_state.json").read_text())
    assert state["status"] == "AGENT_COMPLETE"
    assert state["active_pr"] == 55
    assert not [c for c in capture_notifications if c["incident_code"] == "PR_CREATE_FAILED"]


def test_no_pr_for_no_work_cycle(offline, capture_notifications, monkeypatch):
    """An all-NO_WORK cycle hits CYCLE_NO_WORK and never attempts a PR."""
    cycle = 304
    for ag in AGENTS:
        _write_record(cycle, ag, commit_sha="")

    called: list[int] = []
    monkeypatch.setattr(
        pr_builder, "open_cycle_pr",
        lambda c, *a, **k: called.append(c) or {"created": True},  # type: ignore[func-returns-value]
    )

    result = CliRunner().invoke(cli, ["run-cycle", "--cycle", str(cycle)])

    assert result.exit_code == 1, result.output
    state = json.loads((runner_paths.state_dir() / "controller_state.json").read_text())
    assert state["status"] == "CYCLE_NO_WORK"
    assert called == [], "no PR may be attempted for a no-work cycle"


# ---------------------------------------------------------------------------
# tick recovery for PR_CREATE_FAILED
# ---------------------------------------------------------------------------
def test_pr_create_failed_in_status_explanation_map():
    """PR_CREATE_FAILED is explained in the autopilot status map (operator clarity)."""
    import automation.ai_cycle_controller as ctrl
    src = Path(ctrl.__file__).read_text(encoding="utf-8")
    assert '"PR_CREATE_FAILED": "PR-create failed' in src


def test_pr_create_failed_tick_retries_and_advances(offline, monkeypatch):
    """A PR_CREATE_FAILED tick re-attempts open_cycle_pr; success → AGENT_COMPLETE + PR recorded."""
    import automation.cycle_authority as ca
    monkeypatch.setattr(ca, "reconcile", lambda **k: {"action": "OK", "consensus": 305})

    monkeypatch.setattr(
        pr_builder, "open_cycle_pr",
        lambda c, *a, **k: {"created": True, "existing": False, "pr_number": 88,
                            "url": "https://github.com/KevinSGarrett/Fiverr/pull/88",
                            "verified": True, "error": ""},
    )

    from automation.state_writer import write_controller_state
    write_controller_state("PR_CREATE_FAILED", cycle=305)

    result = CliRunner().invoke(cli, ["tick"])
    assert result.exit_code == 0, result.output

    state = json.loads((runner_paths.state_dir() / "controller_state.json").read_text())
    assert state["status"] == "AGENT_COMPLETE"
    assert state["active_pr"] == 88


def test_pr_create_failed_tick_stays_on_repeat_failure(offline, capture_notifications, monkeypatch):
    """A PR_CREATE_FAILED tick whose retry also fails stays PR_CREATE_FAILED (no advance)."""
    import automation.cycle_authority as ca
    monkeypatch.setattr(ca, "reconcile", lambda **k: {"action": "OK", "consensus": 306})

    monkeypatch.setattr(
        pr_builder, "open_cycle_pr",
        lambda c, *a, **k: {"created": False, "existing": False, "pr_number": None,
                            "url": "", "verified": False, "error": "push failed: denied"},
    )

    from automation.state_writer import write_controller_state
    write_controller_state("PR_CREATE_FAILED", cycle=306)

    result = CliRunner().invoke(cli, ["tick"])
    assert result.exit_code == 0, result.output

    state = json.loads((runner_paths.state_dir() / "controller_state.json").read_text())
    assert state["status"] == "PR_CREATE_FAILED"
    assert [c for c in capture_notifications if c["incident_code"] == "PR_CREATE_FAILED"]
