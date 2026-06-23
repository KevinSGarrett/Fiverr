"""codex_thread_resolver.py — Autonomously address unresolved Codex review threads so a
cycle PR can merge WITHOUT a human (audit BLOCKER 2).

The merge gate (and GitHub's required_conversation_resolution) blocks while ANY review
thread is unresolved. The only prior in-loop resolver (github_reviewer.auto_fix_what_we_can)
resolves ONLY `isOutdated` threads, so a FRESH Codex P1/P2 finding dead-ended at
MERGE_BLOCKED → operator (the manual GraphQL resolveReviewThread step done all session).

DESIGN — FIX, don't dismiss (keeps the second-reviewer meaningful + high-confidence):
  For each round (bounded):
    1. Read unresolved, non-outdated threads authored by the Codex reviewer.
    2. If none → resolve any outdated-but-unresolved (already-fixed) threads → DONE.
    3. Otherwise dispatch ONE scoped Cursor repair that ADDRESSES the findings (file:line
       + body), commit, and push. Pushing changes the lines → GitHub marks the threads
       outdated → we resolve them.
    4. Re-check; repeat up to max_rounds.
  After the budget, anything still unresolved ESCALATES (the caller keeps MERGE_BLOCKED).
This never auto-DISMISSES a live finding; it fixes it (or escalates), so Codex stays a real
gate. All side effects go through small injectable seams so the logic is unit-testable.
"""
from __future__ import annotations

import json
import subprocess
from dataclasses import dataclass, field

from automation.codex_thread_reader import REPO, CodexThread, read_threads

# Logins whose threads the runner will auto-address. The Codex GitHub app + known bots.
CODEX_AUTHORS = {"chatgpt-codex-connector", "github-actions", "coderabbitai"}

_RESOLVE_MUTATION = (
    "mutation($id:ID!){resolveReviewThread(input:{threadId:$id}){thread{isResolved}}}"
)


@dataclass
class ResolveResult:
    pr_number: int
    resolved: bool = False
    rounds: int = 0
    repaired_rounds: int = 0
    remaining: int = 0
    escalate: bool = False
    reason: str = ""
    notes: list[str] = field(default_factory=list)


def _gh_graphql(query: str, **params: str) -> tuple[int, str]:
    args = ["gh", "api", "graphql", "-f", f"query={query}"]
    for k, v in params.items():
        args += ["-f", f"{k}={v}"]
    r = subprocess.run(args, capture_output=True, text=True, timeout=30)
    return r.returncode, (r.stdout or "") + (r.stderr or "")


def _resolve_thread(thread_id: str) -> bool:
    rc, out = _gh_graphql(_RESOLVE_MUTATION, id=thread_id)
    return rc == 0 and '"isResolved":true' in out.replace(" ", "")


def _reply_to_thread(pr_number: int, body: str) -> None:
    # Best-effort PR-level note (thread-scoped replies need the comment id; a PR comment
    # documents the autonomous disposition without blocking).
    try:
        subprocess.run(
            ["gh", "pr", "comment", str(pr_number), "--repo", REPO, "--body", body],
            capture_output=True, text=True, timeout=30,
        )
    except Exception:
        pass


def _actionable(threads: list[CodexThread]) -> list[CodexThread]:
    """Unresolved + non-outdated threads from a recognized reviewer that we should fix."""
    return [
        t for t in threads
        if not t.is_resolved and not t.is_outdated and (t.author in CODEX_AUTHORS or not t.author)
    ]


def _resolve_already_fixed(threads: list[CodexThread]) -> int:
    """Resolve threads GitHub has marked OUTDATED but not yet resolved (their lines
    changed → the finding no longer applies to current HEAD). Returns count resolved."""
    n = 0
    for t in threads:
        if t.is_outdated and not t.is_resolved and _resolve_thread(t.thread_id):
            n += 1
    return n


def build_codex_repair_prompt(cycle: int, threads: list[CodexThread]) -> str:
    """Build a scoped repair prompt instructing the agent to ADDRESS each Codex finding.
    Pure/string-only so it is unit-testable."""
    lines = [
        f"# CYCLE {cycle:03d} — CODEX REVIEW REPAIR",
        "",
        "A second reviewer (Codex) left the following review findings on this cycle's PR.",
        "Fix EACH one with a real, minimal code change in its file. Do NOT dismiss a finding;",
        "address it. Re-run the local gates (ruff/mypy/pytest) before finishing, then write",
        f"your AGENT_COMPLETE report to docs/cycle_reports/CYCLE_{cycle:03d}_AGENT_B.md.",
        "",
        "## FINDINGS",
    ]
    for i, t in enumerate(threads, 1):
        lines.append(f"### Finding {i}")
        # Codex P2: lead with the file:line location so the agent edits the right
        # place even when the finding body does not name the file explicitly.
        loc = getattr(t, "path", "") or ""
        if loc:
            ln = getattr(t, "line", None)
            loc = f"{loc}:{ln}" if ln else loc
            lines.append(f"**Location:** `{loc}`")
        lines.append(t.body.strip())
        lines.append("")
    return "\n".join(lines)


def resolve_pr_codex_threads(
    cycle: int,
    pr_number: int,
    branch: str,
    *,
    max_rounds: int = 2,
    dispatch_repair=None,
    reader=read_threads,
    resolver=_resolve_thread,
    outdated_resolver=_resolve_already_fixed,
) -> ResolveResult:
    """Drive a bounded fix→re-review loop until all Codex threads resolve or the budget
    is exhausted. ``dispatch_repair(cycle, branch, prompt)->bool`` runs a scoped Cursor
    repair + commit + push (injected so the loop is testable without a real agent run).
    Fail-closed: any read error or repair failure leaves merge blocked (escalate)."""
    result = ResolveResult(pr_number=pr_number)
    for round_i in range(1, max_rounds + 1):
        result.rounds = round_i
        disp = reader(pr_number)
        if disp.read_error:
            result.escalate = True
            result.reason = f"read_error: {disp.read_error}"
            return result
        # First, resolve anything GitHub already outdated (prior fix landed).
        outdated_resolver(disp.threads)
        disp = reader(pr_number)
        actionable = _actionable(disp.threads)
        if not actionable:
            result.resolved = True
            result.reason = "all threads resolved"
            return result
        if dispatch_repair is None:
            result.escalate = True
            result.reason = "no repair dispatcher configured"
            result.remaining = len(actionable)
            return result
        prompt = build_codex_repair_prompt(cycle, actionable)
        ok = bool(dispatch_repair(cycle, branch, prompt))
        result.repaired_rounds += 1
        result.notes.append(f"round {round_i}: addressed {len(actionable)} finding(s), repair_ok={ok}")
        if not ok:
            result.escalate = True
            result.reason = "codex repair dispatch failed"
            result.remaining = len(actionable)
            return result
        # The push changed the lines; resolve threads GitHub now marks outdated.
        outdated_resolver(reader(pr_number).threads)

    final = reader(pr_number)
    remaining = _actionable(final.threads)
    result.remaining = len(remaining)
    result.resolved = not remaining
    result.escalate = bool(remaining)
    result.reason = "resolved after repair" if result.resolved else "still unresolved after budget"
    return result


def disposition_json(result: ResolveResult) -> str:
    return json.dumps({
        "pr_number": result.pr_number,
        "resolved": result.resolved,
        "escalate": result.escalate,
        "rounds": result.rounds,
        "repaired_rounds": result.repaired_rounds,
        "remaining": result.remaining,
        "reason": result.reason,
        "notes": result.notes,
    }, indent=2)
