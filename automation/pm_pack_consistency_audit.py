"""PM_Pack semantic consistency audit (fail-closed dispatch gate)."""
from __future__ import annotations

import json
import os
import re
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).parent.parent
RUNNER_ROOT = Path("C:/AI_Runner")
AGENTS = ["A", "B", "E", "C", "F", "D"]


@dataclass
class ConflictItem:
    code: str
    message: str
    severity: str = "BLOCKING"
    details: dict[str, Any] = field(default_factory=dict)

    def __str__(self) -> str:
        suffix = f" details={self.details}" if self.details else ""
        return f"[{self.severity}] {self.code}: {self.message}{suffix}"


@dataclass
class AuditResult:
    passed: bool = True
    conflicts: list[ConflictItem] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    missing_files: list[str] = field(default_factory=list)
    checked_at: str = ""
    sources: dict[str, Any] = field(default_factory=dict)

    def add_blocker(self, code: str, message: str, details: dict[str, Any] | None = None) -> None:
        self.passed = False
        self.conflicts.append(
            ConflictItem(code=code, message=message, severity="BLOCKING", details=details or {})
        )

    def summary(self) -> str:
        status = "PASS" if self.passed else "BLOCKED"
        lines = [f"PM_PACK_AUDIT {status} — {self.checked_at}"]
        if self.missing_files:
            lines.append(f"  Missing files: {self.missing_files}")
        for c in self.conflicts:
            lines.append(f"  CONFLICT: {c}")
        for w in self.warnings:
            lines.append(f"  WARN: {w}")
        if self.passed:
            lines.append("  All fail-closed governance checks passed.")
        return "\n".join(lines)


def _is_ci_mode() -> bool:
    return bool(os.environ.get("CI") or os.environ.get("GITHUB_ACTIONS"))


def _load_json(path: Path, result: AuditResult) -> dict[str, Any]:
    if not path.exists():
        result.missing_files.append(str(path))
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8", errors="replace"))
    except Exception as exc:
        result.warnings.append(f"Could not parse JSON: {path} ({exc})")
        return {}


def _extract_cycle_from_markdown(path: Path, result: AuditResult) -> int | None:
    if not path.exists():
        result.missing_files.append(str(path))
        return None
    text = path.read_text(encoding="utf-8", errors="replace")
    patterns = [
        r"^CYCLE_CURRENT:\s*0*(\d+)",
        r"^CYCLE_NEXT:\s*0*(\d+)",
        r"Active cycle:\s*0*(\d+)",
        r"Current Cycle:\s*0*(\d+)",
        r"Cycle:\s*0*(\d+)",
    ]
    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE | re.MULTILINE)
        if match:
            return int(match.group(1))
    return None


def _first_existing(paths: list[Path]) -> Path | None:
    for path in paths:
        if path.exists():
            return path
    return None


def _validate_active_prompts(repo: Path, cycle: int, result: AuditResult) -> None:
    validated_manifest_candidates = [
        repo / f"PM_Pack/automation/prompts/validated/CYCLE_{cycle:03d}_manifest.json",
        repo / f"PM_Pack/automation/prompts/validated/CYCLE_{cycle:03d}_PROMPT_MANIFEST.json",
        repo / f"PM_Pack/automation/prompts/CYCLE_{cycle:03d}_PROMPT_MANIFEST.json",
    ]
    manifest = _first_existing(validated_manifest_candidates)
    if manifest is None:
        return

    try:
        from automation.prompt_validator import validate_all

        prompts_dir = repo / "PM_Pack/automation/prompts"
        validations = validate_all(prompts_dir, cycle, AGENTS)
        failed_agents = [agent for agent, check in validations.items() if not check.passed]
        if failed_agents:
            result.add_blocker(
                "ACTIVE_PROMPTS_INVALID",
                "Validated prompt manifest exists but active prompts fail validation.",
                {"cycle": cycle, "failed_agents": failed_agents, "manifest": str(manifest)},
            )
    except Exception as exc:
        result.warnings.append(f"Prompt validation check skipped due to runtime error: {exc}")


def run_audit(repo_root: Path | None = None, runner_root: Path | None = None) -> AuditResult:
    """Run fail-closed PM_Pack consistency checks before dispatch."""
    repo = repo_root or REPO_ROOT
    runner = runner_root or RUNNER_ROOT
    result = AuditResult(checked_at=datetime.now(UTC).isoformat())

    policy_snapshot = _load_json(repo / "PM_Pack/automation/current_policy_snapshot.json", result)
    controller_path = runner / "state/controller_state.json"
    heartbeat = _load_json(runner / "state/heartbeat.json", result)

    controller_state: dict[str, Any] = {}
    if controller_path.exists():
        controller_state = _load_json(controller_path, result)
    elif not _is_ci_mode():
        result.add_blocker(
            "MISSING_CONTROLLER_STATE",
            "controller_state.json is missing outside CI mode.",
            {"path": str(controller_path)},
        )

    hydration_path = _first_existing(
        [
            repo / "PM_Pack/07_hydration/HYDRATION_HEADER.md",
            repo / "PM_Pack/02_current_state/HYDRATION_HEADER.md",
        ]
    )
    snapshot_path = _first_existing(
        [
            repo / "PM_Pack/07_hydration/STATE_SNAPSHOT.md",
            repo / "PM_Pack/02_current_state/STATE_SNAPSHOT.md",
        ]
    )
    hydration_cycle = _extract_cycle_from_markdown(
        hydration_path or Path("missing_hydration.md"), result
    )
    snapshot_cycle = _extract_cycle_from_markdown(snapshot_path or Path("missing_snapshot.md"), result)
    controller_cycle = controller_state.get("active_cycle")
    heartbeat_cycle = heartbeat.get("active_cycle")
    policy_cycle = policy_snapshot.get("cycle_current")

    result.sources = {
        "policy_snapshot_cycle": policy_cycle,
        "controller_cycle": controller_cycle,
        "heartbeat_cycle": heartbeat_cycle,
        "hydration_cycle": hydration_cycle,
        "snapshot_cycle": snapshot_cycle,
        "controller_status": controller_state.get("status"),
    }

    if policy_cycle in (None, 0):
        result.add_blocker(
            "POLICY_SNAPSHOT_CYCLE_ZERO",
            "current_policy_snapshot.json has cycle_current set to 0/null.",
            {"cycle_current": policy_cycle},
        )

    cycle_sources = {
        "controller_state": controller_cycle,
        "heartbeat": heartbeat_cycle,
        "hydration_header": hydration_cycle,
        "state_snapshot": snapshot_cycle,
    }
    known_cycles = {name: int(value) for name, value in cycle_sources.items() if isinstance(value, int)}
    if len(known_cycles) >= 2:
        min_cycle = min(known_cycles.values())
        max_cycle = max(known_cycles.values())
        if max_cycle - min_cycle > 1:
            result.add_blocker(
                "CYCLE_SOURCE_DISAGREEMENT",
                "Cycle sources differ by more than 1.",
                {"sources": known_cycles, "min_cycle": min_cycle, "max_cycle": max_cycle},
            )

    active_cycle = None
    for candidate in [controller_cycle, heartbeat_cycle, hydration_cycle, snapshot_cycle]:
        if isinstance(candidate, int) and candidate > 0:
            active_cycle = candidate
            break

    if isinstance(active_cycle, int):
        post_cycle_result_path = runner / "runs" / f"CYCLE_{active_cycle:03d}_post_cycle_result.json"
        if post_cycle_result_path.exists():
            post_cycle = _load_json(post_cycle_result_path, result)
            if bool(post_cycle.get("blocks_dispatch")):
                result.add_blocker(
                    "POST_CYCLE_REVIEW_BLOCKS_DISPATCH",
                    "Post-cycle review currently blocks dispatch.",
                    {"path": str(post_cycle_result_path), "cycle": active_cycle},
                )
        _validate_active_prompts(repo, active_cycle, result)

    out_dir = runner / "reports/validation"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / "pm_pack_audit_result.json"
    out_path.write_text(
        json.dumps(
            {
                "passed": result.passed,
                "checked_at": result.checked_at,
                "conflicts": [str(c) for c in result.conflicts],
                "warnings": result.warnings,
                "missing_files": result.missing_files,
                "sources": result.sources,
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    return result
