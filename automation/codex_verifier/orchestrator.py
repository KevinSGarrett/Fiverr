"""
orchestrator.py -- verify_and_repair_agent(): the ICV main sub-loop.

ICV-ORCH-1..8: Verify -> repair -> re-verify, guaranteed termination.
"""
from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

import automation.autopilot_logger as L
from automation.codex_verifier.checklist_builder import ChecklistBuilder
from automation.codex_verifier.classifier import classify_all
from automation.codex_verifier.config import ICVConfig, load_config
from automation.codex_verifier.deterministic_checker import DeterministicChecker
from automation.codex_verifier.evidence_collector import EvidenceCollector
from automation.codex_verifier.ledger import VerificationLedger
from automation.codex_verifier.loop_governor import LoopGovernor
from automation.codex_verifier.repair_prompt_builder import RepairPromptBuilder
from automation.codex_verifier.report_finalizer import ReportFinalizer
from automation.codex_verifier.schemas import (
    AgentVerificationOutcome,
    GovernorDecisionKind,
    OutcomeStatus,
    StopReason,
)
from automation.codex_verifier.snapshot_manager import SnapshotManager
from automation.codex_verifier.verifier_openai import assess

REPO_ROOT = Path("C:/Fiverr/Fiverr")


def verify_and_repair_agent(
    cycle: int,
    agent: str,
    prompt_path: str | Path,
    contract_path: str | Path | None,
    run_dir: str | Path,
    dispatch_result: Any = None,
    pre_dispatch_sha: str | None = None,
    config: ICVConfig | None = None,
) -> AgentVerificationOutcome:
    """
    Main ICV entry point. Called by cmd_run_cycle after each agent's run-agent.
    Returns AgentVerificationOutcome (never raises — always returns a result).
    """
    cfg = config or load_config()
    cycle_s = f"{cycle:03d}"
    run_dir = Path(run_dir) if run_dir else Path(f"C:/AI_Runner/runs/CYCLE_{cycle_s}")

    outcome = AgentVerificationOutcome(
        cycle=cycle_s,
        agent=agent,
        status=OutcomeStatus.ERROR_FALLBACK,
    )

    # ── Check enabled ────────────────────────────────────────────────
    if not cfg.enabled:
        outcome.status = OutcomeStatus.SKIPPED_DISABLED
        outcome.skipped_reason = "ICV disabled in config (ICV_DISABLED=1 or config.enabled=false)"
        L.info(f"ICV skipped for agent {agent}: {outcome.skipped_reason}")
        return outcome

    # ── Wave 14.4 idempotency: return cached outcome if HEAD unchanged ────
    import subprocess as _sub_idem
    _cur_head = ""
    try:
        _cur_head = _sub_idem.run(
            ["git", "rev-parse", "HEAD"], cwd=str(REPO_ROOT),
            capture_output=True, text=True, timeout=10
        ).stdout.strip()
    except Exception:
        pass
    _verif_json = run_dir / "icv" / "verification.json"
    if _verif_json.exists() and _cur_head:
        try:
            _cached = json.loads(_verif_json.read_text(encoding="utf-8"))
            if _cached.get("head_sha") == _cur_head:
                # Same HEAD -- return cached outcome, no re-spend
                _cached_status = _cached.get("status", "ERROR_FALLBACK")
                outcome.status = OutcomeStatus(_cached_status) if _cached_status in [e.value for e in OutcomeStatus] else OutcomeStatus.ERROR_FALLBACK
                outcome.completion_score = _cached.get("completion_score", 0.0)
                outcome.icv_report_path = str(_verif_json)
                outcome.skipped_reason = "idempotent re-run: HEAD unchanged, returning cached outcome"
                L.info(f"ICV idempotent: cached outcome {outcome.status.value} for agent {agent}")
                return outcome
        except Exception:
            pass  # cache miss → proceed normally

    # ── Load contract ────────────────────────────────────────────────
    contract: dict = {}
    if contract_path:
        try:
            cp = Path(contract_path)
            if cp.exists():
                contract = json.loads(cp.read_text(encoding="utf-8"))
        except Exception as exc:
            L.warn(f"ICV: contract load error for {agent}: {exc}")
    elif cfg.require_contract:
        outcome.status = OutcomeStatus.SKIPPED_DISABLED
        outcome.skipped_reason = "No contract found and require_contract=true"
        return outcome

    L.section(f"ICV verify_and_repair — cycle={cycle_s} agent={agent}")

    try:
        # ── Collect evidence ─────────────────────────────────────────
        evidence = EvidenceCollector.collect(
            cycle=cycle,
            agent=agent,
            prompt_path=prompt_path,
            contract=contract,
            run_dir=run_dir,
            dispatch_result=dispatch_result,
            pre_dispatch_sha=pre_dispatch_sha,
        )

        # ── Build checklist ──────────────────────────────────────────
        checklist = ChecklistBuilder.build(
            prompt_text=evidence.prompt_text,
            contract=contract,
        )

        # ── Run deterministic checks ─────────────────────────────────
        checklist = DeterministicChecker.run(checklist, evidence)
        checklist = classify_all(checklist)

        # ── Setup governor + ledger ──────────────────────────────────
        governor = LoopGovernor(
            max_attempts=cfg.max_attempts,
            wall_clock_max_s=cfg.wall_clock_max_minutes * 60,
            openai_budget_usd=cfg.openai_budget_usd,
            min_score=cfg.min_completion_score,
        )
        ledger = VerificationLedger(run_dir, agent)
        attempt = 0
        total_cost = 0.0
        total_tokens = 0

        # ── Main verify → repair loop ────────────────────────────────
        while True:
            L.info(f"ICV attempt {attempt + 1}/{cfg.max_attempts} for agent {agent}")

            # LLM-assisted assessment
            verdict = assess(
                checklist=checklist,
                evidence=evidence,
                attempt=attempt,
                model=cfg.openai_model,
                budget_usd=cfg.openai_budget_usd - total_cost,
            )
            total_cost += verdict.cost_usd
            total_tokens += verdict.tokens_used

            # Record in ledger
            governor.note_attempt(
                score=verdict.completion_score,
                cost_usd=verdict.cost_usd,
            )
            ledger.record(
                agent=agent,
                attempt=attempt,
                verdict_status=verdict.status.value,
                completion_score=verdict.completion_score,
                decision_kind="",  # filled below
                stop_reason=None,
                cost_usd=verdict.cost_usd,
                tokens_used=verdict.tokens_used,
                unmet_count=len(verdict.unmet_items),
                deterministic_only=verdict.deterministic_only,
            )

            # Governor decides
            decision = governor.decide(verdict, attempt)

            L.info(
                f"ICV decision={decision.kind.value} "
                f"score={verdict.completion_score:.2f} "
                f"unmet={len(verdict.unmet_items)} "
                f"cost=${total_cost:.4f}"
            )

            if decision.kind == GovernorDecisionKind.ACCEPT_PASS:
                report_path = ReportFinalizer.write_pass(agent, verdict, run_dir, contract)
                L.ok(f"ICV VERIFIED_PASS for agent {agent} (score={verdict.completion_score:.2f})")
                outcome.status = OutcomeStatus.VERIFIED_PASS
                outcome.completion_score = verdict.completion_score
                outcome.attempts = attempt + 1
                outcome.total_cost_usd = total_cost
                outcome.total_tokens = total_tokens
                outcome.icv_report_path = report_path
                return outcome

            if decision.kind == GovernorDecisionKind.STOP:
                if decision.rolled_back:
                    SnapshotManager.restore(decision.snapshot_ref)
                report_path = ReportFinalizer.write_deferrals(
                    agent, verdict, run_dir, contract, decision, attempt + 1, total_cost
                )
                is_blocked = verdict.has_blocking_unmet
                L.warn(
                    f"ICV {'BLOCKED' if is_blocked else 'PASS_WITH_DEFERRALS'} for agent {agent} "
                    f"stop_reason={decision.stop_reason} score={verdict.completion_score:.2f}"
                )
                outcome.status = OutcomeStatus.BLOCKED if is_blocked else OutcomeStatus.PASS_WITH_DEFERRALS
                outcome.completion_score = verdict.completion_score
                outcome.attempts = attempt + 1
                outcome.total_cost_usd = total_cost
                outcome.total_tokens = total_tokens
                outcome.unmet_items = verdict.unmet_items
                outcome.stop_reason = decision.stop_reason
                outcome.icv_report_path = report_path
                return outcome

            # REPAIR decision: build repair prompt and re-dispatch
            fixable = [
                i for i in verdict.unmet_items
                if i.classification.value == "FIXABLE_IN_SCOPE"
            ]
            repair = RepairPromptBuilder.build(
                original_prompt_text=evidence.prompt_text,
                contract=contract,
                fixable_items=fixable,
                attempt=attempt + 1,
                cycle=cycle,
                agent=agent,
                run_dir=run_dir,
            )
            if repair is None:
                L.warn(f"ICV: no safe repair possible for agent {agent}, stopping")
                report_path = ReportFinalizer.write_deferrals(
                    agent, verdict, run_dir, contract, decision, attempt + 1, total_cost
                )
                outcome.status = OutcomeStatus.PASS_WITH_DEFERRALS
                outcome.completion_score = verdict.completion_score
                outcome.attempts = attempt + 1
                outcome.total_cost_usd = total_cost
                outcome.stop_reason = StopReason.NOTHING_FIXABLE
                outcome.icv_report_path = report_path
                return outcome

            # Take snapshot before repair (for rollback)
            snapshot_ref = SnapshotManager.take(cycle, agent, attempt)

            # Re-dispatch Cursor with the repair prompt
            L.info(f"ICV re-dispatching agent {agent} with repair prompt (attempt {attempt + 1})")
            if not os.environ.get("PYTEST_CURRENT_TEST"):
                try:
                    from automation.cursor_adapter import run_agent as cursor_run
                    from automation.run_agent_lifecycle import run_post_agent_lifecycle
                    cursor_run(
                        agent_id=f"{agent}_icv_repair_{attempt + 1}",
                        prompt_path=repair.prompt_path,
                        working_dir=str(REPO_ROOT),
                        output_dir=str(run_dir / f"icv/repair_{attempt + 1}"),
                    )
                    # Re-run lifecycle checks on repair
                    run_post_agent_lifecycle(
                        agent_id=agent,
                        cycle=cycle,
                        run_id=f"icv_repair_{attempt + 1}",
                        run_dir=run_dir,
                        jira_keys=[],
                        contract=contract,
                        pre_dispatch_sha=pre_dispatch_sha,
                    )
                except Exception as exc:
                    L.warn(f"ICV re-dispatch error: {exc}")

            # Refresh evidence after repair
            evidence = EvidenceCollector.collect(
                cycle=cycle, agent=agent, prompt_path=prompt_path,
                contract=contract, run_dir=run_dir,
                pre_dispatch_sha=pre_dispatch_sha,
            )
            checklist = DeterministicChecker.run(checklist, evidence)
            checklist = classify_all(checklist)
            governor.note_attempt(score=0.0, cost_usd=0.0, snapshot_ref=snapshot_ref)
            attempt += 1

    except Exception as exc:
        import traceback
        L.log_exception("ICV orchestrator", exc)
        outcome.status = OutcomeStatus.ERROR_FALLBACK
        outcome.errors.append(f"{type(exc).__name__}: {exc}\n{traceback.format_exc()[-300:]}")
        return outcome
