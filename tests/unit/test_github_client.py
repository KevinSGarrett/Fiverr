from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest
from automation.github_client import GitHubClient, GitHubClientError


def _valid_body() -> str:
    words = " ".join(["word"] * 160)
    return (
        "SCRUM-123\n\n"
        "Acceptance Criteria\n"
        "Validation\n"
        "Agent B implemented updates.\n\n"
        f"{words}"
    )


def test_validate_pr_body_passes_with_all_rules() -> None:
    client = GitHubClient()
    valid, errors = client.validate_pr_body(_valid_body())
    assert valid is True
    assert errors == []


def test_validate_pr_body_fails_missing_jira_key() -> None:
    client = GitHubClient()
    valid, errors = client.validate_pr_body(_valid_body().replace("SCRUM-123", ""))
    assert valid is False
    assert any("Jira" in error for error in errors)


def test_validate_pr_body_fails_placeholder_text() -> None:
    client = GitHubClient()
    valid, errors = client.validate_pr_body(_valid_body() + "\nTODO: fill this")
    assert valid is False
    assert any("placeholder" in error.lower() for error in errors)


def test_validate_pr_body_fails_short_body() -> None:
    client = GitHubClient()
    valid, errors = client.validate_pr_body("SCRUM-1 Acceptance Criteria Validation Agent A")
    assert valid is False
    assert any("150 words" in error for error in errors)


def test_create_pr_raises_on_error() -> None:
    client = GitHubClient()
    with patch("automation.github_client.requests.post") as post:
        post.return_value = MagicMock(status_code=422, text="unprocessable")
        with pytest.raises(GitHubClientError):
            client.create_pr("develop", "cycle/075/integration", "title", "body")


def test_add_pr_comment_raises_on_secret() -> None:
    client = GitHubClient()
    with pytest.raises(ValueError):
        client.add_pr_comment(123, "leaked " + "gh" + "p_" + "123456789012345678901234567890123456")


def test_validate_pr_body_fails_missing_validation_section() -> None:
    client = GitHubClient()
    body = _valid_body().replace("Validation", "")
    valid, errors = client.validate_pr_body(body)
    assert valid is False
    assert any("Validation" in error for error in errors)


def test_create_pr_sends_post_to_correct_url() -> None:
    client = GitHubClient()
    with patch("automation.github_client.requests.post") as post:
        post.return_value = MagicMock(status_code=201, json=lambda: {"number": 123})
        client.create_pr("develop", "cycle/075/integration", "title", _valid_body())
        assert post.call_args.args[0].endswith("/pulls")


def test_get_check_runs_returns_list_of_dicts() -> None:
    client = GitHubClient()
    with patch("automation.github_client.requests.get") as get:
        get.return_value = MagicMock(
            status_code=200,
            json=lambda: {"check_runs": [{"name": "CI / lint", "conclusion": "success", "status": "completed"}]},
        )
        runs = client.get_check_runs("abc123")
    assert isinstance(runs, list)
    assert runs[0]["name"] == "CI / lint"


def test_get_codecov_statuses_filters_to_codecov_prefix_only() -> None:
    from automation.post_cycle_review import generate_post_cycle_github_bundle

    client = MagicMock()
    client.get_check_runs.return_value = [
        {"name": "CI / lint", "conclusion": "success"},
        {"name": "codecov/project", "conclusion": "success"},
        {"name": "codecov/patch", "conclusion": "failure"},
    ]
    bundle = generate_post_cycle_github_bundle(75, "abc123", client)
    codecov = [run for run in bundle["checks"] if run["name"].startswith("codecov/")]
    assert len(codecov) == 2


@pytest.mark.parametrize(
    "body_mutator,expected_fragment",
    [
        (lambda b: b.replace("SCRUM-123", ""), "Jira"),
        (lambda b: b.replace("Acceptance Criteria", ""), "Acceptance"),
        (lambda b: b.replace("Validation", ""), "Validation"),
        (lambda b: b + "\nTODO", "placeholder"),
        (lambda _b: "too short", "150 words"),
        (lambda b: b.replace("Agent B", "Contributor"), "agent"),
    ],
)
def test_pr_body_validation_rules_parametrized(body_mutator, expected_fragment: str) -> None:
    client = GitHubClient()
    body = body_mutator(_valid_body())
    valid, errors = client.validate_pr_body(body)
    assert valid is False
    assert any(expected_fragment.lower() in error.lower() for error in errors)


# Prompt-required name aliases.
def test_validate_pr_body_passes_complete_body() -> None:
    test_validate_pr_body_passes_with_all_rules()


def test_validate_pr_body_fails_placeholder_text_todo() -> None:
    test_validate_pr_body_fails_placeholder_text()


def test_validate_pr_body_fails_short_body_under_150_words() -> None:
    test_validate_pr_body_fails_short_body()


def test_create_pr_raises_github_client_error_on_422() -> None:
    test_create_pr_raises_on_error()


def test_add_pr_comment_raises_on_secret_in_body() -> None:
    test_add_pr_comment_raises_on_secret()


def test_update_pr_body_success() -> None:
    client = GitHubClient()
    with patch("automation.github_client.requests.patch") as req:
        req.return_value = MagicMock(status_code=200, json=lambda: {"number": 1, "body": "updated"})
        payload = client.update_pr_body(1, "updated")
    assert payload["body"] == "updated"


def test_update_pr_body_raises_on_error() -> None:
    client = GitHubClient()
    with patch("automation.github_client.requests.patch") as req:
        req.return_value = MagicMock(status_code=500, text="error")
        with pytest.raises(GitHubClientError):
            client.update_pr_body(1, "updated")


def test_get_pr_reviews_raises_on_error() -> None:
    client = GitHubClient()
    with patch("automation.github_client.requests.get") as req:
        req.return_value = MagicMock(status_code=403, text="denied")
        with pytest.raises(GitHubClientError):
            client.get_pr_reviews(123)


def test_get_pr_comments_raises_on_error() -> None:
    client = GitHubClient()
    with patch("automation.github_client.requests.get") as req:
        req.return_value = MagicMock(status_code=403, text="denied")
        with pytest.raises(GitHubClientError):
            client.get_pr_comments(123)


def test_get_pr_reviews_success_states() -> None:
    client = GitHubClient()
    expected = [
        {"state": "APPROVED"},
        {"state": "CHANGES_REQUESTED"},
        {"state": "DISMISSED"},
    ]
    with patch("automation.github_client.requests.get") as req:
        req.return_value = MagicMock(status_code=200, json=lambda: expected)
        reviews = client.get_pr_reviews(123)
    assert [item["state"] for item in reviews] == ["APPROVED", "CHANGES_REQUESTED", "DISMISSED"]


def test_get_pr_comments_success() -> None:
    client = GitHubClient()
    with patch("automation.github_client.requests.get") as req:
        req.return_value = MagicMock(status_code=200, json=lambda: [{"id": 1}])
        comments = client.get_pr_comments(123)
    assert comments == [{"id": 1}]


def test_add_pr_comment_raises_on_http_error() -> None:
    client = GitHubClient()
    with patch("automation.github_client.requests.post") as req:
        req.return_value = MagicMock(status_code=403, text="forbidden")
        with pytest.raises(GitHubClientError):
            client.add_pr_comment(123, "safe comment text")


def test_create_pr_applies_labels_when_provided() -> None:
    client = GitHubClient()
    with patch("automation.github_client.requests.post") as post:
        create_resp = MagicMock(status_code=201, json=lambda: {"number": 42})
        label_resp = MagicMock(status_code=200, json=lambda: {})
        post.side_effect = [create_resp, label_resp]
        payload = client.create_pr(
            base="develop",
            head="cycle/075/integration",
            title="t",
            body=_valid_body(),
            labels=["cycle:076"],
        )
    assert payload["number"] == 42
    assert post.call_count == 2
    assert "/issues/42/labels" in post.call_args_list[1].args[0]


def test_get_check_runs_raises_on_http_error() -> None:
    client = GitHubClient()
    with patch("automation.github_client.requests.get") as req:
        req.return_value = MagicMock(status_code=401, text="unauthorized")
        with pytest.raises(GitHubClientError):
            client.get_check_runs("sha")


def test_gh_helper_raises_on_failure() -> None:
    from automation.github_client import _gh

    with patch("automation.github_client.subprocess.run") as run:
        run.return_value = MagicMock(returncode=1, stderr="boom")
        with pytest.raises(RuntimeError):
            _gh("repo", "view")


def test_repo_info_parses_json() -> None:
    from automation.github_client import repo_info

    with patch("automation.github_client._gh", return_value='{"name":"Fiverr","owner":{"login":"x"}}'):
        data = repo_info()
    assert data["name"] == "Fiverr"


def test_current_branch_reads_git_output() -> None:
    from automation.github_client import current_branch

    with patch("automation.github_client.subprocess.run") as run:
        run.return_value = MagicMock(stdout="cycle/075/integration\n")
        assert current_branch("C:/repo") == "cycle/075/integration"


def test_create_branch_runs_expected_git_commands() -> None:
    from automation.github_client import create_branch

    with patch("automation.github_client.subprocess.run") as run:
        run.return_value = MagicMock(returncode=0)
        create_branch("cycle/075/integration", base="develop", repo_root="C:/repo")
    assert run.call_count == 4
    assert run.call_args_list[0].args[0][:2] == ["git", "fetch"]


def test_push_branch_runs_git_push() -> None:
    from automation.github_client import push_branch

    with patch("automation.github_client.subprocess.run") as run:
        run.return_value = MagicMock(returncode=0)
        push_branch("cycle/075/integration", repo_root="C:/repo")
    assert run.call_args.args[0][:3] == ["git", "push", "-u"]


def test_create_pr_helper_and_status_helpers() -> None:
    from automation.github_client import create_pr, get_ci_status, get_pr_status

    with patch("automation.github_client._gh") as gh:
        gh.side_effect = [
            '{"number": 99, "url": "https://example/pr/99", "state": "OPEN"}',
            '{"number":99,"state":"OPEN","mergeable":"MERGEABLE","statusCheckRollup":[{"name":"CI / lint"}],"url":"u"}',
            '{"number":99,"state":"OPEN","mergeable":"MERGEABLE","statusCheckRollup":[{"name":"CI / lint"}],"url":"u"}',
        ]
        created = create_pr("title", "body", "head", "base")
        status = get_pr_status(99)
        ci = get_ci_status(99)

    assert created["number"] == 99
    assert status["state"] == "OPEN"
    assert ci[0]["name"] == "CI / lint"


def test_list_labels_and_ensure_labels_create_missing_only() -> None:
    from automation.github_client import ensure_labels, list_labels

    with patch("automation.github_client._gh") as gh:
        gh.side_effect = ['[{"name":"existing"}]', '[{"name":"existing"}]', ""]
        labels = list_labels()
        ensure_labels(["existing", "new-label"])

    assert labels == ["existing"]
    assert gh.call_args_list[-1].args[0] == "label"
