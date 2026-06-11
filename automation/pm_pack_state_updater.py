"""
pm_pack_state_updater.py — Update PM_Pack brain files after each cycle.
Writes to HYDRATION_HEADER, STATE_SNAPSHOT, EPIC_STATUS_TRACKER, cycle logs.
This is the STATE section of the checklist (STATE-001 through STATE-016).
"""
from __future__ import annotations

import re
import subprocess
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

REPO_ROOT = Path("C:/Fiverr/Fiverr")
PM_PACK = REPO_ROOT / "PM_Pack"


def update_hydration_header(cycle: int, branch: str, pr: int | None,
                             merge_sha: str, score1: float, score2: float,
                             next_cycle: int, blockers: list[str]) -> bool:
    """
    Update CYCLE_CURRENT, LAST_COMPLETED, branch, PR, scores in HYDRATION_HEADER.
    Uses line-level targeted replacements to preserve the rest of the file.
    """
    path = PM_PACK / "07_hydration/HYDRATION_HEADER.md"
    if not path.exists():
        return False

    text = path.read_text(encoding="utf-8", errors="replace")
    now = datetime.now(UTC).strftime("%Y-%m-%d")

    # Update CYCLE_CURRENT to next cycle
    text = re.sub(r"^CYCLE_CURRENT:\s*\d+",
                  f"CYCLE_CURRENT: {next_cycle:03d}", text, flags=re.MULTILINE)
    text = re.sub(r"^CYCLE_NEXT:\s*\d+",
                  f"CYCLE_NEXT: {next_cycle:03d}", text, flags=re.MULTILINE)
    text = re.sub(r"^CYCLE_DONE:\s*\d+",
                  f"CYCLE_DONE: {cycle:03d}", text, flags=re.MULTILINE)
    text = re.sub(r"^LAST_COMPLETED:\s*.+",
                  f"LAST_COMPLETED: C{cycle:03d}", text, flags=re.MULTILINE)

    # Update header date
    text = re.sub(r"## Updated:\s*[\d-]+",
                  f"## Updated: {now}", text)

    # Update scores if present
    if score1 > 0:
        text = re.sub(r"^INTERNAL_BUILD_PROGRESS:\s*~?\d+(?:\.\d+)?%",
                      f"INTERNAL_BUILD_PROGRESS: ~{score1:.0f}%",
                      text, flags=re.MULTILINE)
    if score2 > 0:
        text = re.sub(r"^END_TO_END_PRODUCTION_READINESS:\s*~?\d+(?:\.\d+)?%",
                      f"END_TO_END_PRODUCTION_READINESS: ~{score2:.0f}%",
                      text, flags=re.MULTILINE)

    path.write_text(text, encoding="utf-8")
    return True


def write_cycle_log(cycle: int, branch: str, pr: int | None,
                    merge_sha: str, agents_done: list[str],
                    validation_passed: bool, score1: float, score2: float,
                    tierd2_status: str, post_cycle_result: str) -> Path:
    """Write PM_Pack/10_cycle_log/CYCLE_NNN_AUTONOMOUS_RUN.md"""
    log_dir = PM_PACK / "10_cycle_log"
    log_dir.mkdir(parents=True, exist_ok=True)
    path = log_dir / f"CYCLE_{cycle:03d}_AUTONOMOUS_RUN.md"

    now = datetime.now(UTC).isoformat()
    lines = [
        f"# Cycle {cycle:03d} — Autonomous Runner Log",
        f"Generated: {now}",
        f"Branch: {branch}",
        f"PR: #{pr}" if pr else "PR: N/A",
        f"Merge SHA: {merge_sha or 'pending'}",
        "",
        "## Agents",
        f"Completed: {', '.join(agents_done)}",
        "",
        "## Validation",
        f"Local suite: {'PASS' if validation_passed else 'FAIL'}",
        "",
        "## Scores",
        f"Score 1 Internal Build: ~{score1:.0f}%",
        f"Score 2 E2E Readiness : ~{score2:.0f}%",
        "",
        "## TierD-2 Status",
        tierd2_status or "See HYDRATION_HEADER.md",
        "",
        "## Post-Cycle Review",
        f"Result: {post_cycle_result}",
    ]
    path.write_text("\n".join(lines), encoding="utf-8")
    return path


def write_run_summary_full(run_dir: Path, cycle: int, agents: list[str],
                            agent_results: dict, validation: Any,
                            pr: int | None, jira_keys: list[str]) -> Path:
    """Write detailed RUN_SUMMARY.md for the cycle run directory."""
    path = run_dir / "RUN_SUMMARY.md"
    now = datetime.now(UTC).isoformat()
    lines = [
        f"# Run Summary — Cycle {cycle:03d}",
        f"Generated: {now}",
        "",
        "## Agents",
    ]
    for agent in agents:
        r = agent_results.get(agent, {})
        status = r.get("status", "unknown") if isinstance(r, dict) else getattr(r, "status", "unknown")
        lines.append(f"- Agent {agent}: {status}")

    lines += ["", "## Validation"]
    if hasattr(validation, "summary"):
        lines.append(validation.summary())
    elif isinstance(validation, dict):
        for k, v in validation.items():
            lines.append(f"- {k}: {'PASS' if v else 'FAIL'}")

    lines += ["", "## GitHub"]
    lines.append(f"PR: #{pr}" if pr else "PR: not yet created")

    lines += ["", "## Jira"]
    lines.append(f"Keys: {', '.join(jira_keys) if jira_keys else 'TBD'}")

    lines += ["", "## Artifacts", f"Run directory: {run_dir}"]
    path.write_text("\n".join(lines), encoding="utf-8")
    return path


def write_agent_summary(run_dir: Path, cycle: int,
                         agent_results: dict) -> Path:
    path = run_dir / "AGENT_SUMMARY.md"
    lines = [f"# Agent Summary — Cycle {cycle:03d}", ""]
    for agent, result in agent_results.items():
        status = result.get("status", "?") if isinstance(result, dict) else getattr(result, "status", "?")
        lines += [f"## Agent {agent}", f"Status: {status}", ""]
    path.write_text("\n".join(lines), encoding="utf-8")
    return path


def write_validation_summary(run_dir: Path, cycle: int,
                               validation_result: Any) -> Path:
    path = run_dir / "VALIDATION_SUMMARY.md"
    lines = [f"# Validation Summary — Cycle {cycle:03d}", ""]
    if hasattr(validation_result, "gates"):
        for gate in validation_result.gates:
            icon = "PASS" if gate.passed else "FAIL"
            lines.append(f"- [{icon}] {gate.name}: {gate.output[:100] if gate.output else ''}")
    path.write_text("\n".join(lines), encoding="utf-8")
    return path


def write_jira_sync_summary(run_dir: Path, cycle: int,
                              updates: list[dict]) -> Path:
    path = run_dir / "JIRA_SYNC_SUMMARY.md"
    lines = [f"# Jira Sync Summary — Cycle {cycle:03d}", ""]
    for u in updates:
        lines.append(f"- {u.get('key', '?')}: {u.get('action', '?')}")
    if not updates:
        lines.append("No Jira updates recorded this cycle.")
    path.write_text("\n".join(lines), encoding="utf-8")
    return path


def write_github_pr_summary(run_dir: Path, cycle: int,
                              pr: int | None, merge_sha: str,
                              ci_passed: bool) -> Path:
    path = run_dir / "GITHUB_PR_SUMMARY.md"
    lines = [
        f"# GitHub PR Summary — Cycle {cycle:03d}",
        "",
        f"PR: #{pr}" if pr else "PR: not yet created",
        f"Merge SHA: {merge_sha or 'N/A'}",
        f"CI passed: {ci_passed}",
    ]
    path.write_text("\n".join(lines), encoding="utf-8")
    return path


def commit_governance_closeout(cycle: int, message: str) -> str:
    """
    Direct docs/PM_Pack governance commit to develop.
    Only allowed if no src/tests changes are staged.
    """
    # Safety: verify only docs/PM_Pack files are staged
    r = subprocess.run(
        ["git", "diff", "--cached", "--name-only"],
        cwd=str(REPO_ROOT), capture_output=True, text=True
    )
    staged = r.stdout.strip().splitlines()
    forbidden = [f for f in staged
                 if not (f.startswith("PM_Pack/") or f.startswith("docs/")
                         or f.startswith("automation/docs/"))]
    if forbidden:
        raise ValueError(
            f"Governance closeout staged non-docs files: {forbidden}. "
            "Abort and investigate before committing."
        )

    subprocess.run(["git", "add", "PM_Pack/", "docs/"],
                   cwd=str(REPO_ROOT), check=True, capture_output=True)
    r = subprocess.run(
        ["git", "commit", "-m", message or f"docs(cycle-{cycle:03d}): autonomous runner closeout"],
        cwd=str(REPO_ROOT), capture_output=True, text=True
    )
    if r.returncode != 0:
        raise RuntimeError(f"Governance commit failed: {r.stderr.strip()}")
    return subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=str(REPO_ROOT), capture_output=True, text=True
    ).stdout.strip()
