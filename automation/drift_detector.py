"""
drift_detector.py â€” detect state drift across repo and runner artifacts.
"""
from __future__ import annotations

import json
import re
import subprocess
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


@dataclass
class DriftItem:
    drift_type: str
    severity: str  # "BLOCKING" | "WARNING"
    detail: str = ""


@dataclass
class DriftReport:
    drifts: list[DriftItem] = field(default_factory=list)
    checked_at: str = ""

    @property
    def passed(self) -> bool:
        """Pass if there are no BLOCKING drifts."""
        return not any(d.severity == "BLOCKING" for d in self.drifts)


class DriftDetector:
    """Detect drift between repo PM state and runner state."""

    def __init__(self, expected_state_path: str | Path | None = None) -> None:
        self.expected_state_path = Path(
            expected_state_path or "C:/AI_Runner/state/cursor_model_state.json"
        )

    # ------------------------------------------------------------------ #
    # Public API used by tests
    # ------------------------------------------------------------------ #

    def detect(self, repo_root: Path, runner_root: Path) -> DriftReport:
        """
        Full drift check: repo PM state vs runner state.

        Checks:
        - CYCLE_MISMATCH       (BLOCKING) â€” policy snapshot cycle != controller cycle
        - BRANCH_MISMATCH      (BLOCKING) â€” branch wrong during dispatch
        - STALE_STATE_SNAPSHOT (WARNING)  â€” canonical state >= 2 cycles behind
        - MODEL_STATE_EXPIRED  (BLOCKING) â€” cursor model valid_until in past
        - STALE_HYDRATION      (WARNING)  â€” hydration header >= 2 cycles behind
        - MISSING_PROMPTS_FOR_ACTIVE_CYCLE (BLOCKING) â€” no prompts for current cycle
        - FROZEN_WHILE_DISPATCHING (BLOCKING) â€” frozen=true while dispatching
        """
        report = DriftReport(checked_at=datetime.now(UTC).isoformat())
        drifts = report.drifts

        # Load artifacts
        policy = self._load_json(
            repo_root / "PM_Pack/automation/policy_snapshots/current_policy_snapshot.json"
        )
        controller = self._load_json(runner_root / "state/controller_state.json")
        cursor_model = self._load_json(runner_root / "state/cursor_model_state.json")
        freeze_path = repo_root / "PM_Pack/automation/policies/autonomy_freeze.yml"
        canonical_path = repo_root / "PM_Pack/CURRENT_STATE_CANONICAL.md"
        hydration_path = repo_root / "PM_Pack/07_hydration/HYDRATION_HEADER.md"

        policy_cycle = policy.get("current_cycle")
        ctrl_cycle = controller.get("active_cycle")
        ctrl_status = controller.get("status", "")
        ctrl_branch = controller.get("active_branch", "")

        # 1. CYCLE_MISMATCH
        if policy_cycle is not None and ctrl_cycle is not None:
            if policy_cycle != ctrl_cycle:
                drifts.append(DriftItem("CYCLE_MISMATCH", "BLOCKING",
                    f"policy={policy_cycle} controller={ctrl_cycle}"))

        # 2. BRANCH_MISMATCH (only during dispatch)
        if ctrl_status == "AGENT_DISPATCH" and ctrl_cycle is not None:
            expected_branch = f"cycle/{ctrl_cycle:03d}/integration"
            if ctrl_branch and ctrl_branch != expected_branch:
                drifts.append(DriftItem("BRANCH_MISMATCH", "BLOCKING",
                    f"expected={expected_branch} got={ctrl_branch}"))

        # 3. STALE_STATE_SNAPSHOT â€” canonical state >= 2 cycles behind
        if canonical_path.exists() and ctrl_cycle is not None:
            canonical_cycle = self._extract_cycle(canonical_path.read_text(encoding="utf-8", errors="replace"))
            if canonical_cycle is not None and (ctrl_cycle - canonical_cycle) >= 2:
                drifts.append(DriftItem("STALE_STATE_SNAPSHOT", "WARNING",
                    f"canonical={canonical_cycle} current={ctrl_cycle}"))

        # 4. MODEL_STATE_EXPIRED
        valid_until_str = cursor_model.get("valid_until") or cursor_model.get("expires")
        if valid_until_str:
            try:
                valid_until = datetime.fromisoformat(valid_until_str.replace("Z", "+00:00"))
                if valid_until < datetime.now(UTC):
                    drifts.append(DriftItem("MODEL_STATE_EXPIRED", "BLOCKING",
                        f"expired={valid_until_str}"))
            except Exception:
                pass

        # 5. STALE_HYDRATION â€” hydration header >= 2 cycles behind
        if hydration_path.exists() and ctrl_cycle is not None:
            hydration_cycle = self._extract_cycle(hydration_path.read_text(encoding="utf-8", errors="replace"))
            if hydration_cycle is not None and (ctrl_cycle - hydration_cycle) >= 2:
                drifts.append(DriftItem("STALE_HYDRATION", "WARNING",
                    f"hydration={hydration_cycle} current={ctrl_cycle}"))

        # 6. MISSING_PROMPTS_FOR_ACTIVE_CYCLE — only relevant when about to dispatch
        if ctrl_cycle is not None and ctrl_status in ("PLANNED",):
            prompts_dir = repo_root / "PM_Pack/automation/prompts"
            pattern = f"CYCLE_{ctrl_cycle:03d}_AGENT_"
            has_prompts = False
            if prompts_dir.exists():
                has_prompts = any(p.name.startswith(pattern) for p in prompts_dir.iterdir())
            if not has_prompts:
                # Also check via git ls-files as fallback
                try:
                    r = subprocess.run(
                        ["git", "ls-files", f"PM_Pack/automation/prompts/CYCLE_{ctrl_cycle:03d}_*"],
                        cwd=str(repo_root), capture_output=True, text=True, timeout=5
                    )
                    has_prompts = bool(r.stdout.strip())
                except Exception:
                    pass
            if not has_prompts:
                drifts.append(DriftItem("MISSING_PROMPTS_FOR_ACTIVE_CYCLE", "BLOCKING",
                    f"no prompts for cycle {ctrl_cycle}"))

        # 7. FROZEN_WHILE_DISPATCHING
        if freeze_path.exists() and ctrl_status == "AGENT_DISPATCH":
            try:
                import yaml
                freeze_data = yaml.safe_load(freeze_path.read_text(encoding="utf-8")) or {}
            except Exception:
                freeze_data = {}
            if freeze_data.get("frozen"):
                drifts.append(DriftItem("FROZEN_WHILE_DISPATCHING", "BLOCKING",
                    "autonomy_freeze.yml frozen=true during dispatch"))

        return report

    def write_report(self, report: DriftReport, output_dir: Path) -> Path:
        """Write drift report to JSON file in output_dir."""
        output_dir.mkdir(parents=True, exist_ok=True)
        ts = report.checked_at.replace(":", "").replace("-", "")[:15]
        path = output_dir / f"drift_report_{ts}.json"
        payload = {
            "checked_at": report.checked_at,
            "passed": report.passed,
            "drift_count": len(report.drifts),
            "blocking_count": sum(1 for d in report.drifts if d.severity == "BLOCKING"),
            "drifts": [{"type": d.drift_type, "severity": d.severity, "detail": d.detail}
                       for d in report.drifts],
        }
        path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        return path

    # ------------------------------------------------------------------ #
    # Legacy single-path API (kept for backward compat)
    # ------------------------------------------------------------------ #

    def check_drift(self, candidate_state_path: str | Path) -> dict[str, Any]:
        """Legacy check: compare candidate state file vs expected state file."""
        expected = self._load_json(self.expected_state_path)
        candidate = self._load_json(Path(candidate_state_path))
        expected_model = (expected.get("observed_model") or expected.get("requested_model")
                          or expected.get("model") or "UNKNOWN")
        candidate_model = candidate.get("model") or candidate.get("observed_model") or "UNKNOWN"
        drift_detected = candidate_model != expected_model
        return {
            "drift_detected": drift_detected,
            "expected_model": expected_model,
            "candidate_model": candidate_model,
            "candidate_status": candidate.get("status", "UNKNOWN"),
            "reason": "model_mismatch" if drift_detected else "none",
        }

    # ------------------------------------------------------------------ #
    # Helpers
    # ------------------------------------------------------------------ #

    @staticmethod
    def _load_json(path: Path) -> dict[str, Any]:
        try:
            return json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}
        except Exception:
            return {}

    @staticmethod
    def _extract_cycle(text: str) -> int | None:
        """Extract the first cycle number from text like 'Active cycle: 75' or 'Cycle: 73'."""
        m = re.search(r"[Cc]ycle[:\s]+(\d+)", text)
        return int(m.group(1)) if m else None

