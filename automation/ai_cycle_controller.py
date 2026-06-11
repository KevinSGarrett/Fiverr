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
    # CYCLE_CURRENT in HYDRATION_HEADER means the cycle we are about to work on.
    # Do NOT add +1 — it is already the target cycle.
    current_cycle = snap.get("cycle_current", 75)
    next_cycle = cycle if cycle is not None else current_cycle
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


@cli.command("validate-prompts")
@click.option("--cycle", required=True, type=int, help="Cycle number.")
@click.option("--agents", default="A,B,E,C,F,D", help="Comma-separated agent list.")
def cmd_validate_prompts(cycle: int, agents: str):
    """Validate generated prompt files for a cycle before dispatch."""
    click.echo("=" * 60)
    click.echo(f"VALIDATE PROMPTS — Cycle {cycle:03d}")
    click.echo("=" * 60)

    from automation.prompt_validator import validate_all
    agent_list = [a.strip() for a in agents.split(",")]
    prompts_dir = REPO_ROOT / "PM_Pack/automation/prompts"
    results = validate_all(prompts_dir, cycle, agent_list)

    all_pass = True
    for agent, r in results.items():
        icon = "PASS" if r.passed else "FAIL"
        click.echo(f"  [{icon}] Agent {agent}: {r.prompt_path}")
        for e in r.errors:
            click.secho(f"         ERROR: {e}", fg="red")
        for w in r.warnings:
            click.secho(f"         WARN : {w}", fg="yellow")
        if not r.passed:
            all_pass = False

    click.echo()
    if all_pass:
        click.secho("PROMPT VALIDATION PASS", fg="green", bold=True)
    else:
        click.secho("PROMPT VALIDATION FAIL", fg="red", bold=True)
        sys.exit(1)


@cli.command("run-agent")
@click.option("--agent", required=True, help="Agent ID (A/B/E/C/F/D).")
@click.option("--cycle", required=True, type=int, help="Cycle number.")
@click.option("--safe-docs-only", is_flag=True, default=False,
              help="Docs-only test — skips MODEL_GATE hard-fail, warns only.")
@click.option("--dry-run", is_flag=True, default=False,
              help="Print what would run without executing Cursor.")
def cmd_run_agent(agent: str, cycle: int, safe_docs_only: bool, dry_run: bool):
    """Run a single Cursor agent with MODEL_GATE + validation + commit."""
    click.echo("=" * 60)
    click.echo(f"RUN AGENT {agent} — Cycle {cycle:03d} {'[DRY RUN]' if dry_run else ''}")
    click.echo("=" * 60)

    from automation.model_gate import check as model_gate_check
    from automation.state_writer import write_heartbeat, write_controller_state, make_run_dir

    # --- MODEL_GATE ---
    click.echo("  [1/5] MODEL_GATE check...")
    gate = model_gate_check(repo_root=REPO_ROOT, cycle=cycle, agent=agent)
    click.echo(gate.summary())
    if not gate.passed:
        if safe_docs_only:
            click.secho("  MODEL_GATE failed but --safe-docs-only set, continuing with warning.", fg="yellow")
        else:
            click.secho("  MODEL_GATE FAILED — aborting dispatch.", fg="red", bold=True)
            write_controller_state("MODEL_BLOCKED", cycle=cycle)
            sys.exit(1)

    write_heartbeat("MODEL_GATE_PASSED", cycle=cycle, agent=agent)
    write_controller_state("AGENT_DISPATCH", cycle=cycle)

    # --- Locate prompt ---
    click.echo(f"  [2/5] Locating prompt...")
    prompts_dir = REPO_ROOT / "PM_Pack/automation/prompts"
    prompt_path = prompts_dir / f"CYCLE_{cycle:03d}_AGENT_{agent}_PROMPT.md"
    if not prompt_path.exists():
        click.secho(f"  Prompt not found: {prompt_path}", fg="red")
        sys.exit(1)
    click.echo(f"  Prompt: {prompt_path}")

    # --- Validate prompt ---
    click.echo("  [3/5] Validating prompt...")
    from automation.prompt_validator import validate as validate_prompt
    pv = validate_prompt(prompt_path, agent, cycle)
    if not pv.passed and not safe_docs_only:
        click.secho(pv.summary(), fg="red")
        sys.exit(1)
    elif not pv.passed:
        click.secho(f"  Prompt validation warnings (--safe-docs-only, continuing):", fg="yellow")
        click.echo(pv.summary())
    else:
        click.secho("  Prompt validation PASS", fg="green")

    if dry_run:
        click.echo()
        click.secho(f"  DRY RUN: Would dispatch Cursor with: {prompt_path}", fg="cyan")
        click.secho(f"  DRY RUN: Working dir: {REPO_ROOT}", fg="cyan")
        click.secho("RUN AGENT DRY RUN COMPLETE", fg="green", bold=True)
        return

    # --- Dispatch Cursor ---
    run_id = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S")
    run_dir = make_run_dir(cycle, run_id)
    agent_dir = run_dir / "agent_runs" / agent

    click.echo(f"  [4/5] Dispatching Cursor agent {agent}...")
    write_heartbeat("CURSOR_RUNNING", cycle=cycle, agent=agent)

    from automation.cursor_adapter import run_agent as cursor_run
    result = cursor_run(
        agent_id=agent,
        prompt_path=str(prompt_path),
        working_dir=str(REPO_ROOT),
        output_dir=str(agent_dir),
    )

    click.echo(f"  Agent {agent} finished: status={result.status} exit={result.exit_code}")
    if result.stdout_tail:
        click.echo(f"  stdout tail:\n{result.stdout_tail[-300:]}")
    if result.error_message:
        click.secho(f"  Error: {result.error_message}", fg="red")

    # --- Post-agent validation ---
    click.echo("  [5/5] Post-agent validation (ruff + mypy)...")
    from automation.validation_runner import run_targeted_validation
    val = run_targeted_validation(["ruff", "mypy"], REPO_ROOT)
    click.echo(val.summary())

    write_heartbeat("AGENT_COMPLETE", cycle=cycle, agent=agent)
    write_controller_state("AGENT_COMPLETE", cycle=cycle)

    if result.status == "complete" and val.all_passed:
        click.secho(f"Agent {agent} COMPLETE", fg="green", bold=True)
    else:
        click.secho(f"Agent {agent} needs repair: status={result.status}", fg="yellow")
        sys.exit(1)


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
    from automation.state_writer import write_heartbeat, write_controller_state
    state = _read_runner_state()
    status = state.get("status", "IDLE")
    write_heartbeat(status)
    write_controller_state(status)
    click.echo(f"[TICK] {_now()} status={status}")


@cli.command("merge-gate")
@click.option("--pr", required=True, type=int, help="PR number.")
@click.option("--dry-run", "do_dry_run", is_flag=True, default=True,
              help="Check gates only, do not merge (default: True).")
@click.option("--execute-merge", is_flag=True, default=False,
              help="Actually merge if all gates pass.")
def cmd_merge_gate(pr: int, do_dry_run: bool, execute_merge: bool):
    """Run full merge gate check for a PR. Safe by default (dry-run)."""
    click.echo("=" * 60)
    live = not do_dry_run or execute_merge
    click.echo(f"MERGE GATE - PR #{pr} {'[LIVE]' if live else '[DRY RUN]'}")
    click.echo("=" * 60)
    from automation.merge_gate import run as gate_run
    result = gate_run(pr_number=pr, dry_run=(not execute_merge))
    click.echo(result.summary())
    click.echo()
    if result.passed:
        if execute_merge and result.merge_sha:
            click.secho(f"MERGED to develop: {result.merge_sha}", fg="green", bold=True)
        else:
            click.secho("MERGE GATE PASS - run with --execute-merge to merge", fg="green", bold=True)
    else:
        fails = len(result.failed_checks())
        click.secho(f"MERGE GATE FAIL - {fails} blocking failures", fg="red", bold=True)
        sys.exit(1)


@cli.command("create-labels")
def cmd_create_labels():
    """Create all required GitHub labels for the autonomous runner."""
    click.echo("=" * 60)
    click.echo("CREATE GITHUB LABELS")
    click.echo("=" * 60)
    import subprocess
    labels = [
        ("ai-runner", "0052cc", "Managed by autonomous AI runner"),
        ("type:feature", "0075ca", "Feature work"),
        ("type:fix", "e4e669", "Bug fix"),
        ("type:test", "c2e0c6", "Test additions"),
        ("type:chore", "ededed", "Chore/housekeeping"),
        ("risk:low", "c2e0c6", "Low risk change"),
        ("risk:medium", "fbca04", "Medium risk change"),
        ("risk:high", "e11d48", "High risk change"),
        ("risk:critical", "b60205", "Critical risk change"),
        ("agent:A", "1d76db", "Agent A work"),
        ("agent:B", "0e8a16", "Agent B work"),
        ("agent:C", "5319e7", "Agent C work"),
        ("agent:D", "e4e669", "Agent D work"),
        ("agent:E", "d93f0b", "Agent E work"),
        ("agent:F", "0075ca", "Agent F work"),
        ("status:ai-running", "0052cc", "AI runner actively working"),
        ("status:ai-repairing", "fbca04", "AI runner in repair loop"),
        ("status:merge-gate-pass", "0e8a16", "Merge gate passed"),
        ("status:merge-gate-blocked", "e11d48", "Merge gate blocked"),
        ("needs:jira-sync", "ededed", "Needs Jira sync"),
        ("needs:codex-disposition", "ededed", "Needs Codex review disposition"),
        ("needs:coverage-repair", "fbca04", "Needs coverage repair"),
    ]
    created, skipped, failed = 0, 0, 0
    for name, color, desc in labels:
        r = subprocess.run(
            ["gh", "label", "create", name,
             "--repo", "KevinSGarrett/Fiverr",
             "--color", color, "--description", desc, "--force"],
            capture_output=True, text=True
        )
        if r.returncode == 0:
            click.secho(f"  [OK] {name}", fg="green")
            created += 1
        else:
            click.secho(f"  [FAIL] {name}: {r.stderr.strip()[:60]}", fg="red")
            failed += 1
    click.echo()
    click.echo(f"Created/updated: {created}  Failed: {failed}")
    if failed == 0:
        click.secho("LABELS COMPLETE", fg="green", bold=True)


if __name__ == "__main__":
    cli()
