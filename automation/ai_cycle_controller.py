"""
ai_cycle_controller.py — Main CLI entrypoint for the Autonomous Development Runner.

Usage:
  python automation/ai_cycle_controller.py brain-check
  python automation/ai_cycle_controller.py compile-policy
  python automation/ai_cycle_controller.py jira-inventory [--dry-run]
  python automation/ai_cycle_controller.py plan-cycle [--dry-run] [--cycle N]
  python automation/ai_cycle_controller.py cursor-smoke
  python automation/ai_cycle_controller.py status
  python automation/ai_cycle_controller.py tick
  python automation/ai_cycle_controller.py recover
"""
from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import click

# Ensure repo root on sys.path when run as a script
_here = Path(__file__).parent
_repo_root = _here.parent
if str(_repo_root) not in sys.path:
    sys.path.insert(0, str(_repo_root))

from automation.pm_pack_loader import brain_check
from automation.policy_compiler import compile_policy
from automation.config_loader import get_secret

REPO_ROOT = _repo_root
RUNNER_STATE = Path("C:/AI_Runner/state/controller_state.json")


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _write_runner_state(state: dict) -> None:
    RUNNER_STATE.parent.mkdir(parents=True, exist_ok=True)
    RUNNER_STATE.write_text(json.dumps(state, indent=2))


def _read_runner_state() -> dict:
    try:
        return json.loads(RUNNER_STATE.read_text()) if RUNNER_STATE.exists() else {}
    except Exception:
        return {}


@click.group()
def cli():
    """Fiverr Research System — Autonomous Development Runner."""
    pass


@cli.command("brain-check")
def cmd_brain_check():
    """Load all PM_Pack brain files and verify they exist and are readable."""
    click.echo("=" * 60)
    click.echo("BRAIN CHECK - Fiverr Autonomous Runner")
    click.echo("=" * 60)

    result = brain_check(REPO_ROOT)

    for msg in result.passed:
        click.echo(f"  [PASS] {msg}")
    for msg in result.warnings:
        click.secho(f"  [WARN] {msg}", fg="yellow")
    for msg in result.failed:
        click.secho(f"  [FAIL] {msg}", fg="red")

    click.echo()
    if result.cycle_detected:
        click.echo(f"  Cycle detected  : {result.cycle_detected}")
    if result.wave_detected:
        click.echo(f"  Wave detected   : {result.wave_detected}")
    if result.blockers_detected:
        click.echo(f"  Blockers        : {', '.join(result.blockers_detected[:3])}")
    click.echo(f"  Cursor model    : {result.cursor_model_status}")
    click.echo(f"  Claude billing  : {result.claude_model_status}")
    click.echo(f"  Post-cycle prompt: {'OK' if result.post_cycle_prompt_present else 'MISSING'}")
    click.echo()

    if result.ok:
        click.secho("BRAIN CHECK PASS", fg="green", bold=True)
        sys.exit(0)
    else:
        click.secho(f"BRAIN CHECK FAIL — {len(result.failed)} missing file(s)", fg="red", bold=True)
        sys.exit(1)


@cli.command("compile-policy")
def cmd_compile_policy():
    """Compile PM_Pack rules into current_policy_snapshot.json."""
    click.echo("=" * 60)
    click.echo("COMPILE POLICY")
    click.echo("=" * 60)

    snapshot = compile_policy(REPO_ROOT)
    out = REPO_ROOT / "PM_Pack/automation/current_policy_snapshot.json"
    click.echo(f"  Cycle   : {snapshot.get('cycle_current')}")
    click.echo(f"  Wave    : {snapshot.get('active_wave')}")
    click.echo(f"  E2E     : {snapshot.get('e2e_score_pct')}%")
    click.echo(f"  Agents  : {snapshot.get('active_agent_lanes')}")
    click.echo(f"  Cursor  : {snapshot.get('cursor_model', {}).get('status')}")
    click.echo()
    click.secho(f"Policy snapshot written to: {out}", fg="green")


@cli.command("jira-inventory")
@click.option("--dry-run", is_flag=True, default=False, help="No Jira writes.")
@click.option("--project", default="SCRUM", help="Jira project key.")
def cmd_jira_inventory(dry_run: bool, project: str):
    """Fetch Jira board inventory — all non-Done issues."""
    click.echo("=" * 60)
    click.echo(f"JIRA BOARD INVENTORY {'[DRY RUN]' if dry_run else ''}")
    click.echo("=" * 60)

    jira_token = get_secret("JIRA_API_TOKEN")
    if not jira_token or jira_token in ("DO_NOT_COMMIT", "FILL_IN_BEFORE_USE"):
        click.secho("  Jira credentials not set. Add JIRA_EMAIL and JIRA_API_TOKEN", fg="yellow")
        click.secho("  to C:\\AI_Runner\\secrets\\runner.env before running.", fg="yellow")
        click.echo()
        click.secho("  SKIPPED — no credentials", fg="yellow")
        sys.exit(0)

    from automation.jira_client import board_inventory
    try:
        inv = board_inventory(project)
        run_id = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S")
        out_dir = REPO_ROOT / f"PM_Pack/automation/runs/{run_id}"
        out_dir.mkdir(parents=True, exist_ok=True)
        out_path = out_dir / "board_inventory.json"
        out_path.write_text(json.dumps(inv, indent=2))

        click.echo(f"  Total non-Done issues : {inv['total']}")
        for issue in inv["issues"][:10]:
            click.echo(f"    [{issue['status']}] {issue['key']} — {issue['summary'][:60]}")
        if inv["total"] > 10:
            click.echo(f"    ... and {inv['total'] - 10} more")
        click.echo()
        if dry_run:
            click.secho(f"DRY RUN — board_inventory.json written to {out_path}", fg="green")
        else:
            click.secho(f"Board inventory written to {out_path}", fg="green")
    except Exception as e:
        click.secho(f"  Jira inventory failed: {e}", fg="red")
        sys.exit(1)


@cli.command("status")
def cmd_status():
    """Show current controller and runner state."""
    click.echo("=" * 60)
    click.echo("CONTROLLER STATUS")
    click.echo("=" * 60)

    state = _read_runner_state()
    if state:
        click.echo(f"  Runner          : {state.get('runner')}")
        click.echo(f"  Active cycle    : {state.get('active_cycle')}")
        click.echo(f"  Active branch   : {state.get('active_branch')}")
        click.echo(f"  Active PR       : {state.get('active_pr')}")
        click.echo(f"  Status          : {state.get('status')}")
        click.echo(f"  Last heartbeat  : {state.get('last_heartbeat')}")
        click.echo(f"  Last run ID     : {state.get('last_run_id')}")
    else:
        click.echo("  No controller state found — controller has not run yet.")

    # Show model states
    cursor_state_path = Path("C:/AI_Runner/state/cursor_model_state.json")
    if cursor_state_path.exists():
        cs = json.loads(cursor_state_path.read_text())
        click.echo(f"  Cursor model    : {cs.get('observed_model')} [{cs.get('status')}]")

    # Show GitHub runner service
    import subprocess
    svc = subprocess.run(
        ["powershell", "-Command",
         "Get-Service 'actions.runner.*' | Select-Object -First 1 | ForEach-Object { $_.Status }"],
        capture_output=True, text=True
    )
    svc_status = svc.stdout.strip() or "unknown"
    click.echo(f"  GitHub runner   : {svc_status}")

    # Show snapshot if present
    snap = REPO_ROOT / "PM_Pack/automation/current_policy_snapshot.json"
    if snap.exists():
        s = json.loads(snap.read_text())
        click.echo(f"  Policy snapshot : cycle={s.get('cycle_current')} wave={s.get('active_wave')}")
    else:
        click.secho("  Policy snapshot : not yet compiled (run compile-policy)", fg="yellow")


@cli.command("plan-cycle")
@click.option("--dry-run", is_flag=True, default=True, help="Generate manifest, do not dispatch.")
@click.option("--cycle", default=None, type=int, help="Cycle number override.")
def cmd_plan_cycle(dry_run: bool, cycle: int | None):
    """Plan next cycle: generate manifest and prompt stubs (dry-run by default)."""
    click.echo("=" * 60)
    click.echo(f"PLAN CYCLE {'[DRY RUN]' if dry_run else '[LIVE]'}")
    click.echo("=" * 60)

    # Get current cycle from policy snapshot
    snap_path = REPO_ROOT / "PM_Pack/automation/current_policy_snapshot.json"
    if not snap_path.exists():
        click.secho("  Run compile-policy first.", fg="red")
        sys.exit(1)

    snap = json.loads(snap_path.read_text())
    current = snap.get("cycle_current", 74)
    next_cycle = cycle if cycle is not None else current + 1
    run_id = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S")
    branch = f"cycle/{next_cycle:03d}/integration"

    out_dir = REPO_ROOT / f"PM_Pack/automation/runs/{run_id}"
    out_dir.mkdir(parents=True, exist_ok=True)

    manifest = {
        "run_id": run_id,
        "cycle": next_cycle,
        "branch": branch,
        "base_branch": "develop",
        "agents": snap.get("active_agent_lanes", ["A", "B", "E", "C", "F", "D"]),
        "dry_run": dry_run,
        "planned_at": _now(),
        "quality_gates": snap.get("quality_gates", {}),
        "jira_policy": snap.get("jira_policy", {}),
        "status": "PLANNED_DRY_RUN" if dry_run else "PLANNED",
    }

    manifest_path = out_dir / f"CYCLE_{next_cycle:03d}_MANIFEST.json"
    manifest_path.write_text(json.dumps(manifest, indent=2))

    # Write stub prompt files for each agent
    prompts_dir = REPO_ROOT / "PM_Pack/automation/prompts"
    prompts_dir.mkdir(parents=True, exist_ok=True)

    for agent in manifest["agents"]:
        stub_path = prompts_dir / f"CYCLE_{next_cycle:03d}_AGENT_{agent}_PROMPT.md"
        if not stub_path.exists():
            stub_path.write_text(
                f"# Cycle {next_cycle:03d} Agent {agent} Prompt\n\n"
                f"[STUB — populate from PM_Pack PROMPT_TEMPLATE.md + Jira board inventory]\n\n"
                f"Branch: {branch}\n"
                f"Generated: {_now()}\n"
            )

    click.echo(f"  Cycle           : {next_cycle:03d}")
    click.echo(f"  Branch          : {branch}")
    click.echo(f"  Agents          : {manifest['agents']}")
    click.echo(f"  Run ID          : {run_id}")
    click.echo()
    click.echo(f"  Manifest        : {manifest_path}")
    click.echo(f"  Prompt stubs    : PM_Pack/automation/prompts/CYCLE_{next_cycle:03d}_AGENT_*.md")
    click.echo()
    click.secho(f"PLAN CYCLE {'DRY RUN ' if dry_run else ''}COMPLETE", fg="green", bold=True)

    _write_runner_state({
        "runner": "fiverr-runner-local-01",
        "last_run_id": run_id,
        "last_successful_state": "CYCLE_PLAN",
        "active_cycle": next_cycle,
        "active_branch": branch,
        "active_pr": None,
        "status": "PLANNED",
        "last_heartbeat": _now(),
    })


@cli.command("cursor-smoke")
def cmd_cursor_smoke():
    """Run a no-write Cursor smoke test (reads context only)."""
    click.echo("=" * 60)
    click.echo("CURSOR CLI SMOKE TEST")
    click.echo("=" * 60)

    from automation.cursor_adapter import discover, check_version
    info = discover()
    version = check_version()
    click.echo(f"  Cursor version  : {version}")
    click.echo(f"  Discovery log   : C:/AI_Runner/logs/cursor_cli_discovery.txt")

    # Write a no-write smoke prompt
    smoke_prompt = (
        "You are running a smoke test only. Do NOT modify any files.\n"
        "Print the current working directory, list top-level files, "
        "and confirm PM_Pack exists. Do not write or commit anything.\n"
    )
    prompt_path = REPO_ROOT / "PM_Pack/automation/prompts/cursor_smoke_test.md"
    prompt_path.write_text(smoke_prompt)
    click.echo(f"  Smoke prompt    : {prompt_path}")
    click.echo()
    click.secho("Cursor CLI is reachable. Model and headless dispatch verified in Wave 04.", fg="green")


@cli.command("recover")
def cmd_recover():
    """Attempt safe recovery from stale lock or interrupted run."""
    click.echo("=" * 60)
    click.echo("RECOVER")
    click.echo("=" * 60)
    lock_dir = REPO_ROOT / "PM_Pack/automation/locks"
    if lock_dir.exists():
        locks = list(lock_dir.glob("*.lock"))
        if locks:
            for lf in locks:
                click.secho(f"  Found lock: {lf.name} — moving to stale_locks/", fg="yellow")
                stale_dir = lock_dir / "stale_locks"
                stale_dir.mkdir(exist_ok=True)
                from datetime import datetime as dt
                ts = dt.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
                lf.rename(stale_dir / f"{lf.stem}_{ts}.lock")
        else:
            click.echo("  No active locks found.")
    click.echo("  Run brain-check and compile-policy before restarting.")
    click.secho("RECOVER COMPLETE", fg="green")


@cli.command("tick")
def cmd_tick():
    """Scheduled tick — check state and decide next action."""
    click.echo(f"[TICK] {_now()}")
    state = _read_runner_state()
    status = state.get("status", "IDLE")
    click.echo(f"  Status: {status}")
    click.echo("  Tick loop not yet fully implemented — run commands manually for Wave 03.")


if __name__ == "__main__":
    cli()
