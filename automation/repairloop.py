"""Compatibility repair loop API expected by legacy prompt scripts."""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from automation.notification_router import notify_blocked

REPORTS_DIR = Path("C:/AI_Runner/reports/incidents")


class RepairLoop:
    """Simple compatibility class wrapping repair trigger handling."""

    def handle(self, trigger_path: str) -> dict[str, Any]:
        path = Path(trigger_path)
        if not path.exists():
            return {"status": "ERROR", "reason": f"trigger not found: {trigger_path}"}

        payload = json.loads(path.read_text(encoding="utf-8"))
        trigger = payload.get("trigger", "UNKNOWN")
        cycle = int(payload.get("cycle", 0) or 0)

        planned_actions = []
        if trigger == "LINT_FAIL":
            planned_actions = [
                "run targeted ruff check for failed module",
                "re-run unit tests for affected module",
                "open blocked notification if failure persists",
            ]
            notify_blocked(
                title="Repair loop trigger: LINT_FAIL",
                body=f"cycle={cycle} module={payload.get('module', '')}",
                incident_code="REPAIR_LINT_FAIL",
                cycle=cycle or None,
            )
            status = "PLANNED"
        else:
            planned_actions = ["manual triage required"]
            status = "UNKNOWN_TRIGGER"

        incident = {
            "timestamp": datetime.now(UTC).isoformat(),
            "trigger": trigger,
            "cycle": cycle,
            "module": payload.get("module"),
            "planned_actions": planned_actions,
            "status": status,
        }
        REPORTS_DIR.mkdir(parents=True, exist_ok=True)
        incident_path = REPORTS_DIR / f"repair_incident_{datetime.now(UTC).strftime('%Y%m%dT%H%M%S')}.json"
        incident_path.write_text(json.dumps(incident, indent=2), encoding="utf-8")

        return {"status": status, "incident_path": str(incident_path), "planned_actions": planned_actions}
