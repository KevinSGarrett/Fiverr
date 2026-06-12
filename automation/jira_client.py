"""
jira_client.py — Jira REST API v3 client for board inventory, comments,
transitions, and issue creation. Read-only until dispatch is active.
All credentials from C:\\AI_Runner\\secrets\\runner.env.
"""
from __future__ import annotations

import re
from datetime import UTC, datetime
from typing import Any

import requests

from automation.config_loader import get_secret


class JiraClient:
    """Jira API client with cycle automation helpers."""

    def __init__(self) -> None:
        self.base_url = _base_url()

    def post_planning_comment(
        self,
        issue_key: str,
        cycle: int,
        branch: str,
        agent: str,
        planned_files: list[str],
    ) -> str:
        planned_at = datetime.now(UTC).isoformat()
        body = (
            f"*Cycle {cycle} Planning Note*\n"
            f"- Branch: {branch}\n"
            f"- Agent: {agent}\n"
            f"- Planned scope: {', '.join(planned_files[:10])}\n"
            f"- Planned at: {planned_at}\n"
            "- Status: PLANNED"
        )
        self._check_for_secrets(body)
        response = add_comment(issue_key, body)
        return str(response.get("id", ""))

    def post_evidence_comment(
        self,
        issue_key: str,
        cycle: int,
        pr_number: int,
        files_changed: list[str],
        validation_summary: str,
        dod_items: list[str],
    ) -> str:
        items = "\n".join(f"  - {item}" for item in dod_items)
        body = (
            f"*Cycle {cycle} Implementation Evidence*\n"
            f"- PR: #{pr_number}\n"
            f"- Files changed: {len(files_changed)} files\n"
            f"- Validation: {validation_summary}\n"
            "- AC/DoD addressed:\n"
            f"{items}\n"
            "- Subscription billing: claude_subscription_only (no API key)"
        )
        self._check_for_secrets(body)
        response = add_comment(issue_key, body)
        return str(response.get("id", ""))

    def transition_to_in_review(self, issue_key: str) -> bool:
        transitions = self.get_transitions(issue_key)
        match = next((t for t in transitions if t.get("name") == "In Review"), None)
        if not match:
            return False
        transition_issue(issue_key, str(match["id"]))
        return True

    def transition_to_done(self, issue_key: str, dod_evidence: dict[str, Any]) -> bool:
        if not dod_evidence.get("merge_sha") or not dod_evidence.get("ci_passed") or not dod_evidence.get("codex_resolved"):
            return False
        transitions = self.get_transitions(issue_key)
        match = next((t for t in transitions if t.get("name") == "Done"), None)
        if not match:
            return False
        transition_issue(issue_key, str(match["id"]))
        return True

    def create_rework_ticket(self, summary: str, description: str, cycle: int, agent: str) -> str:
        description_lines = description.splitlines()
        top_errors = "\n".join(description_lines[:3])
        desc = (
            f"{description}\n\n"
            f"Cycle: {cycle}\n"
            f"Agent: {agent}\n"
            f"Top Errors:\n{top_errors}\n"
        )
        issue = create_issue(
            project_key="SCRUM",
            summary=summary,
            description=desc,
            issue_type="Bug",
            labels=[f"cycle:{cycle:03d}", f"agent:{agent}"],
        )
        return str(issue.get("key", ""))

    def search_issues(self, jql: str, max_results: int = 50) -> list[dict[str, Any]]:
        url = f"{self.base_url}/rest/api/3/search/jql"
        response = requests.get(
            url,
            headers=_headers(),
            params={"jql": jql, "maxResults": str(max_results), "fields": "summary,status"},
            timeout=30,
        )
        response.raise_for_status()
        return response.json().get("issues", [])

    def get_transitions(self, issue_key: str) -> list[dict[str, Any]]:
        url = f"{self.base_url}/rest/api/3/issue/{issue_key}/transitions"
        response = requests.get(url, headers=_headers(), timeout=30)
        response.raise_for_status()
        return response.json().get("transitions", [])

    def _check_for_secrets(self, text: str) -> None:
        patterns = [
            r"gh" + r"p_[A-Za-z0-9]{36}",
            r"ATAT" + r"T3x",
            r"sk-" + r"ant-",
            r"xox" + r"b-",
            r"[A-Z]{8,}[A-Za-z0-9]{24,}",
        ]
        for pattern in patterns:
            match = re.search(pattern, text)
            if match:
                raise ValueError(f"Comment contains potential secret at position {match.start()}")


def _headers() -> dict[str, str]:
    import base64
    email = get_secret("JIRA_EMAIL")
    token = get_secret("JIRA_API_TOKEN")
    creds = base64.b64encode(f"{email}:{token}".encode()).decode()
    return {
        "Authorization": f"Basic {creds}",
        "Content-Type": "application/json",
        "Accept": "application/json",
    }


def _base_url() -> str:
    return get_secret("JIRA_BASE_URL", "https://YOURDOMAIN.atlassian.net")


def board_inventory(project_key: str = "SCRUM") -> dict[str, Any]:
    """Return all non-Done issues for the project, ordered by priority."""
    url = f"{_base_url()}/rest/api/3/search/jql"
    jql = (
        f"project = {project_key} "
        "AND status != Done "
        "AND status != Cancelled "
        "ORDER BY priority ASC, created ASC"
    )
    params = {
        "jql": jql,
        "maxResults": "100",
        "fields": "summary,status,priority,assignee,labels,issuetype",
    }
    resp = requests.get(url, headers=_headers(), params=dict(params), timeout=30)
    resp.raise_for_status()
    data = resp.json()
    return {
        "total": data.get("total", 0),
        "issues": [
            {
                "key": i["key"],
                "summary": i["fields"]["summary"],
                "status": i["fields"]["status"]["name"],
                "priority": i["fields"].get("priority", {}).get("name", ""),
                "labels": i["fields"].get("labels", []),
                "issuetype": i["fields"]["issuetype"]["name"],
            }
            for i in data.get("issues", [])
        ],
    }


def get_issue(issue_key: str) -> dict[str, Any]:
    url = f"{_base_url()}/rest/api/3/issue/{issue_key}"
    resp = requests.get(url, headers=_headers(), timeout=30)
    resp.raise_for_status()
    return resp.json()


def add_comment(issue_key: str, body: str) -> dict[str, Any]:
    url = f"{_base_url()}/rest/api/3/issue/{issue_key}/comment"
    payload: Any = {"body": {"type": "doc", "version": 1, "content": [
        {"type": "paragraph", "content": [{"type": "text", "text": body}]}
    ]}}
    resp = requests.post(url, headers=_headers(), json=payload, timeout=30)
    resp.raise_for_status()
    return resp.json()


def transition_issue(issue_key: str, transition_id: str) -> None:
    url = f"{_base_url()}/rest/api/3/issue/{issue_key}/transitions"
    payload = {"transition": {"id": transition_id}}
    resp = requests.post(url, headers=_headers(), json=payload, timeout=30)
    resp.raise_for_status()


def create_issue(project_key: str, summary: str, description: str,
                 issue_type: str = "Bug", labels: list[str] | None = None) -> dict[str, Any]:
    url = f"{_base_url()}/rest/api/3/issue"
    payload: dict[str, Any] = {
        "fields": {
            "project": {"key": project_key},
            "summary": summary,
            "issuetype": {"name": issue_type},
            "description": {
                "type": "doc", "version": 1,
                "content": [{"type": "paragraph", "content": [{"type": "text", "text": description}]}]
            },
        }
    }
    if labels:
        payload["fields"]["labels"] = labels
    resp = requests.post(url, headers=_headers(), json=payload, timeout=30)
    resp.raise_for_status()
    return resp.json()
