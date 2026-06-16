"""Notification router that writes local log entries only."""
from __future__ import annotations

import json
<<<<<<< HEAD
from datetime import UTC, date, datetime
=======
import logging
import subprocess
from datetime import UTC, datetime
>>>>>>> origin/develop
from enum import IntEnum
from pathlib import Path
from typing import Any

RUNNER_ROOT = Path("C:/AI_Runner")
NOTIFY_LOG = RUNNER_ROOT / "reports/notifications"
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

<<<<<<< HEAD
=======
LOGGER = logging.getLogger(__name__)


>>>>>>> origin/develop
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

    _write_log(entry)
    if severity >= Severity.CRITICAL or incident_code in HUMAN_INTERRUPT_CODES:
        _write_incident(entry)


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
    NOTIFY_LOG.mkdir(parents=True, exist_ok=True)
    day = date.today().strftime("%Y%m%d")
    log_path = NOTIFY_LOG / f"{day}.log"
    with log_path.open("a", encoding="utf-8") as f:
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


def route_notification(severity: str, message: str, context: dict[str, Any]) -> None:
    """Write one notification entry to local log only."""
    entry = {
        "timestamp": datetime.now(UTC).isoformat(),
        "severity": severity,
        "message": message,
        "context": context,
    }
    _write_log(entry)


<<<<<<< HEAD
class NotificationRouter:
    """Compatibility wrapper around local notification routing."""

    def __init__(self, log_path: Path | None = None) -> None:
        self.log_path = log_path or (RUNNER_ROOT / "logs/notifications.jsonl")

    def send_local_notification(self, message: str, channel: str, severity: str) -> None:
        self.log_path.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "timestamp": datetime.now(UTC).isoformat(),
            "message": message,
            "channel": channel,
            "severity": severity,
        }
        with self.log_path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(payload) + "\n")

    def route_notification(self, severity: str, message: str, context: dict[str, Any]) -> None:
        normalized = severity.upper()
        if normalized in {"BLOCKED", "RED", "CRITICAL"}:
            channel = str(context.get("channel", "local"))
            self.send_local_notification(message=message, channel=channel, severity=normalized)
=======
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
>>>>>>> origin/develop
