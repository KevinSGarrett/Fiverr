"""Detect policy/runtime drift before dispatch."""

from __future__ import annotations

import json
import re
import subprocess
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import yaml


@dataclass
class DriftItem:
    drift_type: str
    description: str
    severity: str  # BLOCKING | WARNING


@dataclass
class DriftReport:
    passed: bool
    drifts: list[DriftItem]
    warnings: list[str]
    checked_at: str


class DriftDetector:
    """Performs consistency checks across repo and runner state."""

    def __init__(self, expected_state_path: str | Path | None = None) -> None:
        self.expected_state_path = Path(
            expected_state_path or "C:/AI_Runner/state/cursor_model_state.json"
        )

    def check_drift(self, candidate_state_path: str | Path) -> dict[str, Any]:
        """Legacy check: compare candidate state file vs expected state file."""
        expected = self._load_json(self.expected_state_path)
        candidate = self._load_json(Path(candidate_state_path))
        expected_model = (
            expected.get("observed_model") or expected.get("requested_model")
            or expected.get("model") or "UNKNOWN"
        )
        candidate_model = candidate.get("model") or candidate.get("observed_model") or "UNKNOWN"
        drift_detected = candidate_model != expected_model
        return {
            "drift_detected": drift_detected,
            "expected_model": expected_model,
            "candidate_model": candidate_model,
            "candidate_status": candidate.get("status", "UNKNOWN"),
            "reason": "model_mismatch" if drift_detected else "none",
        }

    def detect(self, repo_root: Path, runner_root: Path) -> DriftReport:
        drifts: list[DriftItem] = []
        warnings: list[str] = []

        checks = (
            self._check_cycle_mismatch,
            self._check_branch_mismatch,
            self._check_stale_state_snapshot,
            self._check_model_state_expired,
            self._check_stale_hydration,
            self._check_missing_prompts_for_active_cycle,
            self._check_frozen_while_dispatching,
            self._check_jira_pr_contradiction,
        )
        for check in checks:
            item = check(repo_root, runner_root)
            if item is None:
                continue
            drifts.append(item)
            if item.severity == "WARNING":
                warnings.append(item.description)

        passed = not any(item.severity == "BLOCKING" for item in drifts)
        return DriftReport(
            passed=passed,
            drifts=drifts,
            warnings=warnings,
            checked_at=datetime.now(UTC).isoformat(),
        )

    def write_report(self, report: DriftReport, output_dir: Path) -> Path:
        """Persist drift report as JSON."""
        output_dir.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%S")
        path = output_dir / f"drift_report_{timestamp}.json"
        path.write_text(json.dumps(asdict(report), indent=2), encoding="utf-8")
        return path

    def _load_json(self, path: Path) -> dict[str, Any]:
        try:
            return json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}
        except Exception:
            return {}

    def _check_cycle_mismatch(self, repo_root: Path, runner_root: Path) -> DriftItem | None:
        snapshot = self._load_json(
            repo_root / "PM_Pack/automation/policy_snapshots/current_policy_snapshot.json"
        )
        controller = self._load_json(runner_root / "state/controller_state.json")
        snapshot_cycle = snapshot.get("current_cycle") or snapshot.get("cycle_current")
        active_cycle = controller.get("active_cycle")
        if snapshot_cycle and active_cycle and int(snapshot_cycle) != int(active_cycle):
            return DriftItem(
                drift_type="CYCLE_MISMATCH",
                description=f"policy cycle={snapshot_cycle} controller cycle={active_cycle}",
                severity="BLOCKING",
            )
        return None

    def _check_branch_mismatch(self, repo_root: Path, runner_root: Path) -> DriftItem | None:
        _ = repo_root
        controller = self._load_json(runner_root / "state/controller_state.json")
        status = controller.get("status", "")
        branch = controller.get("active_branch", "")
        if status == "AGENT_DISPATCH" and not re.match(r"cycle/\d{3}/integration", branch or ""):
            return DriftItem(
                drift_type="BRANCH_MISMATCH",
                description=f"Invalid active branch for dispatch: {branch}",
                severity="BLOCKING",
            )
        return None

    def _check_stale_state_snapshot(self, repo_root: Path, runner_root: Path) -> DriftItem | None:
        snapshot = self._load_json(
            repo_root / "PM_Pack/automation/policy_snapshots/current_policy_snapshot.json"
        )
        current_cycle = int(snapshot.get("current_cycle") or snapshot.get("cycle_current") or 0)
        state_path = repo_root / "PM_Pack/CURRENT_STATE_CANONICAL.md"
        if not state_path.exists():
            return None
        match = re.search(r"Cycle[:\s]+(\d+)", state_path.read_text(encoding="utf-8"))
        if not match:
            return None
        state_cycle = int(match.group(1))
        if current_cycle and state_cycle < current_cycle - 1:
            return DriftItem(
                drift_type="STALE_STATE_SNAPSHOT",
                description=f"State snapshot cycle {state_cycle} lags current {current_cycle}",
                severity="WARNING",
            )
        return None

    def _check_model_state_expired(self, repo_root: Path, runner_root: Path) -> DriftItem | None:
        _ = repo_root
        model = self._load_json(runner_root / "state/cursor_model_state.json")
        valid_until = model.get("valid_until")
        if not valid_until:
            return None
        try:
            expires = datetime.fromisoformat(str(valid_until).replace("Z", "+00:00"))
        except ValueError:
            return DriftItem(
                drift_type="MODEL_STATE_EXPIRED",
                description="cursor_model_state valid_until is invalid",
                severity="BLOCKING",
            )
        if expires < datetime.now(UTC):
            return DriftItem(
                drift_type="MODEL_STATE_EXPIRED",
                description=f"Model verification expired at {valid_until}",
                severity="BLOCKING",
            )
        return None

    def _check_stale_hydration(self, repo_root: Path, runner_root: Path) -> DriftItem | None:
        snapshot = self._load_json(
            repo_root / "PM_Pack/automation/policy_snapshots/current_policy_snapshot.json"
        )
        current_cycle = int(snapshot.get("current_cycle") or snapshot.get("cycle_current") or 0)
        hydration = repo_root / "PM_Pack/07_hydration/HYDRATION_HEADER.md"
        if not hydration.exists():
            return None
        match = re.search(r"Active cycle:\s*(\d+)", hydration.read_text(encoding="utf-8"))
        if not match:
            return None
        hydration_cycle = int(match.group(1))
        if current_cycle and hydration_cycle < current_cycle - 1:
            return DriftItem(
                drift_type="STALE_HYDRATION",
                description=f"Hydration header cycle {hydration_cycle} is stale vs {current_cycle}",
                severity="WARNING",
            )
        return None

    def _check_missing_prompts_for_active_cycle(
        self, repo_root: Path, runner_root: Path
    ) -> DriftItem | None:
        controller = self._load_json(runner_root / "state/controller_state.json")
        active_cycle = int(controller.get("active_cycle") or 0)
        if controller.get("status") != "PLANNED" or not active_cycle:
            return None
        prompts = list(
            (repo_root / "PM_Pack/automation/prompts").glob(
                f"CYCLE_{active_cycle:03d}_AGENT_*.md"
            )
        )
        if not prompts:
            return DriftItem(
                drift_type="MISSING_PROMPTS_FOR_ACTIVE_CYCLE",
                description=f"No prompts for active cycle {active_cycle}",
                severity="BLOCKING",
            )
        return None

    def _check_frozen_while_dispatching(self, repo_root: Path, runner_root: Path) -> DriftItem | None:
        freeze_path = repo_root / "PM_Pack/automation/policies/autonomy_freeze.yml"
        controller = self._load_json(runner_root / "state/controller_state.json")
        frozen = False
        if freeze_path.exists():
            try:
                frozen = bool(yaml.safe_load(freeze_path.read_text(encoding="utf-8")).get("frozen"))
            except Exception:
                frozen = False
        if frozen and controller.get("status") == "AGENT_DISPATCH":
            return DriftItem(
                drift_type="FROZEN_WHILE_DISPATCHING",
                description="System frozen while controller status is AGENT_DISPATCH",
                severity="BLOCKING",
            )
        return None

    def _check_jira_pr_contradiction(self, repo_root: Path, runner_root: Path) -> DriftItem | None:
        _ = runner_root
        controller = self._load_json(runner_root / "state/controller_state.json")
        active_cycle = int(controller.get("active_cycle") or 0)
        if not active_cycle:
            return None
        pr_check = subprocess.run(
            ["gh", "pr", "list", "--search", f"cycle/{active_cycle:03d}/integration", "--json", "number"],
            cwd=str(repo_root),
            capture_output=True,
            text=True,
            check=False,
        )
        has_pr = bool(pr_check.returncode == 0 and pr_check.stdout.strip() not in ("", "[]"))
        jira_state = self._load_json(runner_root / "state/jira_cycle_snapshot.json")
        in_review = jira_state.get("in_review_stories") or []
        if has_pr and not in_review:
            return DriftItem(
                drift_type="JIRA_PR_CONTRADICTION",
                description="PR exists for active cycle but Jira has no In Review stories",
                severity="WARNING",
            )
        return None
