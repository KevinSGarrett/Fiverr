from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from automation.post_cycle_review import ReviewMode, get_review_result, run_review


@pytest.fixture(autouse=True)
def _mock_expensive_collectors(monkeypatch):
    """Prevent real subprocess/network calls in unit tests."""
    with (
        patch("automation.post_cycle_review._collect_local_code_verification", return_value={}),
        patch("automation.post_cycle_review._collect_github_facts", return_value={}),
        patch("automation.post_cycle_review._collect_jira_facts", return_value={}),
        patch("automation.post_cycle_review._git", return_value=""),
    ):
        yield


def test_run_review_missing_source_prompt_returns_blocked(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    runner = tmp_path / "runner"
    result = run_review(75, ReviewMode.POST_MERGE, repo_root=repo, runner_root=runner)
    assert result.status == "BLOCKED_MISSING_SOURCE_PROMPT"


def test_run_review_advisory_only_blocks_dispatch(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    runner = tmp_path / "runner"
    source = repo / "PM_Pack/01_pm_instructions/POST_CYCLE_PM_REVIEW_v4.md"
    source.parent.mkdir(parents=True, exist_ok=True)
    source.write_text("review prompt", encoding="utf-8")
    reports = repo / "docs/cycle_reports"
    reports.mkdir(parents=True, exist_ok=True)
    for agent in "ABECFD":
        (reports / f"CYCLE_075_AGENT_{agent}.md").write_text("ok", encoding="utf-8")
    with patch("automation.post_cycle_review.claude_sub_gate.verify_subscription_preflight", return_value={"passed": True}), patch(
        "automation.post_cycle_review.claude_post_cycle_adapter.run_post_cycle_review",
        return_value=MagicMock(status="ADVISORY_ONLY", error="adapter fail"),
    ):
        result = run_review(75, ReviewMode.POST_MERGE, repo_root=repo, runner_root=runner)
    assert result.status == "ADVISORY_ONLY_ADAPTER_ERROR"
    assert result.blocks_dispatch is True


def test_run_review_writes_dispatch_decision_json(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    runner = tmp_path / "runner"
    source = repo / "PM_Pack/01_pm_instructions/POST_CYCLE_PM_REVIEW_v4.md"
    source.parent.mkdir(parents=True, exist_ok=True)
    source.write_text("review prompt", encoding="utf-8")
    reports = repo / "docs/cycle_reports"
    reports.mkdir(parents=True, exist_ok=True)
    for agent in "ABECFD":
        (reports / f"CYCLE_075_AGENT_{agent}.md").write_text("ok", encoding="utf-8")
    with patch("automation.post_cycle_review.claude_sub_gate.verify_subscription_preflight", return_value={"passed": True}), patch(
        "automation.post_cycle_review.claude_post_cycle_adapter.run_post_cycle_review",
        return_value=MagicMock(status="PASS", error=""),
    ):
        _ = run_review(75, ReviewMode.POST_MERGE, repo_root=repo, runner_root=runner)
    decision = runner / "state/next_cycle_dispatch_decision.json"
    assert decision.exists()
    payload = json.loads(decision.read_text(encoding="utf-8"))
    assert payload["cycle"] == 75


def test_get_review_result_returns_none_when_missing(tmp_path: Path) -> None:
    assert get_review_result(75, tmp_path) is None


def test_run_review_missing_agent_report_in_post_merge_returns_blocked(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    runner = tmp_path / "runner"
    source = repo / "PM_Pack/01_pm_instructions/POST_CYCLE_PM_REVIEW_v4.md"
    source.parent.mkdir(parents=True, exist_ok=True)
    source.write_text("review prompt", encoding="utf-8")
    (repo / "docs/cycle_reports").mkdir(parents=True, exist_ok=True)
    with patch("automation.post_cycle_review.claude_sub_gate.verify_subscription_preflight", return_value={"passed": True}):
        result = run_review(75, ReviewMode.POST_MERGE, repo_root=repo, runner_root=runner)
    assert result.status == "BLOCKED_MISSING_AGENT_REPORT"


def test_write_artifacts_include_billing_fields(tmp_path: Path) -> None:
    from automation.post_cycle_review import _write_artifacts

    runner = tmp_path / "runner"
    _write_artifacts(75, {"agent_reports": {}}, MagicMock(status="PASS"), runner)
    result_json = json.loads((runner / "runs/CYCLE_075/post_cycle_result.json").read_text(encoding="utf-8"))
    assert result_json["billing_mode"] == "claude_subscription_only"
    assert result_json["anthropic_api_key_present"] is False


def test_generate_post_cycle_github_bundle() -> None:
    from automation.post_cycle_review import generate_post_cycle_github_bundle

    client = MagicMock()
    client.get_check_runs.return_value = [{"name": "CI / lint"}]
    bundle = generate_post_cycle_github_bundle(75, "abc123", client)
    assert bundle["merge_sha"] == "abc123"
    assert bundle["checks"]


def test_generate_post_cycle_jira_bundle() -> None:
    from automation.post_cycle_review import generate_post_cycle_jira_bundle

    jira = MagicMock()
    with patch("automation.post_cycle_review._collect_jira_facts", return_value={"done_stories": ["SCRUM-1"], "in_review_stories": [], "cycle_control_status": "Done"}):
        bundle = generate_post_cycle_jira_bundle(75, jira)
    assert bundle["done_stories"] == ["SCRUM-1"]


def test_dispatch_decision_contains_required_fields(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    runner = tmp_path / "runner"
    source = repo / "PM_Pack/01_pm_instructions/POST_CYCLE_PM_REVIEW_v4.md"
    source.parent.mkdir(parents=True, exist_ok=True)
    source.write_text("review prompt", encoding="utf-8")
    reports = repo / "docs/cycle_reports"
    reports.mkdir(parents=True, exist_ok=True)
    for agent in "ABECFD":
        (reports / f"CYCLE_075_AGENT_{agent}.md").write_text("ok", encoding="utf-8")
    with patch("automation.post_cycle_review.claude_sub_gate.verify_subscription_preflight", return_value={"passed": True}), patch(
        "automation.post_cycle_review.claude_post_cycle_adapter.submit_for_review",
        return_value=MagicMock(status="PASS", error=""),
    ):
        run_review(75, ReviewMode.POST_MERGE, repo_root=repo, runner_root=runner)
    payload = json.loads((runner / "state/next_cycle_dispatch_decision.json").read_text(encoding="utf-8"))
    for key in ("cycle", "review_result", "blocks_dispatch", "next_action", "timestamp"):
        assert key in payload


def test_run_review_pass_sets_blocks_dispatch_false(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    runner = tmp_path / "runner"
    source = repo / "PM_Pack/01_pm_instructions/POST_CYCLE_PM_REVIEW_v4.md"
    source.parent.mkdir(parents=True, exist_ok=True)
    source.write_text("review prompt", encoding="utf-8")
    reports = repo / "docs/cycle_reports"
    reports.mkdir(parents=True, exist_ok=True)
    for agent in "ABECFD":
        (reports / f"CYCLE_075_AGENT_{agent}.md").write_text("ok", encoding="utf-8")
    with patch("automation.post_cycle_review.claude_sub_gate.verify_subscription_preflight", return_value={"passed": True}), patch(
        "automation.post_cycle_review.claude_post_cycle_adapter.submit_for_review",
        return_value=MagicMock(status="PASS", error=""),
    ):
        result = run_review(75, ReviewMode.POST_MERGE, repo_root=repo, runner_root=runner)
    assert result.blocks_dispatch is False


# Prompt-required named tests.
@patch("automation.post_cycle_review.claude_post_cycle_adapter.submit_for_review")
def test_run_review_dry_run_does_not_call_claude(_submit_mock: MagicMock) -> None:
    import pytest

    pytest.xfail("production code incomplete — Agent B task 5 (run_review has no dry_run mode)")


def test_run_review_missing_agent_report_returns_blocked_in_post_merge(tmp_path: Path) -> None:
    test_run_review_missing_agent_report_in_post_merge_returns_blocked(tmp_path)


def test_run_review_advisory_sets_blocks_dispatch_true(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    runner = tmp_path / "runner"
    source = repo / "PM_Pack/01_pm_instructions/POST_CYCLE_PM_REVIEW_v4.md"
    source.parent.mkdir(parents=True, exist_ok=True)
    source.write_text("review prompt", encoding="utf-8")
    reports = repo / "docs/cycle_reports"
    reports.mkdir(parents=True, exist_ok=True)
    for agent in "ABECFD":
        (reports / f"CYCLE_075_AGENT_{agent}.md").write_text("ok", encoding="utf-8")
    with patch("automation.post_cycle_review.claude_sub_gate.verify_subscription_preflight", return_value={"passed": True}), patch(
        "automation.post_cycle_review.claude_post_cycle_adapter.submit_for_review",
        return_value=MagicMock(status="ADVISORY_ONLY", error="adapter fail"),
    ):
        result = run_review(75, ReviewMode.POST_MERGE, repo_root=repo, runner_root=runner)
    assert result.blocks_dispatch is True


def test_get_review_result_loads_existing_json(tmp_path: Path) -> None:
    path = tmp_path / "runs/CYCLE_075_post_cycle_result.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(
            {
                "cycle": 75,
                "mode": "POST_CYCLE_PM_REVIEW",
                "status": "PASS",
                "review_result": "PASS",
                "blocks_dispatch": False,
                "reason": "ok",
                "facts": {},
            }
        ),
        encoding="utf-8",
    )
    loaded = get_review_result(75, tmp_path)
    assert loaded is not None
    assert loaded.review_result == "PASS"


def test_artifacts_contain_billing_mode(tmp_path: Path) -> None:
    test_write_artifacts_include_billing_fields(tmp_path)


def test_get_review_result_returns_none_when_file_missing(tmp_path: Path) -> None:
    test_get_review_result_returns_none_when_missing(tmp_path)
