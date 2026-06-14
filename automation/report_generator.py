"""Daily and weekly autonomy reports (OPS-022, OPS-023)."""
from __future__ import annotations

import json
from datetime import UTC, datetime, timedelta
from pathlib import Path

RUNNER_ROOT = Path("C:/AI_Runner")
REPO_ROOT = Path(__file__).parent.parent
REPORTS_DIR = RUNNER_ROOT / "reports"


def generate_daily_report(cycle: int | None = None) -> Path:
    """
    OPS-022: Daily status report covering runner, development, validation,
    Jira, repairs, incidents, model selection, post-cycle review, next 24h.
    """
    now = datetime.now(UTC)
    ts  = now.strftime("%Y%m%d_%H%M%S")

    # Gather state
    hb  = _load_json(RUNNER_ROOT / "state/heartbeat.json")
    cs  = _load_json(RUNNER_ROOT / "state/controller_state.json")
    ms  = _load_json(RUNNER_ROOT / "state/cursor_model_state.json")
    cls = _load_json(RUNNER_ROOT / "state/claude_model_state.json")
    # Primary health source from reports; fallback to legacy watchdog logs.
    last_health = _latest_json(RUNNER_ROOT / "reports", "health_*.json")
    if not last_health:
        last_health = _latest_json(RUNNER_ROOT / "logs/watchdog", "health_*.json")

    # Count incidents in last 24h
    incident_count = _count_recent_files(RUNNER_ROOT / "logs/incidents", hours=24)

    # Count notifications in last 24h
    notif_log = RUNNER_ROOT / "logs/notifications.log"
    notif_lines = _tail_log(notif_log, hours=24)
    blocked_count = sum(1 for line in notif_lines if '"BLOCKED"' in line or '"CRITICAL"' in line)

    valid_until_raw = ms.get("valid_until", "")
    days_until_expiry = None
    if valid_until_raw:
        try:
            valid_until = datetime.fromisoformat(str(valid_until_raw).replace("Z", "+00:00"))
            days_until_expiry = (valid_until - now).days
        except Exception:
            days_until_expiry = None
    model_header = "## Model Status"
    if days_until_expiry is not None and days_until_expiry <= 2:
        model_header = "## Model Status WARNING"

    heartbeat_age = _heartbeat_age_minutes(hb)
    health_level = _health_level(last_health)
    git_dirty_count = int(last_health.get("git_dirty_count", 0) or 0)
    controller_status = str(cs.get("status", "UNKNOWN"))
    next_action = _load_json(RUNNER_ROOT / "state/next_action_decision.json").get("next_action", "N/A")

    lines = [
        "# Daily Autonomous Runner Report",
        f"Generated: {now.isoformat()}",
        f"Cycle: {cycle or cs.get('active_cycle', 'IDLE')}",
        "",
        "## Health Status",
        f"Level: {health_level}",
        f"Heartbeat age: {heartbeat_age if heartbeat_age is not None else 'N/A'} minutes",
        f"Dirty files: {git_dirty_count}",
        f"Controller status: {controller_status}",
        f"Next action: {next_action}",
        "",
        "## Runner Status",
        f"- Controller state : {cs.get('status', 'UNKNOWN')}",
        f"- Last heartbeat   : {hb.get('last_seen', 'N/A')}",
        f"- Health level     : {health_level}",
        f"- GitHub runner    : {cs.get('github_runner_status', 'N/A')}",
        "",
        "## Development Activity",
        f"- Active cycle  : {cs.get('active_cycle', 'N/A')}",
        f"- Active branch : {cs.get('active_branch', 'N/A')}",
        f"- Active PR     : {cs.get('active_pr', 'N/A')}",
        "",
        model_header,
        f"- Cursor model  : {ms.get('observed_model', 'N/A')} [{ms.get('status', 'N/A')}]",
        f"- Effort        : {ms.get('effort', 'N/A')}",
        f"- Verified at   : {ms.get('verified_at', 'N/A')}",
        f"- Days to expiry: {days_until_expiry if days_until_expiry is not None else 'N/A'}",
        f"- Claude billing: {cls.get('billing_mode', 'N/A')} [{cls.get('status', 'N/A')}]",
        f"- API key check : {'ABSENT' if not cls.get('anthropic_api_key_present') else 'PRESENT â€” REVIEW REQUIRED'}",
        "",
        "## Incidents (last 24h)",
        f"- Total incidents      : {incident_count}",
        f"- BLOCKED/CRITICAL     : {blocked_count}",
        "",
        "## Next 24 Hours",
        "- Next tick       : scheduled (every 5 min via watchdog)",
        "- Next snapshot   : 02:00 UTC daily",
        f"- Post-cycle gate : {'active' if cs.get('status') == 'POST_CYCLE_PASS' else 'pending cycle completion'}",
    ]

    path = REPORTS_DIR / "daily" / f"daily_report_{ts}.md"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")
    # Keep latest symlink-style reference
    latest = REPORTS_DIR / "daily" / "latest_daily_report.md"
    latest.write_text("\n".join(lines), encoding="utf-8")
    return path


def generate_weekly_report() -> Path:
    """
    OPS-023: Weekly autonomy review â€” cycles, PRs, repairs, interruptions,
    false stops, unsafe attempts, model drift, post-cycle failures.
    """
    now = datetime.now(UTC)
    ts  = now.strftime("%Y%m%d")

    incident_count = _count_recent_files(RUNNER_ROOT / "reports/incidents", hours=168)
    if incident_count == 0:
        incident_count = _count_recent_files(RUNNER_ROOT / "logs/incidents", hours=168)
    snapshot_count = _count_recent_files(RUNNER_ROOT / "logs/snapshots", hours=168)
    cycles_completed = _count_recent_files(REPO_ROOT / "PM_Pack/10_cycle_log", hours=168, pattern="CYCLE_*.md")
    model_drift_count = _count_recent_files(RUNNER_ROOT / "reports", hours=168, pattern="*drift*.json")
    human_interruptions = _count_recent_files(
        RUNNER_ROOT / "reports/incidents", hours=168, pattern="*HUMAN*"
    )
    if human_interruptions == 0:
        human_interruptions = _count_recent_files(
            RUNNER_ROOT / "logs/incidents", hours=168, pattern="*HUMAN*"
        )
    avg_cycle_duration_minutes = _average_cycle_duration_minutes(REPO_ROOT / "PM_Pack/10_cycle_log")
    health_summary = _weekly_health_summary(RUNNER_ROOT / "reports")

    lines = [
        "# Weekly Autonomy Review",
        f"Week ending: {now.strftime('%Y-%m-%d')}",
        f"Generated  : {now.isoformat()}",
        "",
        "## This Week",
        f"- Cycles completed (7d) : {cycles_completed}",
        f"- Human interruptions    : {human_interruptions}",
        f"- Model drift incidents  : {model_drift_count}",
        f"- Avg cycle duration (m) : {avg_cycle_duration_minutes if avg_cycle_duration_minutes is not None else 'N/A'}",
        f"- Health summary         : GREEN={health_summary['GREEN']} ORANGE={health_summary['ORANGE']} RED={health_summary['RED']}",
        f"- Incidents (7d)       : {incident_count}",
        f"- Daily snapshots (7d) : {snapshot_count}",
        "",
        "## Autonomy Quality",
        "- Human interruptions  : (review incidents log)",
        "- False stops          : (review BLOCKED incidents vs total)",
        "- Unsafe attempts      : (review SEC guard logs)",
        "- Model drift events   : (review model_verification logs)",
        "",
        "## Action Items",
        "- Review any BLOCKED/CRITICAL incidents",
        "- Confirm model verification is fresh (<7 days)",
        "- Verify develop branch is ahead of last cycle",
        "- Check Jira for any stale In-Review issues",
    ]

    path = REPORTS_DIR / "weekly" / f"weekly_report_{ts}.md"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")
    latest = REPORTS_DIR / "weekly" / "latest_weekly_report.md"
    latest.write_text("\n".join(lines), encoding="utf-8")
    return path


def _load_json(path: Path) -> dict:
    try:
        return json.loads(path.read_text(encoding="utf-8", errors="replace")) if path.exists() else {}
    except Exception:
        return {}


def _latest_json(directory: Path, pattern: str) -> dict:
    if not directory.exists():
        return {}
    files = sorted(directory.glob(pattern))
    return _load_json(files[-1]) if files else {}


def _count_recent_files(directory: Path, hours: int = 24, pattern: str = "*") -> int:
    if not directory.exists():
        return 0
    cutoff = datetime.now(UTC) - timedelta(hours=hours)
    return sum(
        1 for f in directory.glob(pattern)
        if f.is_file() and datetime.fromtimestamp(f.stat().st_mtime, tz=UTC) >= cutoff
    )


def _tail_log(path: Path, hours: int = 24) -> list[str]:
    if not path.exists():
        return []
    cutoff = datetime.now(UTC) - timedelta(hours=hours)
    lines = []
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        try:
            ts = json.loads(line).get("ts", "")
            if ts and datetime.fromisoformat(ts.replace("Z", "+00:00")) >= cutoff:
                lines.append(line)
        except Exception:
            pass
    return lines


def _heartbeat_age_minutes(heartbeat_payload: dict) -> float | None:
    last_seen = heartbeat_payload.get("last_seen")
    if not isinstance(last_seen, str) or not last_seen.strip():
        return None
    try:
        hb_time = datetime.fromisoformat(last_seen.replace("Z", "+00:00"))
    except ValueError:
        return None
    return round((datetime.now(UTC) - hb_time).total_seconds() / 60.0, 1)


def _health_level(health_payload: dict) -> str:
    if not isinstance(health_payload, dict) or not health_payload:
        return "N/A"
    return str(
        health_payload.get("health_level")
        or health_payload.get("Level")
        or "N/A"
    )


def _average_cycle_duration_minutes(cycle_log_dir: Path) -> float | None:
    if not cycle_log_dir.exists():
        return None
    starts: list[datetime] = []
    ends: list[datetime] = []
    for path in cycle_log_dir.glob("CYCLE_*.md"):
        try:
            ts = datetime.fromtimestamp(path.stat().st_mtime, tz=UTC)
        except OSError:
            continue
        if "START" in path.name.upper():
            starts.append(ts)
        elif "END" in path.name.upper() or "COMPLETE" in path.name.upper():
            ends.append(ts)
    if not starts or not ends:
        return None
    starts.sort()
    ends.sort()
    pairs = zip(starts, ends, strict=False)
    durations = [(end - start).total_seconds() / 60.0 for start, end in pairs if end >= start]
    if not durations:
        return None
    return round(sum(durations) / len(durations), 1)


def _weekly_health_summary(reports_dir: Path) -> dict[str, int]:
    summary = {"GREEN": 0, "ORANGE": 0, "RED": 0}
    if not reports_dir.exists():
        return summary
    cutoff = datetime.now(UTC) - timedelta(days=7)
    for path in reports_dir.glob("health_*.json"):
        try:
            if datetime.fromtimestamp(path.stat().st_mtime, tz=UTC) < cutoff:
                continue
        except OSError:
            continue
        payload = _load_json(path)
        level = _health_level(payload).upper()
        if level in summary:
            summary[level] += 1
    return summary
