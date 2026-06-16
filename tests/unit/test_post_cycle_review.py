from __future__ import annotations

<<<<<<< HEAD
import json
=======
>>>>>>> origin/develop
from pathlib import Path

from automation.post_cycle_review import JiraAuthError, PostCycleReview

<<<<<<< HEAD
CYCLE = 81

=======
>>>>>>> origin/develop

def test_verify_github_facts_returns_dict_with_merged_prs(tmp_path: Path, monkeypatch) -> None:
    class _Result:
        returncode = 0
        stdout = '[{"number": 1, "title": "PR", "mergedAt": "2026-06-15T00:00:00Z"}]'
        stderr = ""

    monkeypatch.setattr("automation.post_cycle_review.subprocess.run", lambda *args, **kwargs: _Result())
<<<<<<< HEAD
    review = PostCycleReview(cycle=CYCLE)
=======
    review = PostCycleReview(cycle=81)
>>>>>>> origin/develop
    review.current_run_dir = tmp_path
    facts = review._verify_github_facts()
    assert "merged_prs" in facts
    assert isinstance(facts["merged_prs"], list)
<<<<<<< HEAD
    assert "collected_at" in facts
    saved_payload = json.loads((tmp_path / "github_verification.json").read_text(encoding="utf-8"))
    assert "merged_prs" in saved_payload
=======
>>>>>>> origin/develop


def test_verify_github_facts_gh_unavailable_returns_error_dict(
    tmp_path: Path, monkeypatch
) -> None:
<<<<<<< HEAD
    def _raise(*_: object, **__: object) -> None:
        raise FileNotFoundError("gh missing")

    monkeypatch.setattr("automation.post_cycle_review.subprocess.run", _raise)
    review = PostCycleReview(cycle=CYCLE)
=======
    def _raise(*args, **kwargs):
        _ = args, kwargs
        raise FileNotFoundError("gh missing")

    monkeypatch.setattr("automation.post_cycle_review.subprocess.run", _raise)
    review = PostCycleReview(cycle=81)
>>>>>>> origin/develop
    review.current_run_dir = tmp_path
    facts = review._verify_github_facts()
    assert "error" in facts


def test_verify_jira_facts_auth_fail_returns_error_dict(tmp_path: Path) -> None:
    class _JiraClient:
<<<<<<< HEAD
        def search_issues(self, jql: str) -> list[dict[str, object]]:
            _ = jql
            raise JiraAuthError("JIRA_AUTH_FAILED")

    review = PostCycleReview(cycle=CYCLE, jira_client=_JiraClient())
=======
        def search_issues(self, jql: str):  # noqa: ANN201
            _ = jql
            raise JiraAuthError("JIRA_AUTH_FAILED")

    review = PostCycleReview(cycle=81, jira_client=_JiraClient())
>>>>>>> origin/develop
    review.current_run_dir = tmp_path
    facts = review._verify_jira_facts()
    assert "auth_error" in facts


def test_collect_facts_calls_both_verify_methods(monkeypatch) -> None:
<<<<<<< HEAD
    review = PostCycleReview(cycle=CYCLE)
=======
    review = PostCycleReview(cycle=81)
>>>>>>> origin/develop
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
<<<<<<< HEAD


def test_verify_jira_facts_returns_done_story_keys(tmp_path: Path) -> None:
    class _JiraClient:
        def search_issues(self, jql: str) -> list[dict[str, object]]:
            _ = jql
            return [
                {"key": "SCRUM-1"},
                {"key": "SCRUM-2"},
            ]

    review = PostCycleReview(cycle=CYCLE, jira_client=_JiraClient())
    review.current_run_dir = tmp_path
    facts = review._verify_jira_facts()
    assert facts["done_stories"] == ["SCRUM-1", "SCRUM-2"]
    assert "collected_at" in facts
    saved_payload = json.loads((tmp_path / "jira_verification.json").read_text(encoding="utf-8"))
    assert saved_payload["done_stories"] == ["SCRUM-1", "SCRUM-2"]
=======
>>>>>>> origin/develop
