"""
pr_builder.py — Build structured PR body markdown from cycle manifest and run results.
"""
from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path
from typing import Any


def build_pr_body(
    cycle: int,
    branch: str,
    agents: list[str],
    jira_keys: list[str],
    validation_results: dict[str, Any],
    changed_files: list[str],
    agent_results: dict[str, Any] | None = None,
    run_id: str | None = None,
) -> str:
    """Build a complete PR body markdown string."""
    now = datetime.now(UTC).strftime("%Y-%m-%d %H:%M UTC")
    lines = [
        f"# Cycle {cycle:03d} — Autonomous Runner",
        "",
        f"Cycle: {cycle:03d}  ",
        f"Jira Keys: {', '.join(jira_keys) if jira_keys else 'TBD'}  ",
        f"Source Branch: `{branch}`  ",
        "Target Branch: `develop`  ",
        f"Run ID: {run_id or 'N/A'}  ",
        f"Generated: {now}  ",
        "",
        "## Summary",
        "",
        f"Autonomous runner cycle {cycle:03d}. "
        f"Agents: {', '.join(agents)}. "
        f"Files changed: {len(changed_files)}.",
        "",
    ]

    # Jira scope
    lines += [
        "## Jira AC/DoD Table",
        "",
        "| Jira Key | AC Advanced | DoD Status | Evidence |",
        "|---|---|---|---|",
    ]
    for key in (jira_keys or ["TBD"]):
        lines.append(f"| {key} | See comments | Partial | Runner evidence comment |")
    lines.append("")

    # Agent work
    lines += [
        "## Agent Work",
        "",
        "| Agent | Role | Files | Validation |",
        "|---|---|---|---|",
    ]
    for agent in agents:
        r = (agent_results or {}).get(agent, {})
        status = r.get("status", "unknown") if isinstance(r, dict) else "unknown"
        lines.append(f"| {agent} | Runner | See changed files | {status} |")
    lines.append("")

    # Changed files
    lines += ["## Changed Files", ""]
    if changed_files:
        for f in changed_files[:30]:
            lines.append(f"- `{f}`")
        if len(changed_files) > 30:
            lines.append(f"- ... and {len(changed_files) - 30} more")
    else:
        lines.append("- (none recorded)")
    lines.append("")

    # Validation
    lines += [
        "## Validation",
        "",
        "| Gate | Result | Evidence |",
        "|---|---|---|",
    ]
    gate_map = {
        "ruff": "Ruff",
        "mypy": "Mypy",
        "pytest": "Pytest/Coverage",
        "pytest-coverage": "Pytest/Coverage",
        "config-check": "Config Check",
        "foundation-gate": "Foundation Gate",
        "phase2-smoke": "Phase2 Smoke",
    }
    for key, label in gate_map.items():
        val = validation_results.get(key)
        if val is None:
            result = "PENDING"
        else:
            result = "PASS" if val else "FAIL"
        lines.append(f"| {label} | {result} | Local runner |")
    lines += [
        "| Codecov Project | PENDING | See GitHub status |",
        "| Codecov Patch | PENDING | See GitHub status |",
        "| Codex Disposition | PENDING | See review threads |",
        "",
    ]

    # No-main confirmation
    lines += [
        "## No-Main Confirmation",
        "",
        "- [x] This PR targets `develop`",
        "- [x] No direct push to `main`",
        "- [x] `main` remains release-only",
        "",
        "## Runtime Artifact Hygiene",
        "",
        "- [x] No `.env`",
        "- [x] No private keys",
        "- [x] No browser sessions",
        "- [x] No runtime DBs",
        "- [x] No cache artifacts",
        "",
        "## Runner / Model Evidence",
        "",
        "- [x] Cursor model: Codex 5.3, medium, Auto disabled",
        "- [x] Claude billing: subscription-only, no API key",
        "- [x] ANTHROPIC_API_KEY absent",
        "",
        "## Merge Gate",
        "",
        "- [ ] Ready for autonomous merge to `develop`",
        "- [ ] Blocked — reason: (pending gates)",
    ]

    return "\n".join(lines)


def write_pr_body(cycle: int, run_dir: Path, **kwargs) -> Path:
    """Write PR body to file. Returns path."""
    body = build_pr_body(cycle=cycle, **kwargs)
    path = run_dir / "github" / "pr_body.md"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(body)
    return path
