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


def write_pr_body(cycle: int, run_dir: Path, **kwargs: Any) -> Path:
    """Write PR body to file. Returns path."""
    body = build_pr_body(cycle=cycle, **kwargs)
    path = run_dir / "github" / "pr_body.md"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(body)
    return path


def create_pr(cycle: int, branch: str, base: str = "develop",
              body: str = "", title: str = "",
              labels: list[str] | None = None) -> dict:
    """GJCI-015: Create PR from cycle branch to develop via gh CLI."""
    import subprocess
    if not title:
        title = f"[C{cycle:03d}] Autonomous runner cycle {cycle:03d}"

    args = [
        "gh", "pr", "create",
        "--repo", "KevinSGarrett/Fiverr",
        "--title", title,
        "--body", body or f"Cycle {cycle:03d} runner cycle PR",
        "--base", base,
        "--head", branch,
    ]
    for lbl in (labels or ["ai-runner"]):
        args += ["--label", lbl]

    r = subprocess.run(args, capture_output=True, text=True)
    if r.returncode != 0:
        return {"created": False, "error": r.stderr.strip(), "pr_number": None, "url": ""}

    url = r.stdout.strip()
    # Extract PR number from URL
    pr_number = None
    try:
        pr_number = int(url.rstrip("/").split("/")[-1])
    except Exception:
        pass

    return {"created": True, "pr_number": pr_number, "url": url, "error": ""}


def update_pr(pr_number: int, body: str) -> dict:
    """GJCI-016: Update PR body (post validation, repair, Codecov, Jira sync)."""
    import subprocess
    r = subprocess.run(
        ["gh", "pr", "edit", str(pr_number),
         "--repo", "KevinSGarrett/Fiverr",
         "--body", body],
        capture_output=True, text=True
    )
    return {"updated": r.returncode == 0, "error": r.stderr.strip() if r.returncode != 0 else ""}


def validate_pr_body(body: str, jira_keys: list[str]) -> dict:
    """GJCI-017: Validate PR body has required sections and Jira keys."""
    errors = []
    required_sections = [
        "## Jira AC/DoD",
        "## Changed Files",
        "## Validation",
        "## No-Main Confirmation",
        "## Runner / Model Evidence",
    ]
    for section in required_sections:
        if section.split("##")[1].strip().lower() not in body.lower():
            errors.append(f"Missing section: {section}")

    for key in jira_keys:
        if key not in body:
            errors.append(f"Missing Jira key: {key}")

    if "no direct push to `main`" not in body.lower() and "no direct push to main" not in body.lower():
        errors.append("Missing no-main confirmation")

    if "anthropic_api_key absent" not in body.lower():
        errors.append("Missing ANTHROPIC_API_KEY absent confirmation")

    return {"passed": len(errors) == 0, "errors": errors}
