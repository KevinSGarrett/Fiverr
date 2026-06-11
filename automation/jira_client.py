"""
jira_client.py — Jira REST API v3 client for board inventory, comments,
transitions, and issue creation. Read-only until dispatch is active.
All credentials from C:\\AI_Runner\\secrets\\runner.env.
"""
from __future__ import annotations

from typing import Any

import requests

from automation.config_loader import get_secret


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
