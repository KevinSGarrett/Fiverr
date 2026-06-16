"""
report_generator.py — Daily and weekly autonomy reports (OPS-022, OPS-023).
"""
from __future__ import annotations

import json
import subprocess
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

RUNNER_ROOT = Path("C:/AI_Runner")
REPO_ROOT = Path("C:/Fiverr/Fiverr")
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
    last_health = _latest_json(RUNNER_ROOT / "logs/watchdog", "health_*.json")

    # Count incidents in last 24h
    incident_count = _count_recent_files(RUNNER_ROOT / "logs/incidents", hours=24)

    # Count notifications in last 24h
    notif_log = RUNNER_ROOT / "logs/notifications.log"
    notif_lines = _tail_log(notif_log, hours=24)
    blocked_count = sum(1 for line in notif_lines if '"BLOCKED"' in line or '"CRITICAL"' in line)

    builder = ReportGenerator()
    lines = [
        "# Daily Autonomous Runner Report",
        f"Generated: {now.isoformat()}",
        f"Cycle: {cycle or cs.get('active_cycle', 'IDLE')}",
        "",
        "## Runner Status",
        f"- Controller state : {cs.get('status', 'UNKNOWN')}",
        f"- Last heartbeat   : {hb.get('last_seen', 'N/A')}",
        f"- Health level     : {last_health.get('Level', 'N/A') if last_health else 'N/A'}",
        f"- GitHub runner    : {cs.get('github_runner_status', 'N/A')}",
        "",
        "## Development Activity",
        f"- Active cycle  : {cs.get('active_cycle', 'N/A')}",
        f"- Active branch : {cs.get('active_branch', 'N/A')}",
        f"- Active PR     : {cs.get('active_pr', 'N/A')}",
        "",
        "## Model Selection",
        f"- Cursor model  : {ms.get('observed_model', 'N/A')} [{ms.get('status', 'N/A')}]",
        f"- Claude billing: {cls.get('billing_mode', 'N/A')} [{cls.get('status', 'N/A')}]",
        f"- API key check : {'ABSENT' if not cls.get('anthropic_api_key_present') else 'PRESENT — REVIEW REQUIRED'}",
        "",
    ]
    lines.extend(builder._get_model_status_section().splitlines())
    lines.extend(
        [
            "",
        ]
    )
    lines.extend(builder._get_ci_timing_section().splitlines())
    lines.extend(
        [
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
    )

    path = REPORTS_DIR / "daily" / f"daily_report_{ts}.md"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")
    # Keep latest symlink-style reference
    latest = REPORTS_DIR / "daily" / "latest_daily_report.md"
    latest.write_text("\n".join(lines), encoding="utf-8")
    return path


def generate_weekly_report() -> Path:
    """
    OPS-023: Weekly autonomy review — cycles, PRs, repairs, interruptions,
    false stops, unsafe attempts, model drift, post-cycle failures.
    """
    now = datetime.now(UTC)
    ts  = now.strftime("%Y%m%d")

    incident_count  = _count_recent_files(RUNNER_ROOT / "logs/incidents", hours=168)
    snapshot_count  = _count_recent_files(RUNNER_ROOT / "logs/snapshots", hours=168)

    lines = [
        "# Weekly Autonomy Review",
        f"Week ending: {now.strftime('%Y-%m-%d')}",
        f"Generated  : {now.isoformat()}",
        "",
        "## This Week",
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
        return json.loads(path.read_text()) if path.exists() else {}
    except Exception:
        return {}


def _latest_json(directory: Path, pattern: str) -> dict:
    if not directory.exists():
        return {}
    files = sorted(directory.glob(pattern))
    return _load_json(files[-1]) if files else {}


def _count_recent_files(directory: Path, hours: int = 24) -> int:
    if not directory.exists():
        return 0
    cutoff = datetime.now(UTC) - timedelta(hours=hours)
    return sum(
        1 for f in directory.glob("*")
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


class ReportGenerator:
    """Report helper methods for daily report extensions."""

    def _get_model_status_section(self) -> str:
        cursor_state = _load_json(Path("C:/AI_Runner/state/cursor_model_state.json"))
        claude_state = _load_json(Path("C:/AI_Runner/state/claude_model_state.json"))
        now = datetime.now(tz=UTC)

        cursor_verified_at = _parse_iso(cursor_state.get("verified_at"))
        cursor_age_days = _age_days(cursor_verified_at, now)
        cursor_expires = (
            (cursor_verified_at + timedelta(days=7)).date().isoformat() if cursor_verified_at else "unknown"
        )
        cursor_model = cursor_state.get("observed_model", cursor_state.get("model", "unknown"))
        cursor_effort = cursor_state.get("effort", "unknown")

        claude_model = claude_state.get("model", claude_state.get("observed_model", "unknown"))
        claude_effort = claude_state.get("effort", "unknown")
        claude_billing = claude_state.get("billing_mode", "unknown")

        return (
            "## Model Verification Status\n"
            f"Cursor: {cursor_model} | effort: {cursor_effort} | age: {cursor_age_days} days | expires: {cursor_expires}\n"
            f"Claude: {claude_model} | effort: {claude_effort} | billing: {claude_billing}"
        )

    def _get_ci_timing_section(self) -> str:
        try:
            result = subprocess.run(
                ["gh", "run", "list", "--workflow=ci.yml", "--limit", "5", "--json", "conclusion,createdAt,updatedAt"],
                capture_output=True,
                text=True,
                check=True,
            )
            runs = json.loads(result.stdout or "[]")
        except (subprocess.CalledProcessError, FileNotFoundError, json.JSONDecodeError):
            return "## CI Timing\nLast 5 runs avg: N/A | last run: unavailable (0s)"

        durations: list[float] = []
        last_conclusion = "unknown"
        last_duration = 0.0
        for idx, run in enumerate(runs):
            created = _parse_iso(run.get("createdAt"))
            updated = _parse_iso(run.get("updatedAt"))
            if not created or not updated:
                continue
            duration = max((updated - created).total_seconds(), 0.0)
            durations.append(duration)
            if idx == 0:
                last_conclusion = str(run.get("conclusion", "unknown"))
                last_duration = duration
        avg = int(sum(durations) / len(durations)) if durations else 0
        return f"## CI Timing\nLast 5 runs avg: {avg}s | last run: {last_conclusion} ({int(last_duration)}s)"


def _parse_iso(value: Any) -> datetime | None:
    if not value:
        return None
    text = str(value).replace("Z", "+00:00")
    try:
        parsed = datetime.fromisoformat(text)
    except ValueError:
        return None
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=UTC)
    return parsed.astimezone(UTC)


def _age_days(verified_at: datetime | None, now: datetime) -> int:
    if verified_at is None:
        return -1
    return max((now - verified_at).days, 0)
