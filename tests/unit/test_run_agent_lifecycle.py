"""Unit tests for run_agent_lifecycle.py — ownership, secrets, validation gates."""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[2]))

from automation.run_agent_lifecycle import AGENT_OWNERSHIP, _check_ownership


class TestAgentOwnership:
    def test_all_six_agents_defined(self):
        """All six agents A, B, E, C, F, D must have ownership rules."""
        assert set("ABECFD") == set(AGENT_OWNERSHIP.keys())

    def test_agent_d_docs_only(self):
        """Agent D must not be allowed to modify src/."""
        d_rules = AGENT_OWNERSHIP["D"]
        forbidden = d_rules.get("forbidden", [])
        assert any("src" in f for f in forbidden), \
            "Agent D must have src/ in forbidden list"

    def test_agent_e_tests_only(self):
        """Agent E must only be allowed in tests/."""
        e_rules = AGENT_OWNERSHIP["E"]
        allowed = e_rules.get("allowed", [])
        assert any("tests" in a for a in allowed)
        forbidden = e_rules.get("forbidden", [])
        assert any("src" in f for f in forbidden)

    def test_check_ownership_no_violations(self):
        """check_ownership returns empty list for files in scope."""
        # Agent A is allowed in src/pipeline
        violations = _check_ownership("A", ["src/pipeline/collector.py", "tests/unit/test_x.py"])
        assert isinstance(violations, list)

    def test_check_ownership_detects_violation(self):
        """check_ownership detects when agent modifies forbidden paths."""
        # Agent D should not modify src/
        violations = _check_ownership("D", ["src/pipeline/collector.py"])
        assert len(violations) > 0
        assert "src/pipeline/collector.py" in violations

    def test_check_ownership_agent_e_src_violation(self):
        """Agent E cannot modify src/ files."""
        violations = _check_ownership("E", ["src/scoring/scorer.py"])
        assert len(violations) > 0

    def test_check_ownership_empty_files(self):
        """No files = no violations."""
        violations = _check_ownership("A", [])
        assert violations == []


class TestAgentLifecycleResult:
    def test_result_dataclass(self):
        from automation.run_agent_lifecycle import AgentLifecycleResult
        r = AgentLifecycleResult(agent="A", cycle=75, run_id="20260611T000000",
                                 status="COMPLETE")
        assert r.agent == "A"
        assert r.cycle == 75
        assert r.status == "COMPLETE"
        d = r.to_dict()
        assert isinstance(d, dict)
        assert d["agent"] == "A"

    def test_result_errors_default_empty(self):
        from automation.run_agent_lifecycle import AgentLifecycleResult
        r = AgentLifecycleResult(agent="B", cycle=75, run_id="test", status="IN_PROGRESS")
        assert r.errors == []
        assert r.changed_files == []


class TestClassifyFailure:
    def test_classify_lint_failure(self):
        """ruff errors should classify as lint."""
        from automation.repair_loop import _classify_failure
        result = _classify_failure(["ruff check failed: E501 line too long"])
        assert result == "lint"

    def test_classify_type_failure(self):
        """mypy errors should classify as typecheck."""
        from automation.repair_loop import _classify_failure
        result = _classify_failure(["mypy error: incompatible types"])
        assert result == "typecheck"

    def test_classify_test_failure(self):
        """pytest errors should classify as test."""
        from automation.repair_loop import _classify_failure
        result = _classify_failure(["pytest FAILED tests/unit/test_x.py"])
        assert result == "test"

    def test_classify_report_failure(self):
        """Missing report should classify as report."""
        from automation.repair_loop import _classify_failure
        result = _classify_failure(["Required report not found"])
        assert result == "report"

    def test_classify_general_fallback(self):
        """Unknown errors fall back to general."""
        from automation.repair_loop import _classify_failure
        result = _classify_failure(["Some unknown error message"])
        assert result == "general"


def _setup_lifecycle_repo(tmp_path: Path, monkeypatch):
    from automation import run_agent_lifecycle as lifecycle

    repo_root = tmp_path / "repo"
    report_path = repo_root / "docs/cycle_reports/CYCLE_081_AGENT_A.md"
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text("AGENT_COMPLETE\n", encoding="utf-8")
    monkeypatch.setattr(lifecycle, "REPO_ROOT", repo_root)
    monkeypatch.setattr(lifecycle, "_get_changed_files", lambda: ["tests/unit/test_run_agent_lifecycle.py"])
    monkeypatch.setattr(lifecycle, "_check_ownership", lambda agent, files: [])
    monkeypatch.setattr(lifecycle, "_scan_changed_files", lambda files: [])
    monkeypatch.setattr(lifecycle, "_run_validation", lambda agent: (True, "all passed"))
    return lifecycle


def test_dispatch_020_ruff_failure_blocks_commit(tmp_path: Path, monkeypatch) -> None:
    lifecycle = _setup_lifecycle_repo(tmp_path, monkeypatch)
    commit_called = {"count": 0}
    state_updates: list[str] = []

    class _Result:
        def __init__(self, returncode: int) -> None:
            self.returncode = returncode
            self.stdout = ""
            self.stderr = ""

    def _fake_subprocess_run(cmd, *args, **kwargs):
        _ = args, kwargs
        if isinstance(cmd, list) and "ruff" in cmd:
            return _Result(1)
        return _Result(0)

    monkeypatch.setattr("automation.run_agent_lifecycle.subprocess.run", _fake_subprocess_run)
    monkeypatch.setattr(
        lifecycle,
        "_commit_agent_work",
        lambda *args, **kwargs: commit_called.__setitem__("count", commit_called["count"] + 1),
    )
    monkeypatch.setattr(lifecycle, "_write_controller_state", lambda status, cycle: state_updates.append(status))

    result = lifecycle.run_post_agent_lifecycle("A", 81, "rid", tmp_path / "run", dry_run=False)
    assert result.status == "BLOCKED_FAILING_WORK"
    assert result.commit_blocked is True
    assert commit_called["count"] == 0
    assert "BLOCKED_FAILING_WORK" in state_updates


def test_dispatch_020_pytest_failure_blocks_commit(tmp_path: Path, monkeypatch) -> None:
    lifecycle = _setup_lifecycle_repo(tmp_path, monkeypatch)
    commit_called = {"count": 0}

    class _Result:
        def __init__(self, returncode: int) -> None:
            self.returncode = returncode
            self.stdout = ""
            self.stderr = ""

    def _fake_subprocess_run(cmd, *args, **kwargs):
        _ = args, kwargs
        if isinstance(cmd, list) and "pytest" in cmd:
            return _Result(1)
        return _Result(0)

    monkeypatch.setattr("automation.run_agent_lifecycle.subprocess.run", _fake_subprocess_run)
    monkeypatch.setattr(
        lifecycle,
        "_commit_agent_work",
        lambda *args, **kwargs: commit_called.__setitem__("count", commit_called["count"] + 1),
    )
    monkeypatch.setattr(lifecycle, "_write_controller_state", lambda status, cycle: None)

    result = lifecycle.run_post_agent_lifecycle("A", 81, "rid", tmp_path / "run2", dry_run=False)
    assert result.status == "BLOCKED_FAILING_WORK"
    assert result.commit_blocked is True
    assert commit_called["count"] == 0


def test_dispatch_017_contract_validation_commands_run(tmp_path: Path, monkeypatch) -> None:
    lifecycle = _setup_lifecycle_repo(tmp_path, monkeypatch)
    executed: list[str] = []

    class _Result:
        returncode = 0
        stdout = ""
        stderr = ""

    def _fake_subprocess_run(cmd, **kwargs):
        if kwargs.get("shell"):
            executed.append(str(cmd))
        return _Result()

    monkeypatch.setattr("automation.run_agent_lifecycle.subprocess.run", _fake_subprocess_run)
    monkeypatch.setattr(lifecycle, "_run_pre_commit_gate", lambda: (True, "PASS"))
    monkeypatch.setattr(lifecycle, "_commit_agent_work", lambda *args, **kwargs: "abc123")

    contract = {"validation_commands": ["ruff check automation/"]}
    result = lifecycle.run_post_agent_lifecycle(
        "A",
        81,
        "rid",
        tmp_path / "run3",
        contract=contract,
        dry_run=True,
    )
    assert result.status == "COMPLETE"
    assert "ruff check automation/" in executed
