from __future__ import annotations

from pathlib import Path

from automation.post_cycle_review import JiraAuthError, PostCycleReview


def test_verify_github_facts_returns_dict_with_merged_prs(tmp_path: Path, monkeypatch) -> None:
    class _Result:
        returncode = 0
        stdout = '[{"number": 1, "title": "PR", "mergedAt": "2026-06-15T00:00:00Z"}]'
        stderr = ""

    monkeypatch.setattr("automation.post_cycle_review.subprocess.run", lambda *args, **kwargs: _Result())
    review = PostCycleReview(cycle=81)
    review.current_run_dir = tmp_path
    facts = review._verify_github_facts()
    assert "merged_prs" in facts
    assert isinstance(facts["merged_prs"], list)


def test_verify_github_facts_gh_unavailable_returns_error_dict(
    tmp_path: Path, monkeypatch
) -> None:
    def _raise(*args, **kwargs):
        _ = args, kwargs
        raise FileNotFoundError("gh missing")

    monkeypatch.setattr("automation.post_cycle_review.subprocess.run", _raise)
    review = PostCycleReview(cycle=81)
    review.current_run_dir = tmp_path
    facts = review._verify_github_facts()
    assert "error" in facts


def test_verify_jira_facts_auth_fail_returns_error_dict(tmp_path: Path) -> None:
    class _JiraClient:
        def search_issues(self, jql: str):  # noqa: ANN201
            _ = jql
            raise JiraAuthError("JIRA_AUTH_FAILED")

    review = PostCycleReview(cycle=81, jira_client=_JiraClient())
    review.current_run_dir = tmp_path
    facts = review._verify_jira_facts()
    assert "auth_error" in facts


def test_collect_facts_calls_both_verify_methods(monkeypatch) -> None:
    review = PostCycleReview(cycle=81)
    calls = {"github": 0, "jira": 0}

    def _github() -> dict[str, object]:
        calls["github"] += 1
        return {"merged_prs": []}

    def _jira() -> dict[str, object]:
        calls["jira"] += 1
        return {"done_stories": []}

    monkeypatch.setattr(review, "_verify_github_facts", _github)
    monkeypatch.setattr(review, "_verify_jira_facts", _jira)
    facts = review.collect_facts()
    assert calls["github"] == 1
    assert calls["jira"] == 1
    assert set(facts) == {"github", "jira"}
