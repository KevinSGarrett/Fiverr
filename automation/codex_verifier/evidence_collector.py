"""
evidence_collector.py -- Collects all machine-verifiable evidence for one agent run.

ICV-EVIDENCE-1..7: Reads git, run_dir, contract, prompt, GitHub, Jira (read-only).
"""
from __future__ import annotations

import json
import subprocess
from pathlib import Path
from typing import Any

from automation.codex_verifier.schemas import EvidenceBundle

REPO_ROOT = Path("C:/Fiverr/Fiverr")


def _git(
    *args: str, cwd: Path = REPO_ROOT, timeout: int = 30
) -> str:
    try:
        r = subprocess.run(
            ["git", *args], cwd=str(cwd), capture_output=True, text=True, timeout=timeout
        )
        return r.stdout.strip()
    except Exception:
        return ""


class EvidenceCollector:
    """Gather all evidence for one agent's run before calling the verifier."""

    @staticmethod
    def collect(
        cycle: int,
        agent: str,
        prompt_path: Path | str,
        contract: dict,
        run_dir: Path | str,
        dispatch_result: Any = None,
        pre_dispatch_sha: str | None = None,
    ) -> EvidenceBundle:
        cycle_s = f"{cycle:03d}"
        run_dir = Path(run_dir) if run_dir else Path("C:/AI_Runner/runs") / f"CYCLE_{cycle_s}"
        branch = f"cycle/{cycle_s}/integration"

        bundle = EvidenceBundle(
            cycle=cycle_s,
            agent=agent,
            branch=branch,
            prompt_text="",
            contract=contract or {},
            run_dir=str(run_dir),
        )

        # 1. Prompt text
        try:
            pp = Path(prompt_path)
            if pp.exists():
                bundle.prompt_text = pp.read_text(encoding="utf-8", errors="replace")
        except Exception as exc:
            bundle.errors.append(f"prompt_read: {exc}")

        # 2. Git state
        bundle.head_sha = _git("rev-parse", "HEAD") or None
        if pre_dispatch_sha and bundle.head_sha:
            changed_raw = _git(
                "diff", "--name-only", f"{pre_dispatch_sha}..HEAD"
            )
            bundle.changed_files = [f for f in changed_raw.splitlines() if f]
            bundle.committed_this_run = bool(bundle.changed_files)
        else:
            # Fall back: look at recent commits on the integration branch
            log = _git("log", "--name-only", "--format=", "-20")
            bundle.changed_files = [ln for ln in log.splitlines() if ln and "/" in ln][:50]
            bundle.committed_this_run = bool(bundle.changed_files)

        # 3. Ownership lane check
        allowed = contract.get("allowedpaths", []) or []
        blocked = contract.get("blockedpaths", []) or []
        if allowed:
            import fnmatch
            out_of_lane = []
            for f in bundle.changed_files:
                in_allowed = any(fnmatch.fnmatch(f, pat) for pat in allowed)
                in_blocked = any(fnmatch.fnmatch(f, pat) for pat in blocked)
                if not in_allowed or in_blocked:
                    out_of_lane.append(f)
            bundle.out_of_lane_files = out_of_lane

        # 4. Agent report
        report_path_str = contract.get("finalreportpath", "")
        if not report_path_str:
            report_path_str = f"docs/cycle_reports/CYCLE_{cycle_s}_AGENT_{agent}.md"
        report_path = REPO_ROOT / report_path_str
        if report_path.exists():
            bundle.report_exists = True
            bundle.report_text = report_path.read_text(encoding="utf-8", errors="replace")
            bundle.report_has_complete_marker = "AGENT_COMPLETE" in bundle.report_text

        # 5. Deliverables
        for scope_item in contract.get("jirascope", []):
            for fpath in scope_item.get("filesormodules", []):
                full = REPO_ROOT / fpath
                bundle.deliverable_exists[fpath] = full.exists()

        # 6. Dispatch result metadata
        if dispatch_result is not None:
            try:
                bundle.dispatch_exit_code = getattr(dispatch_result, "exit_code", None)
                elapsed = getattr(dispatch_result, "elapsed_minutes", None)
                if elapsed:
                    bundle.elapsed_minutes = elapsed
                    bundle.suspiciously_fast = elapsed < 5.0
            except Exception:
                pass

        # 7. Run-record from run_dir
        try:
            for run_record in run_dir.rglob("run_record.json"):
                data = json.loads(run_record.read_text(encoding="utf-8"))
                if not bundle.dispatch_exit_code:
                    bundle.dispatch_exit_code = data.get("exit_code")
                break
        except Exception:
            pass

        # 8. Jira statuses (read-only; skip if PYTEST)
        import os
        if not os.environ.get("PYTEST_CURRENT_TEST"):
            try:
                from automation.jira_client import _normalise_issue, get_issue
                for scope_item in contract.get("jirascope", []):
                    key = scope_item.get("key")
                    if key:
                        try:
                            issue = get_issue(key)
                            norm = _normalise_issue(issue) if issue else {}
                            bundle.jira_statuses[key] = norm.get("status", "Unknown")
                        except Exception:
                            bundle.jira_statuses[key] = "Error"
            except Exception:
                pass

        return bundle
