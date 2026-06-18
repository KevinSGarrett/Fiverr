"""
verifier_openai.py -- LLM-assisted verification using OpenAI reasoning model.

ICV-VERIFIER-1..6: Calls OpenAI API; deterministic-only fallback on budget/error.
"""
from __future__ import annotations

import json
import os

from automation.codex_verifier.schemas import (
    ChecklistItem,
    ChecklistStatus,
    EvidenceBundle,
    ItemClassification,
    VerificationResult,
    VerificationStatus,
)

_SYSTEM_PROMPT = """\
You are an expert code-review agent verifying whether a Cursor AI agent
completed its assigned tasks. You answer in JSON only (no markdown, no preamble).
You will be given: the agent's prompt (what it was asked to do), a machine-generated
checklist of required items with their deterministic status, and an evidence bundle
(git state, report text, file existence, command outputs).

Your job: for each UNVERIFIABLE or PARTIAL checklist item, determine whether the
agent actually completed it. Produce a structured verdict.

IMPORTANT:
- Deterministic SATISFIED/MISSING/PARTIAL verdicts CANNOT be overridden.
- Only assess items in UNVERIFIABLE/PARTIAL state.
- Evidence-bound claims only: cite specific artifacts.
- If you cannot determine, mark status: "unverifiable".
"""


def _build_user_prompt(
    checklist: list[ChecklistItem],
    evidence: EvidenceBundle,
    attempt: int,
) -> str:
    unverifiable = [
        i for i in checklist
        if i.status in (ChecklistStatus.UNVERIFIABLE, ChecklistStatus.PARTIAL)
    ]
    satisfied_count = sum(1 for i in checklist if i.status == ChecklistStatus.SATISFIED)
    missing_count = sum(1 for i in checklist if i.status == ChecklistStatus.MISSING)

    lines = [
        f"CYCLE: {evidence.cycle}  AGENT: {evidence.agent}  ATTEMPT: {attempt}",
        f"Committed this run: {evidence.committed_this_run}",
        f"Changed files ({len(evidence.changed_files)}): {evidence.changed_files[:10]}",
        f"Report exists: {evidence.report_exists}  AGENT_COMPLETE marker: {evidence.report_has_complete_marker}",
        f"Deterministic results: {satisfied_count} satisfied, {missing_count} missing",
        "",
        "=== ITEMS NEEDING LLM ASSESSMENT ===",
    ]
    for item in unverifiable[:20]:
        lines.append(f"- [{item.id}] {item.description[:120]}")
        if item.evidence:
            lines.append(f"  evidence: {item.evidence[:100]}")

    lines += [
        "",
        "=== REPORT TEXT (first 2000 chars) ===",
        evidence.report_text[:2000] if evidence.report_text else "(no report)",
        "",
        "=== RESPOND WITH JSON ===",
        '{"completion_score": 0.0-1.0, "status": "PASS|PARTIAL_PASS|FAIL|UNVERIFIABLE",',
        ' "reasoning": "...",',
        ' "item_updates": [{"id": "...", "status": "satisfied|partial|missing|unverifiable",',
        '                   "classification": "FIXABLE_IN_SCOPE|OUT_OF_SCOPE|BLOCKED_EXTERNAL|NON_ISSUE|AMBIGUOUS",',
        '                   "evidence": "..."}]}',
    ]
    return "\n".join(lines)


def _compute_det_score(checklist: list[ChecklistItem]) -> float:
    if not checklist:
        return 0.0
    blocking = [i for i in checklist if i.is_blocking]
    if not blocking:
        return 1.0
    satisfied = sum(1 for i in blocking if i.status == ChecklistStatus.SATISFIED)
    return satisfied / len(blocking)


def assess(
    checklist: list[ChecklistItem],
    evidence: EvidenceBundle,
    attempt: int = 0,
    model: str = "o3-mini",
    budget_usd: float = 2.0,
) -> VerificationResult:
    """
    Run verification. Returns a VerificationResult.
    Falls back to deterministic-only if budget=0 or LLM unavailable.
    """
    det_score = _compute_det_score(checklist)
    unverifiable = [
        i for i in checklist
        if i.status in (ChecklistStatus.UNVERIFIABLE, ChecklistStatus.PARTIAL)
    ]

    # Deterministic-only path (no budget or test env or nothing to assess)
    if budget_usd <= 0 or os.environ.get("PYTEST_CURRENT_TEST") or not unverifiable:
        status = VerificationStatus.PASS if det_score >= 0.80 else (
            VerificationStatus.PARTIAL_PASS if det_score >= 0.50 else VerificationStatus.FAIL
        )
        unmet = [i for i in checklist if i.status != ChecklistStatus.SATISFIED and i.is_blocking]
        return VerificationResult(
            status=status,
            completion_score=det_score,
            checklist=checklist,
            unmet_items=unmet,
            reasoning="Deterministic-only (no budget or test env)",
            confidence=0.95,
            deterministic_only=True,
        )

    # LLM path
    try:
        from openai import OpenAI
        client = OpenAI()  # uses OPENAI_API_KEY env var
        user_prompt = _build_user_prompt(checklist, evidence, attempt)
        resp = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": _SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt},
            ],
            response_format={"type": "json_object"},
            max_completion_tokens=1500,
        )
        content = resp.choices[0].message.content or "{}"
        tokens = resp.usage.total_tokens if resp.usage else 0
        # Rough cost: o3-mini ~$1.10/M input + $4.40/M output
        cost = tokens * 0.000003  # conservative estimate

        parsed = json.loads(content)
        score = float(parsed.get("completion_score", det_score))
        status_str = parsed.get("status", "UNVERIFIABLE").upper()
        status = VerificationStatus[status_str] if status_str in VerificationStatus.__members__ else VerificationStatus.UNVERIFIABLE

        # Apply item updates from LLM
        item_map = {i.id: i for i in checklist}
        for upd in parsed.get("item_updates", []):
            item_id = upd.get("id")
            if item_id in item_map:
                item = item_map[item_id]
                st = upd.get("status", "").lower()
                if st in ChecklistStatus._value2member_map_:
                    item.status = ChecklistStatus(st)
                cl = upd.get("classification", "")
                if cl in ItemClassification._value2member_map_:
                    item.classification = ItemClassification(cl)
                if upd.get("evidence"):
                    item.evidence = item.evidence + " | LLM: " + str(upd["evidence"])[:100]

        updated_checklist = list(item_map.values())
        unmet = [i for i in updated_checklist if i.status != ChecklistStatus.SATISFIED and i.is_blocking]
        return VerificationResult(
            status=status,
            completion_score=max(score, _compute_det_score(updated_checklist)),
            checklist=updated_checklist,
            unmet_items=unmet,
            reasoning=parsed.get("reasoning", "")[:500],
            confidence=0.8,
            tokens_used=tokens,
            cost_usd=cost,
        )

    except Exception as exc:
        # LLM failed — fall back to deterministic
        unmet = [i for i in checklist if i.status != ChecklistStatus.SATISFIED and i.is_blocking]
        return VerificationResult(
            status=VerificationStatus.PARTIAL_PASS if det_score >= 0.50 else VerificationStatus.FAIL,
            completion_score=det_score,
            checklist=checklist,
            unmet_items=unmet,
            reasoning=f"LLM fallback (error: {exc})",
            confidence=0.5,
            deterministic_only=True,
        )
