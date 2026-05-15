"""Deterministic alert contracts and rule helpers for dashboard readiness."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

VALID_ALERT_SEVERITIES = frozenset({"info", "warning", "error", "critical"})


@dataclass(frozen=True, slots=True)
class DashboardAlert:
    """Stable dashboard alert contract for export and UI consumers."""

    id: str
    type: str
    severity: str
    title: str
    explanation: str
    source_context: dict[str, Any]
    recommended_action: str
    jira_key: str
    dismissible: bool

    def as_dict(self) -> dict[str, Any]:
        severity = self.severity if self.severity in VALID_ALERT_SEVERITIES else "warning"
        jira_key = self.jira_key.strip() or "UNMAPPED"
        return {
            "id": self.id,
            "type": self.type,
            "severity": severity,
            "title": self.title,
            "explanation": self.explanation,
            "source_context": dict(self.source_context),
            "recommended_action": self.recommended_action,
            "jira_key": jira_key,
            "dismissible": self.dismissible,
        }


def build_dashboard_alerts(
    *,
    opportunities: list[dict[str, Any]] | None = None,
    run_history: list[dict[str, Any]] | None = None,
    source_freshness: list[dict[str, Any]] | None = None,
    phase2_smoke: dict[str, Any] | None = None,
    cost_risk: dict[str, Any] | None = None,
    quality_risk: dict[str, Any] | None = None,
    data_hygiene_risk: dict[str, Any] | None = None,
) -> list[dict[str, Any]]:
    """Return deterministic alert rows from fixture-safe signals."""
    alerts: list[DashboardAlert] = []
    alerts.extend(_build_opportunity_alerts(opportunities or []))
    alerts.extend(_build_run_alerts(run_history or [], phase2_smoke=phase2_smoke or {}))
    alerts.extend(_build_freshness_alerts(source_freshness or []))
    alerts.extend(_build_risk_placeholder_alerts(cost_risk=cost_risk, quality_risk=quality_risk, data_hygiene_risk=data_hygiene_risk))
    return [alert.as_dict() for alert in alerts]


def _build_opportunity_alerts(opportunities: list[dict[str, Any]]) -> list[DashboardAlert]:
    if not opportunities:
        return [
            DashboardAlert(
                id="opportunity-missing-evidence",
                type="opportunity_missing_evidence",
                severity="warning",
                title="No Opportunity Evidence",
                explanation="Opportunity alerts are running in sparse-data mode because no records were provided.",
                source_context={"source": "opportunities", "record_count": 0},
                recommended_action="Run fixture-backed opportunity analysis and refresh dashboard payloads.",
                jira_key="SCRUM-227",
                dismissible=False,
            )
        ]

    alerts: list[DashboardAlert] = []
    for row in opportunities:
        row_id = str(row.get("id", "unknown")).strip() or "unknown"
        score = _to_float(row.get("score"))
        confidence = _to_float(row.get("confidence"))
        title = str(row.get("opportunity", row_id)).strip() or row_id

        if score is not None and confidence is not None and score >= 85 and confidence >= 0.80:
            alerts.append(
                DashboardAlert(
                    id=f"opportunity-high-potential-{row_id}",
                    type="high_potential_opportunity",
                    severity="info",
                    title=f"High-Potential Opportunity: {title}",
                    explanation=f"Score {score:.1f} and confidence {confidence:.2f} indicate a high-value opportunity.",
                    source_context={"source": "opportunities", "opportunity_id": row_id},
                    recommended_action="Prioritize this opportunity in recommendations and export highlights.",
                    jira_key="SCRUM-214",
                    dismissible=True,
                )
            )
        if score is not None and confidence is not None and score >= 70 and confidence < 0.65:
            alerts.append(
                DashboardAlert(
                    id=f"opportunity-low-confidence-{row_id}",
                    type="low_confidence_opportunity",
                    severity="warning",
                    title=f"Low-Confidence Opportunity: {title}",
                    explanation=f"Score {score:.1f} is promising but confidence {confidence:.2f} is below threshold.",
                    source_context={"source": "opportunities", "opportunity_id": row_id},
                    recommended_action="Inspect supporting evidence before promoting this opportunity.",
                    jira_key="SCRUM-227",
                    dismissible=False,
                )
            )
        if score is None:
            alerts.append(
                DashboardAlert(
                    id=f"opportunity-missing-score-{row_id}",
                    type="missing_score_evidence",
                    severity="error",
                    title=f"Missing Score Evidence: {title}",
                    explanation="The opportunity is missing score evidence required for deterministic ranking.",
                    source_context={"source": "opportunities", "opportunity_id": row_id},
                    recommended_action="Regenerate analysis payloads and confirm score fields are populated.",
                    jira_key="SCRUM-227",
                    dismissible=False,
                )
            )
    return alerts


def _build_run_alerts(run_history: list[dict[str, Any]], *, phase2_smoke: dict[str, Any]) -> list[DashboardAlert]:
    if not run_history:
        return [
            DashboardAlert(
                id="run-missing-evidence",
                type="missing_run_evidence",
                severity="warning",
                title="Missing Run Evidence",
                explanation="No run history payload was provided; monitoring coverage is incomplete.",
                source_context={"source": "run_history", "record_count": 0},
                recommended_action="Provide fixture-backed run history payloads for monitoring views.",
                jira_key="SCRUM-237",
                dismissible=False,
            )
        ]

    alerts: list[DashboardAlert] = []
    for row in run_history:
        run_id = str(row.get("run_id", "unknown")).strip() or "unknown"
        status = str(row.get("status", "unknown")).strip().lower() or "unknown"
        warning_count = int(_to_float(row.get("warning_count")) or 0)
        stages = row.get("stages")

        if status in {"failed", "fail", "error", "blocked"}:
            alerts.append(
                DashboardAlert(
                    id=f"run-failed-stage-{run_id}",
                    type="failed_stage",
                    severity="critical",
                    title=f"Run Failure: {run_id}",
                    explanation=f"Run reported status '{status}', indicating at least one failed stage.",
                    source_context={"source": "run_history", "run_id": run_id},
                    recommended_action="Inspect run logs and re-run failed stages with fixture-safe inputs.",
                    jira_key="SCRUM-219",
                    dismissible=False,
                )
            )
        if warning_count >= 3:
            alerts.append(
                DashboardAlert(
                    id=f"run-warning-heavy-{run_id}",
                    type="warning_heavy_run",
                    severity="warning",
                    title=f"Warning-Heavy Run: {run_id}",
                    explanation=f"Run produced {warning_count} warnings and needs QA review.",
                    source_context={"source": "run_history", "run_id": run_id},
                    recommended_action="Review warnings and confirm no hidden blocking conditions remain.",
                    jira_key="SCRUM-237",
                    dismissible=True,
                )
            )
        if not run_id or not isinstance(stages, list) or len(stages) == 0:
            alerts.append(
                DashboardAlert(
                    id=f"run-missing-structure-{run_id or 'unknown'}",
                    type="missing_run_structure",
                    severity="error",
                    title="Run Record Missing Evidence Fields",
                    explanation="A run entry is missing required run_id or stage metadata.",
                    source_context={"source": "run_history"},
                    recommended_action="Validate run-history contract and regenerate the affected run payload.",
                    jira_key="SCRUM-237",
                    dismissible=False,
                )
            )

    smoke_age_hours = _to_float(phase2_smoke.get("age_hours")) if phase2_smoke else None
    smoke_status = str(phase2_smoke.get("status", "unknown")).strip().lower() if phase2_smoke else "unknown"
    if smoke_age_hours is not None and smoke_age_hours > 24:
        alerts.append(
            DashboardAlert(
                id="run-stale-phase2-smoke",
                type="stale_phase2_smoke",
                severity="warning",
                title="Stale Phase2 Smoke Evidence",
                explanation=f"Latest phase2 smoke evidence is {smoke_age_hours:.0f} hours old.",
                source_context={"source": "phase2_smoke", "status": smoke_status},
                recommended_action="Run `python run.py phase2-smoke` and refresh integration evidence.",
                jira_key="SCRUM-237",
                dismissible=False,
            )
        )
    return alerts


def _build_freshness_alerts(source_freshness: list[dict[str, Any]]) -> list[DashboardAlert]:
    alerts: list[DashboardAlert] = []
    for row in source_freshness:
        freshness_status = str(row.get("freshness_status", "unknown")).strip().lower()
        if freshness_status != "stale":
            continue
        source_name = str(row.get("source_name", "unknown")).strip() or "unknown"
        alerts.append(
            DashboardAlert(
                id=f"source-stale-{source_name.lower().replace(' ', '-')}",
                type="stale_source_warning",
                severity="warning",
                title=f"Stale Source: {source_name}",
                explanation="Source freshness is stale and may impact score reliability.",
                source_context={"source": source_name, "freshness_status": freshness_status},
                recommended_action="Refresh source data before finalizing opportunity decisions.",
                jira_key="SCRUM-227",
                dismissible=True,
            )
        )
    return alerts


def _build_risk_placeholder_alerts(
    *,
    cost_risk: dict[str, Any] | None,
    quality_risk: dict[str, Any] | None,
    data_hygiene_risk: dict[str, Any] | None,
) -> list[DashboardAlert]:
    alerts: list[DashboardAlert] = []
    risk_inputs = [
        ("cost_risk_placeholder", "Cost Risk Placeholder", "SCRUM-241", cost_risk),
        ("quality_risk_placeholder", "Quality Risk Placeholder", "SCRUM-227", quality_risk),
        ("data_hygiene_risk_placeholder", "Data Hygiene Risk Placeholder", "SCRUM-241", data_hygiene_risk),
    ]
    for risk_type, title, jira_key, payload in risk_inputs:
        details = dict(payload or {})
        active = bool(details.get("active", False))
        severity = str(details.get("severity", "warning")).strip().lower() or "warning"
        if not active:
            continue
        alerts.append(
            DashboardAlert(
                id=risk_type,
                type=risk_type,
                severity=severity if severity in VALID_ALERT_SEVERITIES else "warning",
                title=title,
                explanation=str(details.get("explanation", "Risk placeholder raised from deterministic signal set.")),
                source_context={"source": "risk_placeholders", "details": details},
                recommended_action=str(
                    details.get("recommended_action", "Open a follow-up task and validate fixture-backed safeguards.")
                ),
                jira_key=jira_key,
                dismissible=False,
            )
        )
    return alerts


def _to_float(value: Any) -> float | None:
    if value is None:
        return None
    if isinstance(value, bool):
        return 1.0 if value else 0.0
    try:
        return float(value)
    except (TypeError, ValueError):
        return None
