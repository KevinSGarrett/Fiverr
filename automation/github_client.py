"""
github_client.py — GitHub CLI wrapper for branch, PR, CI, and label operations.
Uses `gh` CLI (already authenticated) rather than raw API calls for simplicity.
"""
from __future__ import annotations

import json
import subprocess
from typing import Any


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


class GitHubClient:
    """Compatibility wrapper expected by legacy prompt scripts."""

    def repo_info(self) -> dict[str, Any]:
        return repo_info()

    def current_branch(self, repo_root: str = "C:/Fiverr/Fiverr") -> str:
        return current_branch(repo_root=repo_root)

    def create_branch(self, branch_name: str, base: str = "develop", repo_root: str = "C:/Fiverr/Fiverr") -> None:
        create_branch(branch_name=branch_name, base=base, repo_root=repo_root)

    def push_branch(self, branch_name: str, repo_root: str = "C:/Fiverr/Fiverr") -> None:
        push_branch(branch_name=branch_name, repo_root=repo_root)

    def create_pr(self, title: str, body: str, head: str, base: str = "develop") -> dict[str, Any]:
        return create_pr(title=title, body=body, head=head, base=base)

    def get_pr_status(self, pr_number: int) -> dict[str, Any]:
        return get_pr_status(pr_number)
