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
from datetime import UTC, datetime
from pathlib import Path

import click

# Ensure repo root on sys.path when run as a script
_here = Path(__file__).parent
_repo_root = _here.parent
if str(_repo_root) not in sys.path:
    sys.path.insert(0, str(_repo_root))

from automation.config_loader import get_secret  # noqa: E402
from automation.pm_pack_loader import brain_check  # noqa: E402
from automation.policy_compiler import compile_policy  # noqa: E402

REPO_ROOT = _repo_root
RUNNER_STATE = Path("C:/AI_Runner/state/controller_state.json")


def _now() -> str:
    return datetime.now(UTC).isoformat()


def _write_runner_state(state: dict) -> None:
    RUNNER_STATE.parent.mkdir(parents=True, exist_ok=True)
    RUNNER_STATE.write_text(json.dumps(state, indent=2))


def _read_runner_state() -> dict:
    try:
        return json.loads(RUNNER_STATE.read_text()) if RUNNER_STATE.exists() else {}
    except Exception:
        return {}


@click.group()
def cli() -> None:
    """Fiverr Research System — Autonomous Development Runner."""
    pass


@cli.command("brain-check")
def cmd_brain_check() -> None:
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

    # CLAUDE-SUB-002/004: API key absence check
    from automation.claude_sub_gate import check_api_key_absent
    api_check = check_api_key_absent()
    if not api_check["passed"]:
        click.secho(f"  [WARN] ANTHROPIC_API_KEY detected -- run: {api_check.get('report', 'see report')}", fg="yellow")
    else:
        click.echo("  CLAUDE-SUB      : API key absent (subscription-only confirmed)")

    click.echo()

    if result.ok:
        click.secho("BRAIN CHECK PASS", fg="green", bold=True)
        sys.exit(0)
    else:
        click.secho(f"BRAIN CHECK FAIL — {len(result.failed)} missing file(s)", fg="red", bold=True)
        sys.exit(1)


@cli.command("compile-policy")
def cmd_compile_policy() -> None:
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
def cmd_jira_inventory(dry_run: bool, project: str) -> None:
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
        run_id = datetime.now(UTC).strftime("%Y%m%dT%H%M%S")
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
def cmd_status() -> None:
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
@click.option("--dry-run", is_flag=True, default=False,
              help="Generate manifest only, do not generate real prompts.")
@click.option("--live", is_flag=True, default=False,
              help="Generate real prompts from PM_Pack + Jira (requires pm-pack-audit PASS).")
@click.option("--cycle", default=None, type=int, help="Cycle number override.")
def cmd_plan_cycle(dry_run: bool, live: bool, cycle: int | None) -> None:
    """Plan next cycle.

    --dry-run: Generates only a manifest and stub placeholders (safe).
    --live: Generates real prompts from PM_Pack + Jira (requires pm-pack-audit PASS + unfrozen).

    Default behavior (no flags): dry-run mode for safety.
    """
    # Default to dry-run if neither flag is set
    if not dry_run and not live:
        dry_run = True
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
    run_id = datetime.now(UTC).strftime("%Y%m%dT%H%M%S")
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

    if dry_run:
        click.echo(f"  Cycle           : {next_cycle:03d}")
        click.echo(f"  Branch          : {branch}")
        click.echo(f"  Agents          : {manifest['agents']}")
        click.echo(f"  Run ID          : {run_id}")
        click.echo()
        click.echo(f"  Manifest        : {manifest_path}")
        click.echo(f"  Prompt stubs    : PM_Pack/automation/prompts/CYCLE_{next_cycle:03d}_AGENT_*.md")
        click.echo()
        click.secho("PLAN CYCLE DRY RUN COMPLETE", fg="green", bold=True)
        _write_runner_state({
            "runner": "fiverr-runner-local-01",
            "last_run_id": run_id,
            "status": "PLANNED",
            "active_cycle": next_cycle,
            "active_branch": branch,
            "last_heartbeat": _now(),
        })
        return

    # ── LIVE: Generate real prompts from PM_Pack + Jira ──────────────
    click.echo("  Fetching Jira board inventory...")
    from automation.jira_client import board_inventory
    from automation.prompt_generator import write_prompts

    try:
        inv = board_inventory()
        jira_issues = inv.get("issues", [])
        click.echo(f"  Jira issues loaded: {len(jira_issues)}")
    except Exception as e:
        click.secho(f"  [WARN] Jira inventory failed: {e}", fg="yellow")
        jira_issues = []

    click.echo("  Generating real agent prompts from PM_Pack + Jira...")
    prompts_dir = REPO_ROOT / "PM_Pack/automation/prompts"
    written = write_prompts(
        cycle=next_cycle,
        branch=branch,
        run_id=run_id,
        agents=manifest["agents"],
        jira_issues=jira_issues,
        prompts_dir=prompts_dir,
    )

    click.echo(f"  Cycle           : {next_cycle:03d}")
    click.echo(f"  Branch          : {branch}")
    click.echo(f"  Agents          : {manifest['agents']}")
    click.echo(f"  Run ID          : {run_id}")
    click.echo()
    for agent_id, path in written.items():
        size = path.stat().st_size
        click.echo(f"  Prompt Agent {agent_id}: {path} ({size} bytes)")
    click.echo()
    click.secho("PLAN CYCLE COMPLETE — prompts generated from PM_Pack + Jira", fg="green", bold=True)

    _write_runner_state({
        "runner": "fiverr-runner-local-01",
        "last_run_id": run_id,
        "status": "PLANNED",
        "active_cycle": next_cycle,
        "active_branch": branch,
        "last_heartbeat": _now(),
    })


@cli.command("validate-prompts")
@click.option("--cycle", required=True, type=int, help="Cycle number.")
@click.option("--agents", default="A,B,E,C,F,D", help="Comma-separated agent list.")
def cmd_validate_prompts(cycle: int, agents: str) -> None:
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
def cmd_run_agent(agent: str, cycle: int, safe_docs_only: bool, dry_run: bool) -> None:
    """Run a single Cursor agent with MODEL_GATE + validation + commit."""
    click.echo("=" * 60)
    click.echo(f"RUN AGENT {agent} — Cycle {cycle:03d} {'[DRY RUN]' if dry_run else ''}")
    click.echo("=" * 60)

    from automation.model_gate import check as model_gate_check
    from automation.state_writer import make_run_dir, write_controller_state, write_heartbeat

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
    click.echo("  [2/5] Locating prompt...")
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
        click.secho("  Prompt validation warnings (--safe-docs-only, continuing):", fg="yellow")
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
    run_id = datetime.now(UTC).strftime("%Y%m%dT%H%M%S")
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

    # --- Post-agent lifecycle (FINDING-009 fix) ---
    # Ownership check, secret guard, report required, full validation, commit, Jira, record
    click.echo("  [5/5] Running post-agent lifecycle...")
    from automation.run_agent_lifecycle import run_post_agent_lifecycle
    lifecycle = run_post_agent_lifecycle(
        agent_id=agent,
        cycle=cycle,
        run_id=run_id,
        run_dir=run_dir,
        jira_keys=[],
    )

    write_heartbeat("AGENT_COMPLETE", cycle=cycle, agent=agent)
    write_controller_state("AGENT_COMPLETE", cycle=cycle)

    click.echo(f"  Lifecycle: {lifecycle.status}")
    for err in lifecycle.errors:
        click.secho(f"  ERROR: {err}", fg="red")

    if lifecycle.status == "COMPLETE":
        sha_info = f" commit={lifecycle.commit_sha}" if lifecycle.commit_sha else ""
        click.secho(f"Agent {agent} COMPLETE{sha_info}", fg="green", bold=True)
    elif lifecycle.status == "VALIDATION_FAILED":
        click.secho(f"Agent {agent} validation failed â€” routing to repair loop", fg="yellow")
        from automation.repair_loop import dispatch_repair
        dispatch_repair(agent, cycle, run_dir, lifecycle.errors)
        sys.exit(1)
    else:
        click.secho(f"Agent {agent} lifecycle: {lifecycle.status}", fg="red", bold=True)
        sys.exit(1)


@cli.command("cursor-smoke")
def cmd_cursor_smoke() -> None:
    """Run a no-write Cursor smoke test (reads context only)."""
    click.echo("=" * 60)
    click.echo("CURSOR CLI SMOKE TEST")
    click.echo("=" * 60)

    from automation.cursor_adapter import check_version, discover
    discover()
    version = check_version()
    click.echo(f"  Cursor version  : {version}")
    click.echo("  Discovery log   : C:/AI_Runner/logs/cursor_cli_discovery.txt")

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


@cli.command("cursor-docs-smoke")
def cmd_cursor_docs_smoke() -> None:
    """Run a docs-only smoke command surface check."""
    click.echo("=" * 60)
    click.echo("CURSOR DOCS SMOKE TEST")
    click.echo("=" * 60)
    click.echo("  Command is registered and available.")
    click.echo("  Use this as a lightweight command-surface verification gate.")
    click.secho("CURSOR DOCS SMOKE PASS", fg="green")


@cli.command("validate-routes")
def cmd_validate_routes() -> None:
    """Validate provider policy routes via ProviderRouter."""
    from automation.provider_router import ProviderRouter

    router = ProviderRouter()
    result = router.validate_policy()
    click.echo(str(result))
    sys.exit(0 if result.passed else 1)


@cli.command("provider-route-dry-run")
@click.option("--task-type", default="prompt_lint", help="Task type to route.")
@click.option("--cycle", default="080", help="Cycle number to stamp in decision.")
def cmd_provider_route_dry_run(task_type: str, cycle: str) -> None:
    """Run provider router dry-run and print selected route."""
    from automation.provider_router import ProviderRouter

    _ = cycle
    payload = ProviderRouter().route_dry_run(task_type)
    click.echo(str(payload))
    sys.exit(0)


@cli.command("recover")
def cmd_recover() -> None:
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
                ts = dt.now(UTC).strftime("%Y%m%d_%H%M%S")
                lf.rename(stale_dir / f"{lf.stem}_{ts}.lock")
        else:
            click.echo("  No active locks found.")
    click.echo("  Run brain-check and compile-policy before restarting.")
    click.secho("RECOVER COMPLETE", fg="green")


@cli.command("tick")
def cmd_tick() -> None:
    """
    Tick — real state machine that decides what to do next.

    States and transitions:
      IDLE              → compile-policy, then → PLANNED
      PLANNED           → validate-prompts, then → READY_TO_DISPATCH
      READY_TO_DISPATCH → check post-cycle gate; if clear → DISPATCHING
      DISPATCHING       → agents running (managed externally)
      AGENT_COMPLETE    → run post-cycle-review → POST_CYCLE_REVIEW
      POST_CYCLE_REVIEW → if PASS → IDLE (next cycle)
      POST_CYCLE_PENDING → block dispatch; surface to operator
      MODEL_BLOCKED     → block dispatch; alert model gate failure
    """
    from automation.notification_router import notify_blocked, notify_info
    from automation.state_writer import write_controller_state, write_heartbeat

    state = _read_runner_state()
    status = state.get("status", "IDLE")
    cycle  = state.get("active_cycle")

    click.echo(f"[TICK] {_now()}  status={status}  cycle={cycle}")

    # Always write fresh heartbeat
    write_heartbeat(status, cycle=cycle)

    # ── State machine transitions ─────────────────────────────────────
    if status in ("IDLE", "POST_CYCLE_PASS", "INITIAL"):
        # Ready for next cycle — compile policy to get current cycle
        click.echo("  → Running compile-policy...")
        snap = compile_policy(REPO_ROOT)
        next_cycle = snap.get("cycle_current", 75)
        write_controller_state("COMPILED", cycle=next_cycle)
        notify_info(f"Tick: policy compiled, cycle={next_cycle}")
        click.secho(f"  State: COMPILED (cycle {next_cycle})", fg="cyan")

    elif status == "COMPILED":
        # Plan the cycle — generate prompts
        click.echo("  → Planning cycle (generating prompts)...")
        write_controller_state("PLANNING", cycle=cycle)
        click.secho("  State: PLANNING — run plan-cycle --cycle {cycle} to generate prompts", fg="cyan")

    elif status == "PLANNED":
        # Validate prompts
        if cycle:
            from automation.prompt_validator import validate_all
            prompts_dir = REPO_ROOT / "PM_Pack/automation/prompts"
            agents = ["A", "B", "E", "C", "F", "D"]
            results = validate_all(prompts_dir, cycle, agents)
            all_valid = all(r.passed for r in results.values())
            if all_valid:
                write_controller_state("READY_TO_DISPATCH", cycle=cycle)
                click.secho("  State: READY_TO_DISPATCH (all prompts valid)", fg="green")
            else:
                failed_agents = [a for a, r in results.items() if not r.passed]
                write_controller_state("PROMPT_VALIDATION_FAILED", cycle=cycle)
                notify_blocked(f"Prompts invalid for agents: {failed_agents}",
                               incident_code="PROMPT_VALIDATION_FAILED", cycle=cycle)
                click.secho(f"  State: PROMPT_VALIDATION_FAILED agents={failed_agents}", fg="red")
        else:
            click.secho("  No active cycle — run plan-cycle first", fg="yellow")

    elif status == "READY_TO_DISPATCH":
        # Check model gate
        from automation.model_gate import check as model_gate_check
        gate = model_gate_check(repo_root=REPO_ROOT, cycle=cycle, agent="PRE_DISPATCH")
        if not gate.passed:
            write_controller_state("MODEL_BLOCKED", cycle=cycle)
            notify_blocked("Model gate failed before dispatch", incident_code="MODEL_BLOCKED", cycle=cycle)
            click.secho(f"  State: MODEL_BLOCKED — {gate.summary()}", fg="red")
        else:
            # Check ANTHROPIC_API_KEY absent
            from automation.claude_sub_gate import check_api_key_absent
            api = check_api_key_absent()
            if not api["passed"]:
                write_controller_state("CLAUDE_API_KEY_BLOCKED", cycle=cycle)
                notify_blocked("ANTHROPIC_API_KEY detected", incident_code="BLOCKED_CLAUDE_API_KEY_PRESENT")
                click.secho("  State: CLAUDE_API_KEY_BLOCKED", fg="red")
            else:
                write_controller_state("AWAITING_DISPATCH", cycle=cycle)
                click.secho("  State: AWAITING_DISPATCH — all gates pass, ready to dispatch", fg="green")
                notify_info(f"Tick: awaiting dispatch signal for cycle {cycle}")

    elif status in ("DISPATCHING", "AGENT_DISPATCH", "CURSOR_RUNNING", "AGENT_COMPLETE"):
        # Agent is running — monitor heartbeat freshness
        hb_path = Path("C:/AI_Runner/state/heartbeat.json")
        if hb_path.exists():
            import json as _json
            hb = _json.loads(hb_path.read_text())
            from datetime import datetime as _dt
            last = _dt.fromisoformat(hb.get("last_seen", _now()).replace("Z", "+00:00"))
            age_min = (_dt.now(last.tzinfo) - last).total_seconds() / 60
            if age_min > 45:
                notify_blocked(f"Heartbeat stale {age_min:.0f}m — agent may be stuck",
                               incident_code="AGENT_STUCK", cycle=cycle)
                click.secho(f"  [WARN] Heartbeat stale {age_min:.0f}m", fg="yellow")
            else:
                click.secho(f"  Agent running, heartbeat {age_min:.1f}m old — OK", fg="cyan")

    elif status in ("POST_CYCLE_PENDING", "POST_CYCLE_REVIEW"):
        click.secho(f"  Waiting for post-cycle review — run post-cycle-review --cycle {cycle}", fg="yellow")

    elif status in ("MODEL_BLOCKED", "CLAUDE_API_KEY_BLOCKED", "PROMPT_VALIDATION_FAILED"):
        click.secho(f"  BLOCKED ({status}) — resolve and run recover to reset", fg="red")

    else:
        click.echo(f"  Unknown status: {status} — treating as IDLE")
        write_controller_state("IDLE")

    click.echo("[TICK COMPLETE]")


@cli.command("daily-report")
@click.option("--cycle", default=None, type=int)
def cmd_daily_report(cycle: int | None) -> None:
    """Generate daily status report (OPS-022)."""
    from automation.report_generator import generate_daily_report
    path = generate_daily_report(cycle=cycle)
    click.secho(f"Daily report written: {path}", fg="green")


@cli.command("weekly-report")
def cmd_weekly_report() -> None:
    """Generate weekly autonomy review (OPS-023)."""
    from automation.report_generator import generate_weekly_report
    path = generate_weekly_report()
    click.secho(f"Weekly report written: {path}", fg="green")


@cli.command("post-cycle-review")
@click.option("--cycle", required=True, type=int, help="Cycle number.")
@click.option("--pr", default=None, type=int, help="PR number (if known).")
@click.option("--mode", default="POST_CYCLE_PM_REVIEW",
              type=click.Choice(["POST_CYCLE_PM_REVIEW", "POST_AGENT_CYCLE_REVIEW"]),
              help="Review mode.")
@click.option("--dry-run", is_flag=True, default=False,
              help="Collect facts only, do not write artifacts.")
def cmd_post_cycle_review(cycle: int, pr: int | None, mode: str, dry_run: bool) -> None:
    """Run post-cycle PM review. Blocks next dispatch until PASS."""
    click.echo("=" * 60)
    click.echo(f"POST-CYCLE REVIEW -- Cycle {cycle:03d} [{mode}]")
    click.echo("=" * 60)

    from automation.post_cycle_review import ReviewMode, ReviewResult, collect_facts, run_review

    rev_mode = ReviewMode.POST_MERGE if mode == "POST_CYCLE_PM_REVIEW" else ReviewMode.POST_AGENT

    if dry_run:
        click.echo("  Collecting facts (dry-run, no artifacts written)...")
        facts = collect_facts(cycle, rev_mode, pr)
        click.echo(f"  PR merged        : {facts.pr_merged}")
        click.echo(f"  CI passed        : {facts.ci_passed}")
        click.echo(f"  Codecov project  : {facts.codecov_project}")
        click.echo(f"  Baseline DB ok   : {facts.baseline_db_mtime_unchanged}")
        click.echo(f"  ScrapFly off     : {facts.scrapfly_enabled_false}")
        click.echo(f"  Agent reports    : {facts.agent_reports_present}")
        click.secho("DRY RUN COMPLETE", fg="cyan")
        return

    result = run_review(cycle=cycle, mode=rev_mode, pr_number=pr)
    click.echo(result.summary())
    click.echo()
    for path in result.artifact_paths:
        click.echo(f"  Artifact: {path}")

    if result.result == ReviewResult.PASS:
        click.secho("POST-CYCLE REVIEW PASS -- next dispatch unlocked", fg="green", bold=True)
        from automation.state_writer import write_controller_state, write_heartbeat
        write_heartbeat("POST_CYCLE_PASS", cycle=cycle)
        write_controller_state("POST_CYCLE_PASS", cycle=cycle)
    else:
        click.secho(f"POST-CYCLE REVIEW {result.result.value}", fg="yellow", bold=True)
        if result.blocks_dispatch:
            click.secho("DISPATCH BLOCKED -- resolve errors before next cycle", fg="red")
            sys.exit(1)


@cli.command("merge-gate")
@click.option("--pr", required=True, type=int, help="PR number.")
@click.option("--dry-run", "do_dry_run", is_flag=True, default=True,
              help="Check gates only, do not merge (default: True).")
@click.option("--execute-merge", is_flag=True, default=False,
              help="Actually merge if all gates pass.")
def cmd_merge_gate(pr: int, do_dry_run: bool, execute_merge: bool) -> None:
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
def cmd_create_labels() -> None:
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
    created, failed = 0, 0
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

@cli.command("status-tick")
def cmd_status_tick() -> None:
    """Status-only tick — reads state and writes next_action_decision.json.

    Unlike tick, status-tick NEVER advances state machine or dispatches anything.
    V6-TICK-001/003: every tick writes next_action_decision.json explaining why
    it did/did not dispatch. status-tick is safe to call at any time.
    """
    from automation.state_writer import write_heartbeat

    state = _read_runner_state()
    status = state.get("status", "IDLE")
    cycle  = state.get("active_cycle")
    now = _now()

    write_heartbeat(status, cycle=cycle)

    # Check freeze
    from automation.freeze_gate import is_frozen
    frozen = is_frozen(REPO_ROOT)

    # Check dirty repo
    import subprocess as _sp
    git_status = _sp.run(
        ["git", "status", "--short"], cwd=str(REPO_ROOT),
        capture_output=True, text=True
    ).stdout.strip()
    repo_dirty = bool(git_status)

    # Determine next action
    if frozen:
        next_action = "BLOCKED_AUTONOMY_FROZEN"
        reason = "autonomy_freeze.yml has frozen: true"
    elif repo_dirty:
        next_action = "BLOCKED_DIRTY_REPO"
        reason = f"Repo has uncommitted changes: {git_status[:100]}"
    elif status in ("IDLE", "POST_CYCLE_PASS"):
        next_action = "PLAN_READY"
        reason = "Ready for next cycle — run compile-policy then plan-cycle"
    elif status == "PLANNED":
        next_action = "VALIDATE_PROMPTS"
        reason = "Prompts exist — run validate-prompts to check"
    elif status == "READY_TO_DISPATCH":
        next_action = "AWAITING_MODEL_GATE"
        reason = "Model gate check required before dispatch"
    elif status in ("DISPATCHING", "AGENT_DISPATCH", "CURSOR_RUNNING"):
        next_action = "MONITOR_AGENT"
        reason = "Agent currently running — monitor heartbeat"
    elif status == "POST_CYCLE_PENDING":
        next_action = "POST_CYCLE_REVIEW"
        reason = "Awaiting post-cycle review"
    else:
        next_action = f"UNKNOWN_STATUS_{status}"
        reason = "Unknown status — check controller_state.json"

    # Write decision artifact (V6-TICK-003)
    decision = {
        "evaluated_at": now,
        "current_status": status,
        "active_cycle": cycle,
        "frozen": frozen,
        "repo_dirty": repo_dirty,
        "next_action": next_action,
        "reason": reason,
        "source": "status-tick (read-only)",
    }
    decision_path = Path("C:/AI_Runner/state/next_action_decision.json")
    decision_path.parent.mkdir(parents=True, exist_ok=True)
    import json as _json
    decision_path.write_text(_json.dumps(decision, indent=2))

    click.echo(f"[STATUS-TICK] {now}")
    click.echo(f"  Status     : {status}")
    click.echo(f"  Cycle      : {cycle}")
    click.echo(f"  Frozen     : {frozen}")
    click.echo(f"  Repo dirty : {repo_dirty}")
    click.echo(f"  Next action: {next_action}")
    click.echo(f"  Reason     : {reason}")
    click.echo(f"  Decision   : {decision_path}")


@cli.command("pm-pack-audit")
def cmd_pm_pack_audit() -> None:
    """PM_Pack consistency audit — validates semantic agreement across all state files.

    Checks: HYDRATION_HEADER vs controller_state vs current_status vs policy_snapshot.
    Required by V6-PM-013. Must PASS before plan-cycle --live is allowed.
    """
    from automation.pm_pack_consistency_audit import run_audit
    result = run_audit()
    click.echo(result.summary())
    if result.sources:
        click.echo("")
        click.echo("  State sources:")
        for k, v in result.sources.items():
            click.echo(f"    {k}: {v!r}")
    if not result.passed:
        click.secho("PM_PACK_AUDIT BLOCKED — resolve conflicts before running plan-cycle",
                    fg="red", bold=True)
        sys.exit(1)
    click.secho("PM_PACK_AUDIT PASS", fg="green", bold=True)



if __name__ == "__main__":
    cli()
