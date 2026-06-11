"""
repair_loop.py — Generate repair prompts and retry failed agents.
Reads classification from failure_classifier.py and builds targeted repair prompts.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from automation.failure_classifier import ClassifiedFailure, FailureType

MAX_ATTEMPTS_PER_AGENT = 5
MAX_ATTEMPTS_PER_FAILURE_TYPE = 3
REPO_ROOT = Path("C:/Fiverr/Fiverr")


@dataclass
class RepairAttempt:
    agent: str
    cycle: int
    attempt: int
    failure_type: FailureType
    prompt_path: str
    repair_agent: str


@dataclass
class RepairLoopState:
    cycle: int
    attempts_by_agent: dict[str, int] = field(default_factory=dict)
    attempts_by_type: dict[str, int] = field(default_factory=dict)
    exhausted_agents: list[str] = field(default_factory=list)

    def record(self, agent: str, failure_type: FailureType) -> bool:
        """Record a repair attempt. Returns True if within limits, False if exhausted."""
        self.attempts_by_agent[agent] = self.attempts_by_agent.get(agent, 0) + 1
        ft_key = failure_type.value
        self.attempts_by_type[ft_key] = self.attempts_by_type.get(ft_key, 0) + 1

        if (self.attempts_by_agent[agent] > MAX_ATTEMPTS_PER_AGENT or
                self.attempts_by_type[ft_key] > MAX_ATTEMPTS_PER_FAILURE_TYPE):
            if agent not in self.exhausted_agents:
                self.exhausted_agents.append(agent)
            return False
        return True

    def is_exhausted(self, agent: str) -> bool:
        return agent in self.exhausted_agents


def generate_repair_prompt(
    failure: ClassifiedFailure,
    original_mission: str,
    run_dir: Path,
    attempt: int,
) -> Path:
    """Generate a targeted repair prompt file. Returns path to written file."""
    repair_dir = run_dir / "repair"
    repair_dir.mkdir(parents=True, exist_ok=True)
    prompt_path = repair_dir / f"repair_{attempt:02d}_agent_{failure.repair_agent}_prompt.md"

    branch = _current_branch()
    diff_stat = _git_diff_stat()

    lines = [
        f"# REPAIR PROMPT - CYCLE {failure.cycle:03d} AGENT {failure.repair_agent} - ATTEMPT {attempt:02d}",
        "",
        f"You are repairing Agent {failure.agent}'s previous work in the Fiverr Research System.",
        "",
        "## Required model policy",
        "Use the runner's verified Cursor model configuration: Codex 5.3, medium effort, Auto disabled.",
        "",
        "## Repo",
        "C:\\Fiverr\\Fiverr",
        "",
        "## Branch",
        branch,
        "",
        "## Failure type",
        failure.failure_type.value,
        "",
        "## Original mission",
        original_mission[:500],
        "",
        "## What changed (git diff --stat)",
        diff_stat[:800],
        "",
        "## Validation failure evidence",
        "```",
        failure.evidence[-1200:],
        "```",
        "",
        "## Required repair",
        "Fix the smallest safe scope needed to pass the failing validation while preserving the original task intent.",
        "Add or update tests only where necessary.",
        "Do not change unrelated files.",
        "Do not push to main.",
        "Do not ask for clarification unless this requires a blocked Tier-D operation.",
        "",
        "## Validation commands to run before declaring repair complete",
        "```powershell",
        *_repair_commands_for_type(failure.failure_type),
        "```",
        "",
        "## Autonomy rule",
        "Do not stop for clarification if a reasonable, PM_Pack-consistent decision can be made.",
        "Only stop if the action would require a blocked operation.",
        "",
        "## Final repair report",
        f"Append a repair section to: docs/cycle_reports/CYCLE_{failure.cycle:03d}_AGENT_{failure.repair_agent}.md",
    ]

    prompt_path.write_text("\n".join(lines))
    return prompt_path


def _repair_commands_for_type(ft: FailureType) -> list[str]:
    """Return the minimal set of validation commands needed to confirm repair."""
    venv = "C:\\Fiverr\\Fiverr\\.venv\\Scripts\\python.exe"
    base = [f"{venv} -m ruff check src tests"]
    if ft in (FailureType.RUFF_FAILURE,):
        return base
    if ft in (FailureType.MYPY_FAILURE,):
        return base + [f"{venv} -m mypy src"]
    if ft in (FailureType.PYTEST_FAILURE, FailureType.COVERAGE_FAILURE):
        return base + [
            f"{venv} -m mypy src",
            f"{venv} -m pytest -q --cov=src --cov-report=term-missing --cov-fail-under=90",
        ]
    if ft == FailureType.CONFIG_CHECK_FAILURE:
        return base + [f"{venv} run.py config-check"]
    # Full suite for unknown types
    return base + [
        f"{venv} -m mypy src",
        f"{venv} -m pytest -q --cov=src --cov-report=term-missing --cov-fail-under=90",
        f"{venv} run.py config-check",
    ]


def _current_branch() -> str:
    import subprocess
    r = subprocess.run(
        ["git", "branch", "--show-current"],
        cwd=str(REPO_ROOT), capture_output=True, text=True
    )
    return r.stdout.strip() or "unknown"


def _git_diff_stat() -> str:
    import subprocess
    r = subprocess.run(
        ["git", "diff", "--stat"],
        cwd=str(REPO_ROOT), capture_output=True, text=True
    )
    return r.stdout.strip() or "(no diff)"
