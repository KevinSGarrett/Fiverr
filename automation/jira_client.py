"""
jira_client.py — Jira REST API v3 client for board inventory, comments,
transitions, and issue creation. Read-only until dispatch is active.
All credentials from C:\\AI_Runner\\secrets\\runner.env.
"""
from __future__ import annotations

import json
import logging
import re
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import requests

from automation.config_loader import RUNNER_ENV_PATH, get_secret

LOGGER = logging.getLogger(__name__)
JIRA_FIELDS_MAP_PATH = Path("C:/Fiverr/Fiverr/PM_Pack/automation/jira_fields_map.json")


class JiraClient:
    """Jira API client with cycle automation helpers."""

    def __init__(self) -> None:
        self.base_url = _base_url()
        _validate_jira_credentials()

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

    def get_fields(self) -> list[dict[str, Any]]:
        """Return Jira field definitions from REST API."""
        url = f"{self.base_url}/rest/api/3/field"
        response = requests.get(url, headers=_headers(), timeout=30)
        response.raise_for_status()
        payload = response.json()
        return payload if isinstance(payload, list) else []

    def board_inventory(self, project: str = "SCRUM", max_results: int = 100) -> list[dict[str, Any]]:
        """Compatibility wrapper returning issue list only."""
        return board_inventory(project_key=project, max_results=max_results).get("issues", [])

    def hydrate_ac_dod(self, issue_key: str) -> dict[str, str]:
        """
        Fetch description, acceptance criteria, and definition of done for one issue.

        Missing fields are returned as empty strings.
        """
        ac_field, dod_field = _resolve_ac_dod_fields()
        field_ids = ["description"]
        for maybe_field in (ac_field, dod_field):
            if maybe_field and maybe_field not in field_ids:
                field_ids.append(maybe_field)
        url = f"{self.base_url}/rest/api/3/issue/{issue_key}"
        response = requests.get(
            url,
            headers=_headers(),
            params={"fields": ",".join(field_ids)},
            timeout=30,
        )
        response.raise_for_status()
        fields = response.json().get("fields", {})
        description_text = _extract_jira_text(fields.get("description"))
        acceptance_criteria = _extract_jira_text(fields.get(ac_field)) if ac_field else ""
        definition_of_done = _extract_jira_text(fields.get(dod_field)) if dod_field else ""
        if not _is_meaningful_text(acceptance_criteria):
            acceptance_criteria = description_text
        return {
            "description": description_text,
            "acceptance_criteria": acceptance_criteria or "",
            "definition_of_done": definition_of_done or "",
        }

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
    email, token = _validate_jira_credentials()
    creds = base64.b64encode(f"{email}:{token}".encode()).decode()
    return {
        "Authorization": f"Basic {creds}",
        "Content-Type": "application/json",
        "Accept": "application/json",
    }


def _base_url() -> str:
    return get_secret("JIRA_BASE_URL", "https://YOURDOMAIN.atlassian.net")


def _validate_jira_credentials() -> tuple[str, str]:
    email = get_secret("JIRA_EMAIL").strip()
    token = get_secret("JIRA_API_TOKEN").strip()
    if not token:
        message = (
            f"JIRA_API_TOKEN is missing. Expected in runner env: {RUNNER_ENV_PATH}. "
            "Set JIRA_API_TOKEN and retry."
        )
        LOGGER.error(message)
        raise ValueError(message)
    if not email:
        message = (
            f"JIRA_EMAIL is missing. Expected in runner env: {RUNNER_ENV_PATH}. "
            "Set JIRA_EMAIL and retry."
        )
        LOGGER.error(message)
        raise ValueError(message)
    return email, token


def board_inventory(project_key: str = "SCRUM", max_results: int = 100) -> dict[str, Any]:
    """
    Return all non-Done issues for the project, ordered by priority.

    `acceptance_criteria`: from Jira AC custom field or description fallback.
    `definition_of_done`: from Jira DoD custom field or empty string fallback.
    Both keys are always present in returned issue payloads.
    """
    url = f"{_base_url()}/rest/api/3/search/jql"
    ac_field, dod_field = _resolve_ac_dod_fields()
    requested_fields = [
        "summary",
        "status",
        "priority",
        "assignee",
        "labels",
        "issuetype",
        "description",
    ]
    for maybe_field in (ac_field, dod_field):
        if maybe_field and maybe_field not in requested_fields:
            requested_fields.append(maybe_field)
    jql = (
        f"project = {project_key} "
        "AND status != Done "
        "AND status != Cancelled "
        "ORDER BY priority ASC, created ASC"
    )
    params = {
        "jql": jql,
        "maxResults": str(max_results),
        "fields": ",".join(requested_fields),
    }
    resp = requests.get(url, headers=_headers(), params=dict(params), timeout=30)
    resp.raise_for_status()
    data = resp.json()
    issues: list[dict[str, Any]] = []
    for issue in data.get("issues", []):
        fields = issue.get("fields", {})
        description_text = _extract_jira_text(fields.get("description"))
        ac_text = _extract_jira_text(fields.get(ac_field)) if ac_field else ""
        dod_text = _extract_jira_text(fields.get(dod_field)) if dod_field else ""
        if not _is_meaningful_text(ac_text):
            ac_text = description_text
        issues.append(
            {
                "key": issue.get("key", ""),
                "summary": fields.get("summary", ""),
                "status": fields.get("status", {}).get("name", ""),
                "priority": fields.get("priority", {}).get("name", ""),
                "labels": fields.get("labels", []),
                "issuetype": fields.get("issuetype", {}).get("name", ""),
                "description": description_text,
                "acceptance_criteria": ac_text or "",
                "definition_of_done": dod_text or "",
            }
        )
    return {
        "total": data.get("total", 0),
        "issues": issues,
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


def _resolve_ac_dod_fields() -> tuple[str, str]:
    ac_field = ""
    dod_field = ""
    if JIRA_FIELDS_MAP_PATH.exists():
        try:
            payload = json.loads(JIRA_FIELDS_MAP_PATH.read_text(encoding="utf-8"))
            ac_field = str(
                payload.get("acceptance_criteria", {}).get("field_id")
                or payload.get("custom_fields", {}).get("acceptance_criteria", {}).get("id")
                or ""
            ).strip()
            dod_field = str(
                payload.get("definition_of_done", {}).get("field_id")
                or payload.get("custom_fields", {}).get("definition_of_done", {}).get("id")
                or ""
            ).strip()
        except (OSError, ValueError, TypeError):
            ac_field = ""
            dod_field = ""
    if not ac_field:
        ac_field = "customfield_10016"
    return ac_field, dod_field


def _extract_jira_text(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, str):
        return value.strip()
    if isinstance(value, int | float | bool):
        return str(value)
    if isinstance(value, list):
        return " ".join(part for item in value if (part := _extract_jira_text(item))).strip()
    if isinstance(value, dict):
        text = value.get("text")
        if isinstance(text, str):
            return text.strip()
        content = value.get("content")
        if isinstance(content, list):
            return " ".join(part for item in content if (part := _extract_jira_text(item))).strip()
    return ""


def _is_meaningful_text(value: str) -> bool:
    text = value.strip()
    if not text:
        return False
    return any(char.isalpha() for char in text)
