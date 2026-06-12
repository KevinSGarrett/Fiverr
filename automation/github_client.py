"""
github_client.py — GitHub CLI wrapper for branch, PR, CI, and label operations.
Uses `gh` CLI (already authenticated) rather than raw API calls for simplicity.
"""
from __future__ import annotations

import json
import re
import subprocess
from typing import Any

import requests

from automation.config_loader import get_secret


class GitHubClientError(Exception):
    """Raised when a GitHub API request fails."""


class GitHubClient:
    """GitHub REST client for PR and CI operations."""

    def __init__(self) -> None:
        self._token = get_secret("GH_AUTOMATION_TOKEN")
        self._base_url = "https://api.github.com/repos/KevinSGarrett/Fiverr"
        self._headers = {
            "Accept": "application/vnd.github+json",
            "Authorization": f"Bearer {self._token}",
            "X-GitHub-Api-Version": "2022-11-28",
        }

    def create_pr(
        self,
        base: str,
        head: str,
        title: str,
        body: str,
        labels: list[str] | None = None,
        draft: bool = False,
    ) -> dict[str, Any]:
        response = requests.post(
            f"{self._base_url}/pulls",
            headers=self._headers,
            json={"base": base, "head": head, "title": title, "body": body, "draft": draft},
            timeout=30,
        )
        if response.status_code != 201:
            raise GitHubClientError(f"PR creation failed: {response.status_code} {response.text}")
        payload = response.json()
        if labels:
            requests.post(
                f"{self._base_url}/issues/{payload['number']}/labels",
                headers=self._headers,
                json={"labels": labels},
                timeout=30,
            )
        return payload

    def update_pr_body(self, pr_number: int, body: str) -> dict[str, Any]:
        response = requests.patch(
            f"{self._base_url}/pulls/{pr_number}",
            headers=self._headers,
            json={"body": body},
            timeout=30,
        )
        if response.status_code >= 400:
            raise GitHubClientError(f"PR update failed: {response.status_code} {response.text}")
        return response.json()

    def add_pr_comment(self, pr_number: int, comment: str) -> dict[str, Any]:
        self._check_comment_for_secrets(comment)
        response = requests.post(
            f"{self._base_url}/issues/{pr_number}/comments",
            headers=self._headers,
            json={"body": comment},
            timeout=30,
        )
        if response.status_code >= 400:
            raise GitHubClientError(f"Comment failed: {response.status_code} {response.text}")
        return response.json()

    def validate_pr_body(self, body: str) -> tuple[bool, list[str]]:
        errors: list[str] = []
        if not re.search(r"SCRUM-\d+", body):
            errors.append("Missing Jira story key (SCRUM-###).")
        if "Acceptance Criteria" not in body and "AC:" not in body:
            errors.append("Missing Acceptance Criteria section.")
        if "Validation" not in body:
            errors.append("Missing Validation section.")
        if re.search(r"\b(TODO|FILL IN|TBD)\b", body, flags=re.IGNORECASE):
            errors.append("Contains placeholder text.")
        if not any(agent in body for agent in ("Agent A", "Agent B", "Agent C", "Agent D", "Agent E", "Agent F")):
            errors.append("Must mention at least one agent.")
        if len(body.split()) < 150:
            errors.append("Body must contain at least 150 words.")
        return len(errors) == 0, errors

    def get_check_runs(self, sha: str) -> list[dict[str, Any]]:
        response = requests.get(
            f"{self._base_url}/commits/{sha}/check-runs",
            headers=self._headers,
            timeout=30,
        )
        if response.status_code >= 400:
            raise GitHubClientError(
                f"Check runs failed: {response.status_code} {response.text}"
            )
        runs = response.json().get("check_runs", [])
        return [
            {
                "name": run.get("name", ""),
                "conclusion": run.get("conclusion"),
                "status": run.get("status"),
                "html_url": run.get("html_url", ""),
            }
            for run in runs
        ]

    def get_pr_reviews(self, pr_number: int) -> list[dict[str, Any]]:
        response = requests.get(
            f"{self._base_url}/pulls/{pr_number}/reviews",
            headers=self._headers,
            timeout=30,
        )
        if response.status_code >= 400:
            raise GitHubClientError(f"Reviews failed: {response.status_code} {response.text}")
        return response.json()

    def get_pr_comments(self, pr_number: int) -> list[dict[str, Any]]:
        response = requests.get(
            f"{self._base_url}/issues/{pr_number}/comments",
            headers=self._headers,
            timeout=30,
        )
        if response.status_code >= 400:
            raise GitHubClientError(f"Comments failed: {response.status_code} {response.text}")
        return response.json()

    def _check_comment_for_secrets(self, comment: str) -> None:
        patterns = (
            "gh" + "p_",
            "ATAT" + "T3x",
            "sk-" + "ant-",
            "xox" + "b-",
        )
        for pattern in patterns:
            if pattern in comment:
                raise ValueError(f"Comment contains potential secret: {pattern}")


def _gh(*args: str, capture: bool = True) -> str:
    result = subprocess.run(
        ["gh", *args],
        capture_output=capture,
        text=True,
        check=False,
    )
    if result.returncode != 0 and capture:
        raise RuntimeError(f"gh {' '.join(args)} failed: {result.stderr.strip()}")
    return result.stdout.strip() if capture else ""


def repo_info() -> dict[str, Any]:
    raw = _gh("repo", "view", "KevinSGarrett/Fiverr", "--json",
              "name,owner,defaultBranchRef,isPrivate")
    return json.loads(raw)


def current_branch(repo_root: str = "C:/Fiverr/Fiverr") -> str:
    result = subprocess.run(
        ["git", "branch", "--show-current"],
        cwd=repo_root, capture_output=True, text=True
    )
    return result.stdout.strip()


def create_branch(branch_name: str, base: str = "develop",
                  repo_root: str = "C:/Fiverr/Fiverr") -> None:
    subprocess.run(
        ["git", "fetch", "--all", "--prune"],
        cwd=repo_root, check=True, capture_output=True
    )
    subprocess.run(
        ["git", "checkout", base],
        cwd=repo_root, check=True, capture_output=True
    )
    subprocess.run(
        ["git", "pull", "origin", base],
        cwd=repo_root, check=True, capture_output=True
    )
    subprocess.run(
        ["git", "checkout", "-b", branch_name],
        cwd=repo_root, check=True, capture_output=True
    )


def push_branch(branch_name: str, repo_root: str = "C:/Fiverr/Fiverr") -> None:
    subprocess.run(
        ["git", "push", "-u", "origin", branch_name],
        cwd=repo_root, check=True, capture_output=True
    )


def create_pr(title: str, body: str, head: str,
              base: str = "develop") -> dict[str, Any]:
    raw = _gh("pr", "create",
              "--title", title,
              "--body", body,
              "--head", head,
              "--base", base,
              "--json", "number,url,state")
    return json.loads(raw)


def get_pr_status(pr_number: int) -> dict[str, Any]:
    raw = _gh("pr", "view", str(pr_number),
              "--json", "number,state,mergeable,statusCheckRollup,url")
    return json.loads(raw)


def get_ci_status(pr_number: int) -> list[dict[str, Any]]:
    data = get_pr_status(pr_number)
    return data.get("statusCheckRollup", [])


def list_labels() -> list[str]:
    raw = _gh("label", "list", "--json", "name")
    return [item["name"] for item in json.loads(raw)]


def ensure_labels(labels: list[str]) -> None:
    existing = set(list_labels())
    for label in labels:
        if label not in existing:
            _gh("label", "create", label, "--color", "0075ca", capture=False)
