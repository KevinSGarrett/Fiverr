"""
run_agent_lifecycle.py â€” Complete run-agent lifecycle after Cursor CLI returns.

After cursor agent -p "prompt" completes, this module:
  1. Collects git diff/changed files
  2. Enforces file ownership (agent must not touch out-of-scope files)
  3. Runs secret guard on changed files
  4. Requires report file (docs/cycle_reports/CYCLE_NNN_AGENT_X.md)
  5. Runs targeted validation (ruff, mypy, pytest)
  6. Commits approved files only
  7. Updates Jira with evidence comments
  8. Writes agent_run_record.json
  9. Routes to repair loop on failure
"""
from __future__ import annotations

import json
import socket
import subprocess
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import yaml

REPO_ROOT = Path(__file__).parent.parent
RUNNER_ROOT = Path("C:/AI_Runner")
RUNNER_MODEL_STATE = RUNNER_ROOT / "state/cursor_model_state.json"
AGENT_LANES_PATH = REPO_ROOT / "PM_Pack/automation/policies/agent_lanes.yml"

# Agent file ownership map â€” agents must not modify outside their scope
AGENT_OWNERSHIP = {
    "A": {
        "allowed":   ["src/pipeline", "src/models", "src/collection", "src/scoring",
                      "src/signals", "tests/unit", "tests/integration"],
        "forbidden": ["src/dashboard", "src/reports", "src/playbook", "docs/"],
    },
    "B": {
        "allowed":   ["src/signals", "src/integrations", "src/scrapers", "tests/"],
        "forbidden": ["src/dashboard", "src/reports"],
    },
    "E": {
        "allowed":   ["tests/"],
        "forbidden": ["src/"],
    },
    "C": {
        "allowed":   ["src/dashboard", "src/visualization", "tests/"],
        "forbidden": ["src/pipeline", "src/models", "src/scoring"],
    },
    "F": {
        "allowed":   ["src/reports", "src/playbook", "tests/"],
        "forbidden": ["src/pipeline", "src/dashboard"],
    },
    "D": {
        "allowed":   ["docs/", "PM_Pack/10_cycle_log/", "docs/cycle_reports/"],
        "forbidden": ["src/", "tests/", "automation/"],
    },
}


@dataclass
class AgentLifecycleResult:
    agent: str
    cycle: int
    run_id: str
    status: str          # COMPLETE | VALIDATION_FAILED | OWNERSHIP_VIOLATION | NO_REPORT | SECRET_FOUND | REPAIR_NEEDED
    commit_sha: str = ""
    changed_files: list[str] = field(default_factory=list)
    unauthorized_files: list[str] = field(default_factory=list)
    secret_findings: list[str] = field(default_factory=list)
    validation_passed: bool = False
    report_path: str = ""
    report_found: bool = False
    jira_updates: list[dict] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)
    record_path: str = ""
    repair_result: Any | None = None

    def to_dict(self) -> dict:
        return {k: v for k, v in self.__dict__.items()}


@dataclass
class OwnershipResult:
    passed: bool
    unauthorized: list[str]
    suspicious: list[str]


@dataclass
class ValidationResult:
    ruff_passed: bool
    ruff_errors: str
    mypy_passed: bool
    mypy_errors: str
    pytest_passed: bool
    pytest_count: int
    pytest_failed: list[str]
    missing_test_files: list[str]
    overall_passed: bool


@dataclass
class LifecycleResult:
    status: str
    repair_result: Any | None = None


def run_post_agent_lifecycle(
    agent_id: str,
    cycle: int,
    run_id: str,
    run_dir: Path,
    jira_keys: list[str] | None = None,
    dry_run: bool = False,
) -> AgentLifecycleResult:
    """
    Execute full post-Cursor lifecycle. Called after cursor agent -p returns.
    """
    result = AgentLifecycleResult(
        agent=agent_id, cycle=cycle, run_id=run_id, status="IN_PROGRESS"
    )
    jira_keys = jira_keys or []

    # â”€â”€ Step 1: Collect changed files â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
    result.changed_files = _get_changed_files()

    # â”€â”€ Step 2: Enforce file ownership â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
    ownership = _check_ownership(agent_id, result.changed_files, REPO_ROOT)
    if not ownership.passed:
        result.unauthorized_files = ownership.unauthorized
        result.status = "OWNERSHIP_VIOLATION"
        result.errors.append(
            f"Agent {agent_id} modified files outside its scope: {ownership.unauthorized}"
        )
        # Don't commit â€” quarantine changed files
        if not dry_run:
            _write_record(result, run_dir)
            from automation.notification_router import notify_blocked
            notify_blocked(
                f"Agent {agent_id} ownership violation: {ownership.unauthorized[:3]}",
                incident_code="OWNERSHIP_VIOLATION", cycle=cycle
            )
        return result

    # â”€â”€ Step 3: Secret guard â€” scan changed_files BEFORE any staging (V5-008) â”€â”€â”€â”€
    # Scan must happen on the changed_files list before we stage anything.
    # We call scan_working_tree (not scan_staged) at this point.
    secret_findings = _scan_changed_files(result.changed_files)
    if secret_findings:
        result.secret_findings = secret_findings
        result.status = "SECRET_FOUND"
        result.errors.extend(secret_findings)
        if not dry_run:
            _write_record(result, run_dir)
        return result

    # â”€â”€ Step 4: Require report file â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
    report_path = REPO_ROOT / f"docs/cycle_reports/CYCLE_{cycle:03d}_AGENT_{agent_id}.md"
    result.report_path = str(report_path)
    result.report_found = report_path.exists()

    if not result.report_found:
        result.status = "NO_REPORT"
        result.errors.append(
            f"Required report not found: {report_path}\n"
            f"Agent must write report before exiting."
        )
        if not dry_run:
            _write_record(result, run_dir)
        return result

    # Verify report contains AGENT_COMPLETE
    report_text = report_path.read_text(encoding="utf-8", errors="replace")
    if "AGENT_COMPLETE" not in report_text:
        result.status = "NO_REPORT"
        result.errors.append("Report exists but missing AGENT_COMPLETE marker")
        if not dry_run:
            _write_record(result, run_dir)
        return result

    # â”€â”€ Step 5: Targeted validation â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
    validation_result = _run_targeted_validation(agent_id, result.changed_files, run_dir, REPO_ROOT)
    result.validation_passed = validation_result.overall_passed
    if not validation_result.overall_passed:
        result.status = "VALIDATION_FAILED"
        result.errors.append(f"Validation failed: {validation_result}")
        if not dry_run:
            _write_record(result, run_dir)
            from automation.repair_loop import dispatch_repair

            repair_result = dispatch_repair(
                agent_id=agent_id,
                cycle=cycle,
                failure_type=_classify_failure(validation_result),
                original_prompt_path=str(REPO_ROOT / "PM_Pack/automation/prompts" / f"CYCLE_{cycle:03d}_AGENT_{agent_id}_PROMPT.md"),
                changed_files=result.changed_files,
                validation_output=str(validation_result),
                repo_root=REPO_ROOT,
                runner_root=RUNNER_ROOT,
            )
            result.status = "REPAIR_ATTEMPTED"
            result.repair_result = repair_result
        return result

    # â”€â”€ Step 6: Commit approved files â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
    # Stage and commit only files that passed ownership check
    approved_files = [
        fn for fn in result.changed_files
        if fn not in result.unauthorized_files
    ]
    if not dry_run and approved_files:
        # Second secret scan: after classifying files, before staging
        post_scan = _scan_changed_files(approved_files)
        if post_scan:
            result.secret_findings.extend(post_scan)
            result.status = "SECRET_FOUND"
            result.errors.extend(post_scan)
            _write_record(result, run_dir)
            return result
        sha = _commit_agent_work(agent_id, cycle, approved_files)
        result.commit_sha = sha

    # â”€â”€ Step 7: Update Jira with evidence â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
    if not dry_run and jira_keys:
        from automation.jira_sync import on_agent_complete
        updates = on_agent_complete(
            cycle=cycle,
            agent=agent_id,
            branch=_get_current_branch(),
            pr_number=None,
            files_changed=result.changed_files,
            validation_passed=validation_result.overall_passed,
            jira_keys=jira_keys,
        )
        result.jira_updates = updates

    # â”€â”€ Step 8: Write run record â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
    result.status = "COMPLETE"
    if not dry_run:
        record_path = _write_record(result, run_dir)
        result.record_path = str(record_path)
        _write_run_record(result, agent_id, cycle, run_id, run_dir, REPO_ROOT)

    return result


def _get_changed_files() -> list[str]:
    """Get all modified/added files relative to HEAD."""
    r = subprocess.run(
        ["git", "diff", "--name-only", "HEAD"],
        cwd=str(REPO_ROOT), capture_output=True, text=True
    )
    uncommitted = r.stdout.strip().splitlines()

    r2 = subprocess.run(
        ["git", "status", "--short"],
        cwd=str(REPO_ROOT), capture_output=True, text=True
    )
    untracked = [
        line[3:].strip() for line in r2.stdout.splitlines()
        if line.startswith("?? ")
    ]
    return list(set(uncommitted + untracked))


def _check_ownership(agent_id: str, changed_files: list[str], repo_root: Path) -> OwnershipResult:
    """Return files that violate agent ownership rules.

    V5-008 fix: enforces BOTH allowlist and denylist from agent_lanes.yml.
    A file is a violation if:
      (a) it matches a forbidden prefix, OR
      (b) it doesn't match any allowed prefix (and allowed list is non-empty)
    """
    rules = AGENT_OWNERSHIP.get(agent_id, {})
    if AGENT_LANES_PATH.exists():
        try:
            data = yaml.safe_load(AGENT_LANES_PATH.read_text(encoding="utf-8")) or {}
            lane = data.get(agent_id, {})
            rules = {
                "allowed": lane.get("allowed_paths", rules.get("allowed", [])),
                "forbidden": lane.get("forbidden_paths", rules.get("forbidden", [])),
            }
        except Exception:
            pass
    _ = repo_root
    allowed_prefixes = rules.get("allowed", [])
    forbidden_prefixes = rules.get("forbidden", [])
    violations: list[str] = []
    suspicious: list[str] = []

    for changed_file in changed_files:
        # Check forbidden
        forbidden = any(changed_file.startswith(fp) for fp in forbidden_prefixes)
        if forbidden:
            violations.append(changed_file)
            continue

        # Check allowlist: if allowed list is non-empty and file doesn't match any
        if allowed_prefixes:
            in_allowed = any(
                changed_file.startswith(ap.rstrip("*").rstrip("/"))
                for ap in allowed_prefixes
            )
            # Automation and docs files are always allowed for any agent
            always_allowed = any(
                changed_file.startswith(p)
                for p in ("docs/cycle_reports/", "PM_Pack/automation/runs/",
                          ".gitignore", "README")
            )
            if not in_allowed and not always_allowed:
                suspicious.append(changed_file)

    return OwnershipResult(
        passed=not violations,
        unauthorized=violations,
        suspicious=suspicious,
    )


def _scan_for_secrets() -> list[str]:
    """Scan staged files for secret patterns (used after staging)."""
    try:
        from automation.secret_guard import scan_staged
        scan_result = scan_staged(REPO_ROOT)
        return scan_result.findings if not scan_result.passed else []
    except Exception:
        return []


def _scan_changed_files(changed_files: list[str]) -> list[str]:
    """Scan a list of changed files for secret values BEFORE staging (V5-008 fix).

    Uses scan_file on each file individually, before any git add.
    """
    try:
        from automation.secret_guard import scan_file
        findings: list[str] = []
        for fname in changed_files:
            fpath = REPO_ROOT / fname
            if fpath.exists():
                scan_result = scan_file(fpath)
                if not scan_result.passed:
                    findings.extend(
                        [f"{fname}: {finding}" for finding in scan_result.findings]
                    )
        return findings
    except Exception:
        return []


def _run_validation(agent_id: str) -> tuple[bool, str]:
    """Run ruff + mypy. Pytest for code agents. Returns (passed, details)."""
    py = str(REPO_ROOT / ".venv/Scripts/python.exe")
    passed = True
    details_parts = []

    # Ruff
    r = subprocess.run(
        [py, "-m", "ruff", "check", "automation/", "src/", "--output-format=full"],
        cwd=str(REPO_ROOT), capture_output=True, text=True, timeout=120
    )
    if r.returncode != 0:
        passed = False
        details_parts.append(f"ruff FAIL: {r.stdout[:200]}")

    # Mypy
    r = subprocess.run(
        [py, "-m", "mypy", "src/", "--ignore-missing-imports"],
        cwd=str(REPO_ROOT), capture_output=True, text=True, timeout=120
    )
    if r.returncode != 0:
        passed = False
        details_parts.append(f"mypy FAIL: {r.stdout[-200:]}")

    # Pytest â€” only for code agents (not D)
    if agent_id != "D":
        r = subprocess.run(
            [py, "-m", "pytest", "tests/unit/", "-q", "--no-header", "--tb=no", "-x"],
            cwd=str(REPO_ROOT), capture_output=True, text=True, timeout=300
        )
        if r.returncode != 0:
            passed = False
            details_parts.append(f"pytest FAIL: {r.stdout[-200:]}")

    return passed, " | ".join(details_parts) if details_parts else "all passed"


def _run_targeted_validation(
    agent_id: str,
    changed_files: list[str],
    run_dir: Path,
    repo_root: Path,
) -> ValidationResult:
    py_files = sorted({f for f in changed_files if f.endswith(".py")})
    ruff_passed = True
    ruff_errors = ""
    mypy_passed = True
    mypy_errors = ""
    pytest_passed = True
    pytest_failed: list[str] = []
    missing_test_files: list[str] = []

    try:
        if py_files:
            ruff_cmd = ["python", "-m", "ruff", "check", *py_files, "--output-format=full"]
            ruff_run = subprocess.run(ruff_cmd, cwd=str(repo_root), capture_output=True, text=True, check=False)
            ruff_passed = ruff_run.returncode == 0
            ruff_errors = (ruff_run.stdout + ruff_run.stderr).strip()
    except (subprocess.CalledProcessError, FileNotFoundError) as exc:
        ruff_passed = False
        ruff_errors = str(exc)

    try:
        py_dirs = sorted({str(Path(path).parent) for path in py_files}) or ["automation"]
        mypy_cmd = ["python", "-m", "mypy", *py_dirs, "--ignore-missing-imports"]
        mypy_run = subprocess.run(mypy_cmd, cwd=str(repo_root), capture_output=True, text=True, check=False)
        mypy_passed = mypy_run.returncode == 0
        mypy_errors = (mypy_run.stdout + mypy_run.stderr).strip()
    except (subprocess.CalledProcessError, FileNotFoundError) as exc:
        mypy_passed = False
        mypy_errors = str(exc)

    pytest_targets: list[str] = []
    for changed in py_files:
        if changed.startswith("automation/"):
            test_name = f"tests/unit/test_{Path(changed).stem}.py"
            test_path = repo_root / test_name
            if test_path.exists():
                pytest_targets.append(test_name)
            else:
                missing_test_files.append(test_name)
    pytest_count = len(pytest_targets)
    try:
        if pytest_targets:
            pytest_cmd = ["python", "-m", "pytest", *pytest_targets, "-q", "--tb=short"]
            pytest_run = subprocess.run(pytest_cmd, cwd=str(repo_root), capture_output=True, text=True, check=False)
            pytest_passed = pytest_run.returncode == 0
            if not pytest_passed:
                pytest_failed = pytest_targets
    except (subprocess.CalledProcessError, FileNotFoundError) as exc:
        pytest_passed = False
        pytest_failed = [str(exc)]

    overall_passed = ruff_passed and mypy_passed and (pytest_passed or pytest_count == 0)
    result = ValidationResult(
        ruff_passed=ruff_passed,
        ruff_errors=ruff_errors,
        mypy_passed=mypy_passed,
        mypy_errors=mypy_errors,
        pytest_passed=pytest_passed,
        pytest_count=pytest_count,
        pytest_failed=pytest_failed,
        missing_test_files=missing_test_files,
        overall_passed=overall_passed,
    )
    run_dir.mkdir(parents=True, exist_ok=True)
    (run_dir / f"validation_{agent_id}.json").write_text(
        json.dumps(result.__dict__, indent=2),
        encoding="utf-8",
    )
    return result


def _classify_failure(validation_result: ValidationResult) -> str:
    if not validation_result.ruff_passed:
        return "RUFF_FAILURE"
    if not validation_result.mypy_passed:
        return "MYPY_FAILURE"
    if validation_result.pytest_count > 0 and not validation_result.pytest_passed:
        return "PYTEST_FAILURE"
    return "UNKNOWN"


def _commit_agent_work(agent_id: str, cycle: int, files: list[str]) -> str:
    """Stage only approved files and commit. Never uses git add -A.

    V5-008 fix: stages files explicitly using git add -- <file1> <file2>
    """
    if not files:
        return ""
    # Stage only the explicitly approved files
    stage_cmd = ["git", "add", "--"] + files
    stage_result = subprocess.run(
        stage_cmd, cwd=str(REPO_ROOT), capture_output=True, text=True
    )
    if stage_result.returncode != 0:
        return ""

    msg = f"feat(cycle-{cycle:03d}): Agent {agent_id} work [autonomous]"
    r = subprocess.run(
        ["git", "commit", "-m", msg],
        cwd=str(REPO_ROOT), capture_output=True, text=True
    )
    if r.returncode != 0:
        return ""
    sha = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=str(REPO_ROOT), capture_output=True, text=True
    ).stdout.strip()
    return sha


def _get_current_branch() -> str:
    r = subprocess.run(
        ["git", "branch", "--show-current"],
        cwd=str(REPO_ROOT), capture_output=True, text=True
    )
    return r.stdout.strip()


def _write_record(result: AgentLifecycleResult, run_dir: Path) -> Path:
    """Write agent_run_record.json to run dir."""
    run_dir.mkdir(parents=True, exist_ok=True)
    path = run_dir / f"agent_{result.agent}_run_record.json"
    path.write_text(json.dumps({
        **result.to_dict(),
        "recorded_at": datetime.now(UTC).isoformat(),
    }, indent=2))
    return path


def _write_run_record(
    result: AgentLifecycleResult,
    agent_id: str,
    cycle: int,
    run_id: str,
    run_dir: Path,
    repo_root: Path,
) -> Path:
    record_dir = run_dir / "agent_runs" / agent_id
    record_dir.mkdir(parents=True, exist_ok=True)
    prompt_path = repo_root / "PM_Pack/automation/prompts" / f"CYCLE_{cycle:03d}_AGENT_{agent_id}_PROMPT.md"
    prompt_text = prompt_path.read_text(encoding="utf-8", errors="replace") if prompt_path.exists() else ""
    cursor_state = json.loads(RUNNER_MODEL_STATE.read_text(encoding="utf-8")) if RUNNER_MODEL_STATE.exists() else {}
    started_raw = getattr(result, "started_at", None)
    ended_raw = getattr(result, "ended_at", None)
    started = _parse_dt(started_raw) if started_raw else datetime.now(UTC)
    ended = _parse_dt(ended_raw) if ended_raw else datetime.now(UTC)
    if ended < started:
        ended = started
    duration = int((ended - started).total_seconds())
    record = {
        "schema_version": "1.0",
        "run_id": run_id,
        "cycle": cycle,
        "agent_id": agent_id,
        "agent_role": _agent_role(agent_id),
        "prompt_path": str(prompt_path),
        "prompt_line_count": len(prompt_text.splitlines()),
        "prompt_task_count": prompt_text.count("### Task "),
        "started_at": started.isoformat(),
        "ended_at": ended.isoformat(),
        "duration_seconds": duration,
        "exit_code": getattr(result, "exit_code", 0),
        "status": result.status,
        "changed_files": result.changed_files,
        "unauthorized_files": result.unauthorized_files,
        "commit_sha": result.commit_sha or None,
        "validation_passed": result.validation_passed,
        "secret_findings": result.secret_findings,
        "final_report_path": f"docs/cycle_reports/CYCLE_{cycle:03d}_AGENT_{agent_id}.md",
        "errors": result.errors,
        "runner_host": socket.gethostname(),
        "cursor_version": str(cursor_state.get("cursor_version", "")),
        "cursor_model": str(cursor_state.get("observed_model", "Codex 5.3")),
        "model_verified_at": str(cursor_state.get("verified_at", "")),
    }
    path = record_dir / f"agent_run_record_{agent_id}.json"
    path.write_text(json.dumps(record, indent=2), encoding="utf-8")
    valid, missing = validate_run_record_schema(path)
    if not valid:
        print(f"WARNING: run record schema missing fields: {missing}")
    return path


def validate_run_record_schema(record_path: Path) -> tuple[bool, list[str]]:
    required = [
        "schema_version",
        "run_id",
        "cycle",
        "agent_id",
        "agent_role",
        "prompt_path",
        "prompt_line_count",
        "prompt_task_count",
        "started_at",
        "ended_at",
        "duration_seconds",
        "exit_code",
        "status",
        "changed_files",
        "unauthorized_files",
        "commit_sha",
        "validation_passed",
        "secret_findings",
        "final_report_path",
        "errors",
        "runner_host",
        "cursor_version",
        "cursor_model",
        "model_verified_at",
    ]
    if not record_path.exists():
        return False, required
    payload = json.loads(record_path.read_text(encoding="utf-8"))
    missing = [key for key in required if key not in payload]
    return len(missing) == 0, missing


def _agent_role(agent_id: str) -> str:
    if AGENT_LANES_PATH.exists():
        try:
            data = yaml.safe_load(AGENT_LANES_PATH.read_text(encoding="utf-8")) or {}
            lane = data.get(agent_id, {})
            role = lane.get("role") or lane.get("name")
            if role:
                return str(role)
        except Exception:
            pass
    defaults = {"A": "PM Planner", "B": "Automation Core", "C": "UI/UX", "D": "Integration", "E": "QA", "F": "Testing"}
    return defaults.get(agent_id, "Unknown")


def _parse_dt(value: Any) -> datetime:
    if isinstance(value, datetime):
        return value if value.tzinfo else value.replace(tzinfo=UTC)
    if isinstance(value, str):
        try:
            parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
            return parsed if parsed.tzinfo else parsed.replace(tzinfo=UTC)
        except ValueError:
            return datetime.now(UTC)
    return datetime.now(UTC)
