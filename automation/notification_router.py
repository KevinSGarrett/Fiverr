"""
notification_router.py — Severity-based notification routing (OPS-010, OPS-011).

Routes INFO/SUCCESS/WARNING/BLOCKED/CRITICAL to configured destinations:
  - Slack webhook (if SLACK_WEBHOOK_URL set in runner.env)
  - GitHub issue (if severity >= BLOCKED)
  - Log file (always)

Human interruption rules (OPS-012):
  Only interrupt for: auth expiry, model reverify, max repair, destructive/cost/security,
  machine offline, main release, contradictory state.
"""
from __future__ import annotations

import json
import logging
import subprocess
from datetime import UTC, datetime
from enum import IntEnum
from pathlib import Path
from typing import Any

RUNNER_ROOT = Path("C:/AI_Runner")
NOTIFY_LOG = RUNNER_ROOT / "logs/notifications.log"
INCIDENTS_DIR = RUNNER_ROOT / "logs/incidents"

# Severity levels — only interrupt human for BLOCKED and above
class Severity(IntEnum):
    INFO      = 0
    SUCCESS   = 1
    WARNING   = 2
    BLOCKED   = 3   # Interrupts human
    CRITICAL  = 4   # Interrupts human + writes incident

HUMAN_INTERRUPT_THRESHOLD = Severity.BLOCKED

# Incident codes that always require human attention
HUMAN_INTERRUPT_CODES = {
    "AUTH_EXPIRED", "AUTH_REQUIRED",
    "MODEL_REVERIFICATION_REQUIRED",
    "MAX_REPAIR_EXHAUSTED",
    "DESTRUCTIVE_ACTION_BLOCKED",
    "MAIN_MERGE_BLOCKED",
    "MACHINE_OFFLINE",
    "CONTRADICTORY_STATE",
    "BLOCKED_CLAUDE_API_KEY_PRESENT",
    "CLAUDE_SUBSCRIPTION_LIMIT_REACHED",
}

LOGGER = logging.getLogger(__name__)


def notify(severity: Severity | str, title: str, body: str,
           incident_code: str = "", cycle: int | None = None) -> None:
    """Route notification to appropriate destinations based on severity."""
    if isinstance(severity, str):
        severity = Severity[severity.upper()]

    ts = datetime.now(UTC).isoformat()
    entry = {
        "ts": ts, "severity": severity.name, "title": title,
        "body": body[:500], "incident_code": incident_code, "cycle": cycle,
    }

    # Always log
    _write_log(entry)

    # Write incident file for CRITICAL or known interrupt codes
    if severity >= Severity.CRITICAL or incident_code in HUMAN_INTERRUPT_CODES:
        _write_incident(entry)

    # Slack notification
    _try_slack(severity, title, body, incident_code)

    # GitHub issue for BLOCKED+
    if severity >= Severity.BLOCKED and incident_code:
        _try_github_issue(severity, title, body, incident_code, cycle)


def notify_info(title: str, body: str = "", cycle: int | None = None) -> None:
    notify(Severity.INFO, title, body, cycle=cycle)


def notify_success(title: str, body: str = "", cycle: int | None = None) -> None:
    notify(Severity.SUCCESS, title, body, cycle=cycle)


def notify_warning(title: str, body: str = "", incident_code: str = "",
                   cycle: int | None = None) -> None:
    notify(Severity.WARNING, title, body, incident_code, cycle)


def notify_blocked(title: str, body: str = "", incident_code: str = "",
                   cycle: int | None = None) -> None:
    notify(Severity.BLOCKED, title, body, incident_code, cycle)


def notify_critical(title: str, body: str = "", incident_code: str = "",
                    cycle: int | None = None) -> None:
    notify(Severity.CRITICAL, title, body, incident_code, cycle)


def _write_log(entry: dict) -> None:
    NOTIFY_LOG.parent.mkdir(parents=True, exist_ok=True)
    with NOTIFY_LOG.open("a", encoding="utf-8") as f:
        f.write(json.dumps(entry) + "\n")


def _write_incident(entry: dict) -> None:
    INCIDENTS_DIR.mkdir(parents=True, exist_ok=True)
    ts = entry["ts"].replace(":", "-").replace("+", "")[:19]
    code = entry.get("incident_code") or entry["severity"]
    path = INCIDENTS_DIR / f"INCIDENT_{ts}_{code}.md"
    lines = [
        f"# Incident: {entry['title']}",
        f"Time     : {entry['ts']}",
        f"Severity : {entry['severity']}",
        f"Code     : {entry.get('incident_code', 'N/A')}",
        f"Cycle    : {entry.get('cycle', 'N/A')}",
        "",
        entry.get("body", ""),
    ]
    path.write_text("\n".join(lines), encoding="utf-8")


def _try_slack(severity: Severity, title: str, body: str,
               incident_code: str) -> None:
    """Post to Slack webhook if configured. Silent failure if not set."""
    try:
        import urllib.request

        from automation.config_loader import get_secret
        webhook = get_secret("SLACK_WEBHOOK_URL", "")
        if not webhook:
            return
        emoji = {
            Severity.INFO: ":information_source:",
            Severity.SUCCESS: ":white_check_mark:",
            Severity.WARNING: ":warning:",
            Severity.BLOCKED: ":no_entry:",
            Severity.CRITICAL: ":rotating_light:",
        }.get(severity, ":bell:")
        text = f"{emoji} *[{severity.name}]* {title}"
        if body:
            text += f"\n{body[:300]}"
        if incident_code:
            text += f"\nCode: `{incident_code}`"
        payload = json.dumps({"text": text}).encode()
        req = urllib.request.Request(webhook, data=payload,
                                     headers={"Content-Type": "application/json"})
        urllib.request.urlopen(req, timeout=5)
    except Exception:
        pass  # Notification is best-effort


def _try_github_issue(severity: Severity, title: str, body: str,
                      incident_code: str, cycle: int | None) -> None:
    """Open a GitHub issue for BLOCKED/CRITICAL incidents."""
    try:
        issue_title = f"[Runner {severity.name}] {title}"
        if incident_code:
            issue_title += f" ({incident_code})"
        issue_body = body or "No details provided."
        if cycle:
            issue_body += f"\n\nCycle: {cycle}"
        subprocess.run(
            ["gh", "issue", "create",
             "--repo", "KevinSGarrett/Fiverr",
             "--title", issue_title,
             "--body", issue_body,
             "--label", "ai-runner"],
            capture_output=True, timeout=15
        )
    except Exception:
        pass


class NotificationRouter:
    """Notification adapter for severity-based Slack routing."""

    def send_slack_notification(self, message: str, channel: str, severity: str) -> None:
        try:
            import requests

            from automation.config_loader import get_secret

            webhook_url = get_secret("SLACK_WEBHOOK_URL", default="")
            if not webhook_url:
                LOGGER.info("SLACK_WEBHOOK_NOT_CONFIGURED — skipping")
                return
            _ = channel
            requests.post(
                webhook_url,
                json={"text": f"[{severity}] {message}"},
                timeout=5,
            )
        except Exception as exc:  # noqa: BLE001
            LOGGER.warning("Slack notification failed: %s", exc)

    def route_notification(self, severity: str, message: str, context: dict[str, Any]) -> None:
        normalized = severity.upper().strip()
        if normalized in {"BLOCKED", "RED", "CRITICAL"}:
            channel = str(context.get("channel", "#ai-runner-alerts"))
            self.send_slack_notification(message, channel, normalized)
