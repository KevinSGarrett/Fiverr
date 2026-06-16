"""
jira_client.py — Jira REST API v3 client for the Fiverr Autonomous Runner.

Key improvements over v1:
- board_inventory() paginates through ALL issues (not capped at 200)
- Fetches description field so PM intelligence can read story specs
- board_inventory_all() fetches Done stories too (for build-status analysis)
- get_project_summary() gives a full PM view: done/pending by epic + wave
All credentials from C:\\AI_Runner\\secrets\\runner.env.
"""
from __future__ import annotations

import logging
from typing import Any

import requests

from automation.config_loader import get_secret

log = logging.getLogger(__name__)

PAGE_SIZE = 100   # Jira max per page for search

# Fields to fetch for every issue — description included so PM intelligence
# can read the full story spec, not just the summary.
ISSUE_FIELDS = (
    "summary,status,priority,assignee,labels,issuetype,"
    "description,parent,components,fixVersions,created,updated"
)


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


def _search_all(jql: str, fields: str = ISSUE_FIELDS) -> list[dict[str, Any]]:
    """
    Paginate through ALL Jira search results for the given JQL.
    Returns raw issue dicts from the Jira API (with .fields).
    Never silently truncates — keeps fetching until startAt >= total.
    """
    url = f"{_base_url()}/rest/api/3/search/jql"
    all_issues: list[dict[str, Any]] = []
    start_at = 0

    while True:
        params = {
            "jql": jql,
            "startAt": str(start_at),
            "maxResults": str(PAGE_SIZE),
            "fields": fields,
        }
        resp = requests.get(url, headers=_headers(), params=params, timeout=30)
        resp.raise_for_status()
        data = resp.json()

        page = data.get("issues", [])
        all_issues.extend(page)

        total = data.get("total", 0)
        start_at += len(page)

        if start_at >= total or not page:
            break

    log.debug("_search_all: fetched %d / %d issues for JQL: %s",
              len(all_issues), total, jql[:80])
    return all_issues


def _normalise_issue(raw: dict[str, Any]) -> dict[str, Any]:
    """
    Flatten a raw Jira issue.

    Returns BOTH:
    - Top-level keys (key, summary, status, priority, labels, issuetype)
      for backward compatibility with prompt_generator.py and existing code.
    - Full `fields` dict (including description, parent, etc.)
      for pm_intelligence.py and new code that needs deeper data.
    """
    fields = raw.get("fields", {})
    description_text = _adf_to_text(fields.get("description") or {})
    status_name = fields.get("status", {}).get("name", "")
    priority_name = fields.get("priority", {}).get("name", "Medium")
    issuetype_name = fields.get("issuetype", {}).get("name", "")

    return {
        # ── Top-level (backward compatible) ─────────────────────────
        "key":      raw["key"],
        "summary":  fields.get("summary", ""),
        "status":   status_name,
        "priority": priority_name,
        "labels":   fields.get("labels", []),
        "issuetype": issuetype_name,
        # ── Full fields dict (for PM intelligence + new code) ────────
        "fields": {
            "summary":     fields.get("summary", ""),
            "status":      fields.get("status", {}),
            "priority":    fields.get("priority", {}),
            "assignee":    fields.get("assignee"),
            "labels":      fields.get("labels", []),
            "issuetype":   fields.get("issuetype", {}),
            "description": description_text,
            "parent":      fields.get("parent"),
            "components":  fields.get("components", []),
            "fixVersions": fields.get("fixVersions", []),
        },
    }


def _adf_to_text(adf: dict[str, Any]) -> str:
    """Recursively extract plain text from an Atlassian Document Format node."""
    if not adf:
        return ""
    node_type = adf.get("type", "")
    text = ""
    if node_type == "text":
        text = adf.get("text", "")
    for child in adf.get("content", []):
        child_text = _adf_to_text(child)
        if child_text:
            text = text + ("\n" if text else "") + child_text
    return text


def board_inventory(project_key: str = "SCRUM") -> dict[str, Any]:
    """
    Return ALL non-Done, non-Cancelled issues for the project.

    Paginates through every page so no issues are silently dropped.
    Returns the dict shape that prompt_generator and pm_intelligence expect:
      { "total": N, "issues": [ { "key", "fields": { ... } }, ... ] }
    """
    jql = (
        f"project = {project_key} "
        "AND status != Done "
        "AND status != Cancelled "
        "ORDER BY priority DESC, key ASC"
    )
    raw_issues = _search_all(jql)

    # Filter out [FIVERR-EX] implementation-slice stubs (auto-generated from previous cycles).
    # Real Wave 11 stories look like "[PLAYBOOK] S8.1 Gig Visual Analysis".
    import re as _re
    _ex_pattern = _re.compile(r"\[FIVERR-E\d+\]\s+Story\s+\d+:", _re.IGNORECASE)
    filtered = [r for r in raw_issues
                if not _ex_pattern.search(r.get("fields", {}).get("summary", ""))]
    if len(filtered) < len(raw_issues):
        log.debug("board_inventory: removed %d FIVERR-EX stub stories",
                  len(raw_issues) - len(filtered))

    normalised = [_normalise_issue(i) for i in filtered]
    return {"total": len(normalised), "issues": normalised}


def board_inventory_all(project_key: str = "SCRUM") -> dict[str, Any]:
    """
    Return ALL issues (including Done) for full project-state analysis.
    Used by pm_intelligence to understand what has already been built.
    """
    jql = (
        f"project = {project_key} "
        "ORDER BY key ASC"
    )
    raw_issues = _search_all(jql)
    normalised = [_normalise_issue(i) for i in raw_issues]
    return {"total": len(normalised), "issues": normalised}


def get_wave_stories(project_key: str = "SCRUM",
                     wave_label: str | None = None,
                     summary_contains: str | None = None) -> list[dict[str, Any]]:
    """
    Fetch stories for a specific wave (by label or summary keyword).
    Includes Done stories so PM intelligence can see what's already built.
    """
    conditions = [f"project = {project_key}", "issuetype = Story"]
    if wave_label:
        conditions.append(f'labels = "{wave_label}"')
    if summary_contains:
        conditions.append(f'summary ~ "{summary_contains}"')
    jql = " AND ".join(conditions) + " ORDER BY key ASC"
    raw_issues = _search_all(jql)
    return [_normalise_issue(i) for i in raw_issues]


def get_project_summary(project_key: str = "SCRUM") -> dict[str, Any]:
    """
    Return a structured PM summary of the entire project board:
    - total issues
    - done vs pending counts
    - breakdown by epic/label
    - list of pending stories with summaries (for PM intelligence context)
    """
    all_issues = board_inventory_all(project_key)["issues"]

    done_issues = [i for i in all_issues
                   if i["fields"]["status"].get("name", "").lower() == "done"]
    pending_issues = [i for i in all_issues
                      if i["fields"]["status"].get("name", "").lower() != "done"]

    # Group by labels to detect wave/epic buckets
    label_buckets: dict[str, list[str]] = {}
    for issue in pending_issues:
        for label in issue["fields"].get("labels", []):
            label_buckets.setdefault(label, []).append(issue["key"])

    return {
        "total": len(all_issues),
        "done": len(done_issues),
        "pending": len(pending_issues),
        "label_buckets": label_buckets,
        "pending_stories": [
            {
                "key": i["key"],
                "summary": i["fields"]["summary"],
                "status": i["fields"]["status"].get("name", ""),
                "labels": i["fields"].get("labels", []),
            }
            for i in pending_issues
            if i["fields"].get("issuetype", {}).get("name", "") == "Story"
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
