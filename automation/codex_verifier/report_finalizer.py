"""
report_finalizer.py -- Writes ICV verification records and report sections.

ICV-REPORT-1..3: Writes verification.json + appends to agent report.
"""
from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path

from automation.codex_verifier.schemas import (
    GovernorDecision,
    VerificationResult,
)


class ReportFinalizer:
    @staticmethod
    def write_pass(
        agent: str,
        verdict: VerificationResult,
        run_dir: Path,
        contract: dict,
    ) -> str:
        """Write a PASS verification record. Returns path written."""
        icv_dir = run_dir / "icv"
        icv_dir.mkdir(parents=True, exist_ok=True)
        record = {
            "status": "VERIFIED_PASS",
            "completion_score": verdict.completion_score,
            "total_satisfied": sum(1 for i in verdict.checklist if i.status.value == "satisfied"),
            "total_items": len(verdict.checklist),
            "reasoning": verdict.reasoning,
            "deterministic_only": verdict.deterministic_only,
            "cost_usd": verdict.cost_usd,
            "tokens_used": verdict.tokens_used,
            "generated_at": datetime.now(UTC).isoformat(),
        }
        out_path = icv_dir / "verification.json"
        out_path.write_text(json.dumps(record, indent=2), encoding="utf-8")

        # Append verification section to agent report
        report_path_str = contract.get("finalreportpath", "")
        if report_path_str:
            from pathlib import Path as _P
            rp = _P("C:/Fiverr/Fiverr") / report_path_str
            if rp.exists():
                section = (
                    f"\n\n## ICV Verification Result\n\n"
                    f"**Status:** VERIFIED_PASS  \n"
                    f"**Completion Score:** {verdict.completion_score:.0%}  \n"
                    f"**Items:** {record['total_satisfied']}/{record['total_items']} satisfied  \n"
                    f"**Verified at:** {record['generated_at']}  \n"
                )
                try:
                    with open(rp, "a", encoding="utf-8") as f:
                        f.write(section)
                except Exception:
                    pass

        return str(out_path)

    @staticmethod
    def write_deferrals(
        agent: str,
        verdict: VerificationResult,
        run_dir: Path,
        contract: dict,
        decision: GovernorDecision,
        total_attempts: int,
        total_cost: float,
    ) -> str:
        """Write a STOPPED/BLOCKED verification record with deferrals."""
        icv_dir = run_dir / "icv"
        icv_dir.mkdir(parents=True, exist_ok=True)

        unmet_data = [
            {
                "id": i.id,
                "description": i.description[:200],
                "status": i.status.value,
                "classification": i.classification.value,
                "evidence": i.evidence[:200],
                "is_blocking": i.is_blocking,
            }
            for i in verdict.unmet_items
        ]

        is_blocked = verdict.has_blocking_unmet
        record = {
            "status": "BLOCKED" if is_blocked else "PASS_WITH_DEFERRALS",
            "stop_reason": decision.stop_reason.value if decision.stop_reason else None,
            "completion_score": verdict.completion_score,
            "total_attempts": total_attempts,
            "total_cost_usd": total_cost,
            "unmet_items": unmet_data,
            "reasoning": verdict.reasoning,
            "rolled_back": decision.rolled_back,
            "generated_at": datetime.now(UTC).isoformat(),
        }
        out_path = icv_dir / "verification.json"
        out_path.write_text(json.dumps(record, indent=2), encoding="utf-8")

        # Append to agent report
        report_path_str = contract.get("finalreportpath", "")
        if report_path_str:
            from pathlib import Path as _P
            rp = _P("C:/Fiverr/Fiverr") / report_path_str
            if rp.exists():
                status_s = "BLOCKED" if is_blocked else "PASS_WITH_DEFERRALS"
                section = (
                    f"\n\n## ICV Verification Result\n\n"
                    f"**Status:** {status_s}  \n"
                    f"**Stop reason:** {record['stop_reason']}  \n"
                    f"**Completion Score:** {verdict.completion_score:.0%}  \n"
                    f"**Unmet blocking items:** {sum(1 for i in verdict.unmet_items if i.is_blocking)}  \n"
                )
                for item in verdict.unmet_items[:5]:
                    section += f"- [{item.id}] {item.description[:100]}: {item.evidence[:80]}\n"
                try:
                    with open(rp, "a", encoding="utf-8") as f:
                        f.write(section)
                except Exception:
                    pass

        return str(out_path)
