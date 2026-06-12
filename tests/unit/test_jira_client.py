from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest
from automation.jira_client import JiraClient


def test_post_planning_comment_includes_branch() -> None:
    client = JiraClient()
    with patch("automation.jira_client.add_comment", return_value={"id": "1"}) as add_comment:
        client.post_planning_comment("SCRUM-1", 75, "cycle/075/integration", "B", ["automation/lock_manager.py"])
        body = add_comment.call_args.args[1]
        assert "cycle/075/integration" in body


def test_post_planning_comment_body_contains_cycle() -> None:
    client = JiraClient()
    with patch("automation.jira_client.add_comment", return_value={"id": "1"}) as add_comment:
        client.post_planning_comment("SCRUM-1", 75, "cycle/075/integration", "B", ["automation/lock_manager.py"])
        body = add_comment.call_args.args[1]
        assert "Cycle 75" in body


def test_post_evidence_comment_includes_subscription_billing_note() -> None:
    client = JiraClient()
    with patch("automation.jira_client.add_comment", return_value={"id": "1"}) as add_comment:
        client.post_evidence_comment("SCRUM-1", 75, 123, ["a.py"], "ruff/mypy/pytest pass", ["DoD item"])
        body = add_comment.call_args.args[1]
        assert "claude_subscription_only" in body


def test_post_evidence_comment_body_contains_pr_number() -> None:
    client = JiraClient()
    with patch("automation.jira_client.add_comment", return_value={"id": "1"}) as add_comment:
        client.post_evidence_comment("SCRUM-1", 75, 123, ["a.py"], "ruff/mypy/pytest pass", ["DoD item"])
        body = add_comment.call_args.args[1]
        assert "#123" in body


def test_check_for_secrets_raises_on_github_token() -> None:
    client = JiraClient()
    with pytest.raises(ValueError):
        client._check_for_secrets("secret " + "gh" + "p_" + "ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789")


def test_check_for_secrets_raises_on_jira_token_pattern() -> None:
    client = JiraClient()
    with pytest.raises(ValueError):
        client._check_for_secrets("ATAT" + "T3x" + "zzzzzzzzzzzzzzzzzzzzzz")


def test_check_for_secrets_passes_on_clean_text() -> None:
    client = JiraClient()
    client._check_for_secrets("normal implementation note with no credentials")


def test_transition_to_done_requires_merge_sha() -> None:
    client = JiraClient()
    with patch.object(client, "get_transitions", return_value=[{"id": "31", "name": "Done"}]), patch(
        "automation.jira_client.transition_issue"
    ) as transition:
        assert client.transition_to_done("SCRUM-1", {"ci_passed": True, "codex_resolved": True}) is False
        transition.assert_not_called()


def test_transition_to_done_requires_ci_passed_or_returns_false() -> None:
    client = JiraClient()
    with patch.object(client, "get_transitions", return_value=[{"id": "31", "name": "Done"}]), patch(
        "automation.jira_client.transition_issue"
    ) as transition:
        assert client.transition_to_done("SCRUM-1", {"merge_sha": "abc", "ci_passed": False, "codex_resolved": True}) is False
        transition.assert_not_called()


@pytest.mark.parametrize(
    ("text", "raises"),
    [
        ("normal text", False),
        ("gh" + "p_" + "ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789", True),
        ("ATAT" + "T3x" + "zzzzzzzzzzzzzzzzzzzzzz", True),
        ("xox" + "b-not-jira-but-secret", True),
        ("SCRUM-123 implementation detail", False),
    ],
)
def test_check_for_secrets_edge_cases(text: str, raises: bool) -> None:
    client = JiraClient()
    if raises:
        with pytest.raises(ValueError):
            client._check_for_secrets(text)
    else:
        client._check_for_secrets(text)


def test_post_planning_comment_calls_secret_check() -> None:
    client = JiraClient()
    with patch.object(client, "_check_for_secrets") as checker, patch(
        "automation.jira_client.add_comment", return_value={"id": "1"}
    ):
        client.post_planning_comment("SCRUM-1", 75, "cycle/075/integration", "B", ["a.py"])
        checker.assert_called_once()


def test_create_rework_ticket_sends_correct_project_key() -> None:
    client = JiraClient()
    with patch("automation.jira_client.create_issue", return_value={"key": "SCRUM-999"}) as create_issue:
        key = client.create_rework_ticket("Fix bug", "line1\nline2\nline3", 75, "B")
        assert key == "SCRUM-999"
        assert create_issue.call_args.kwargs["project_key"] == "SCRUM"


def test_create_rework_ticket_sets_bug_issue_type_and_top_errors() -> None:
    client = JiraClient()
    with patch("automation.jira_client.create_issue", return_value={"key": "SCRUM-1000"}) as create_issue:
        client.create_rework_ticket("Fix bug", "e1\ne2\ne3\ne4", 75, "B")
        kwargs = create_issue.call_args.kwargs
        assert kwargs["issue_type"] == "Bug"
        assert "Top Errors" in kwargs["description"]


# Prompt-required name aliases.
def test_post_planning_comment_body_contains_branch() -> None:
    test_post_planning_comment_includes_branch()


def test_post_evidence_comment_contains_subscription_billing_note() -> None:
    test_post_evidence_comment_includes_subscription_billing_note()


def test_check_for_secrets_raises_on_github_token_pattern() -> None:
    test_check_for_secrets_raises_on_github_token()


def test_transition_to_done_requires_merge_sha_or_returns_false() -> None:
    test_transition_to_done_requires_merge_sha()


def test_create_rework_ticket_uses_scrum_project_key() -> None:
    test_create_rework_ticket_sends_correct_project_key()


def test_transition_to_in_review_true_path() -> None:
    client = JiraClient()
    with patch.object(client, "get_transitions", return_value=[{"id": "11", "name": "In Review"}]), patch(
        "automation.jira_client.transition_issue"
    ) as transition:
        assert client.transition_to_in_review("SCRUM-1") is True
        transition.assert_called_once_with("SCRUM-1", "11")


def test_search_issues_returns_issues_list() -> None:
    client = JiraClient()
    with patch("automation.jira_client.requests.get") as req:
        resp = MagicMock()
        resp.json.return_value = {"issues": [{"key": "SCRUM-1"}]}
        resp.raise_for_status.return_value = None
        req.return_value = resp
        issues = client.search_issues("project = SCRUM", max_results=5)
    assert issues == [{"key": "SCRUM-1"}]


def test_get_transitions_returns_transition_list() -> None:
    client = JiraClient()
    with patch("automation.jira_client.requests.get") as req:
        resp = MagicMock()
        resp.json.return_value = {"transitions": [{"id": "31", "name": "Done"}]}
        resp.raise_for_status.return_value = None
        req.return_value = resp
        transitions = client.get_transitions("SCRUM-1")
    assert transitions[0]["name"] == "Done"


def test_headers_encodes_basic_auth() -> None:
    from automation.jira_client import _headers

    with patch("automation.jira_client.get_secret", side_effect=["u@example.com", "token123"]):
        headers = _headers()
    assert headers["Authorization"].startswith("Basic ")


def test_board_inventory_maps_issue_fields() -> None:
    from automation.jira_client import board_inventory

    payload = {
        "total": 1,
        "issues": [
            {
                "key": "SCRUM-1",
                "fields": {
                    "summary": "Summary",
                    "status": {"name": "In Progress"},
                    "priority": {"name": "High"},
                    "labels": ["a"],
                    "issuetype": {"name": "Story"},
                },
            }
        ],
    }
    with patch("automation.jira_client.requests.get") as req:
        resp = MagicMock()
        resp.raise_for_status.return_value = None
        resp.json.return_value = payload
        req.return_value = resp
        data = board_inventory("SCRUM")
    assert data["total"] == 1
    assert data["issues"][0]["key"] == "SCRUM-1"


def test_issue_helper_functions_make_expected_requests() -> None:
    from automation.jira_client import add_comment, create_issue, get_issue, transition_issue

    with patch("automation.jira_client.requests.get") as get_req, patch(
        "automation.jira_client.requests.post"
    ) as post_req:
        get_resp = MagicMock()
        get_resp.raise_for_status.return_value = None
        get_resp.json.return_value = {"key": "SCRUM-1"}
        get_req.return_value = get_resp
        post_resp = MagicMock()
        post_resp.raise_for_status.return_value = None
        post_resp.json.return_value = {"id": "1", "key": "SCRUM-2"}
        post_req.return_value = post_resp

        assert get_issue("SCRUM-1")["key"] == "SCRUM-1"
        assert add_comment("SCRUM-1", "body")["id"] == "1"
        transition_issue("SCRUM-1", "31")
        assert create_issue("SCRUM", "sum", "desc")["key"] == "SCRUM-2"
