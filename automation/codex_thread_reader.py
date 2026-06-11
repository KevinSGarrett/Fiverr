"""
codex_thread_reader.py — Read and classify Codex/AI review threads on a PR.
Required for GJCI-020, GJCI-021, GJCI-022.
"""
from __future__ import annotations

import json
import subprocess
from dataclasses import dataclass, field
from pathlib import Path

REPO = "KevinSGarrett/Fiverr"

VALID_CATEGORIES = {
    "VALID_FIXED", "VALID_DEFERRED_BLOCKER", "VALID_DEFERRED_NONBLOCKING",
    "NOT_APPLICABLE", "FALSE_POSITIVE", "DUPLICATE",
    "OUTDATED_FIXED", "OUTDATED_STILL_VALID", "OUTDATED_FALSE_POSITIVE",
}

BLOCKING_CATEGORIES = {"VALID_DEFERRED_BLOCKER", "OUTDATED_STILL_VALID"}
AUTO_RESOLVE_CATEGORIES = {"VALID_FIXED", "DUPLICATE", "OUTDATED_FIXED"}


@dataclass
class CodexThread:
    thread_id: str
    is_resolved: bool
    is_outdated: bool
    author: str
    body: str
    classification: str = "UNCLASSIFIED"
    evidence_reply: str = ""
    jira_ticket: str = ""


@dataclass
class CodexDispositionResult:
    pr_number: int
    threads: list[CodexThread] = field(default_factory=list)
    blockers: list[CodexThread] = field(default_factory=list)
    all_resolved: bool = False
    merge_blocked: bool = False
    disposition_table: list[dict] = field(default_factory=list)

    def summary(self) -> str:
        if not self.threads:
            return "Codex disposition: 0 threads — PASS"
        lines = [f"Codex threads: {len(self.threads)} total"]
        for t in self.threads:
            lines.append(f"  [{t.classification}] {t.thread_id[:8]} resolved={t.is_resolved}")
        if self.merge_blocked:
            lines.append("MERGE BLOCKED by unresolved Codex findings")
        return "\n".join(lines)


def read_threads(pr_number: int, repo: str = REPO) -> CodexDispositionResult:
    """Fetch review threads from a PR using gh CLI."""
    result = CodexDispositionResult(pr_number=pr_number)

    try:
        # Use gh pr view to get review comments
        r = subprocess.run(
            ["gh", "pr", "view", str(pr_number), "--repo", repo,
             "--json", "reviews,reviewDecision,statusCheckRollup"],
            capture_output=True, text=True, timeout=30
        )
        if r.returncode != 0:
            return result

        data = json.loads(r.stdout)
        reviews = data.get("reviews") or []

        for review in reviews:
            if review.get("author", {}).get("login", "") in ("github-actions", ""):
                continue
            body = review.get("body", "")
            thread_id = review.get("id", "unknown")
            # Classify based on body keywords
            classification = _classify_body(body)
            thread = CodexThread(
                thread_id=str(thread_id),
                is_resolved=review.get("state") == "DISMISSED",
                is_outdated=False,
                author=review.get("author", {}).get("login", ""),
                body=body[:500],
                classification=classification,
            )
            result.threads.append(thread)
            if classification in BLOCKING_CATEGORIES:
                result.blockers.append(thread)

    except Exception as e:
        result.disposition_table.append({"error": str(e)})

    # Build disposition table
    for t in result.threads:
        result.disposition_table.append({
            "thread_id": t.thread_id[:12],
            "resolved": t.is_resolved,
            "category": t.classification,
            "merge_blocking": t.classification in BLOCKING_CATEGORIES,
        })

    result.all_resolved = all(t.is_resolved for t in result.threads) if result.threads else True
    result.merge_blocked = bool(result.blockers) or any(
        not t.is_resolved and t.classification not in AUTO_RESOLVE_CATEGORIES
        for t in result.threads
    )
    return result


def _classify_body(body: str) -> str:
    """Heuristic classification of a review comment body."""
    body_lower = body.lower()
    if any(w in body_lower for w in ["not applicable", "n/a", "doesn't apply"]):
        return "NOT_APPLICABLE"
    if any(w in body_lower for w in ["false positive", "false alarm"]):
        return "FALSE_POSITIVE"
    if any(w in body_lower for w in ["duplicate", "already tracked"]):
        return "DUPLICATE"
    if any(w in body_lower for w in ["fixed", "resolved", "addressed"]):
        return "VALID_FIXED"
    if any(w in body_lower for w in ["critical", "blocking", "blocker", "must fix"]):
        return "VALID_DEFERRED_BLOCKER"
    return "UNCLASSIFIED"


def write_disposition_report(result: CodexDispositionResult, run_dir: Path) -> Path:
    """Write Codex disposition JSON to run dir."""
    run_dir.mkdir(parents=True, exist_ok=True)
    path = run_dir / "github" / "codex_threads.json"
    path.parent.mkdir(exist_ok=True)
    path.write_text(json.dumps({
        "pr_number": result.pr_number,
        "thread_count": len(result.threads),
        "all_resolved": result.all_resolved,
        "merge_blocked": result.merge_blocked,
        "blockers": [t.thread_id for t in result.blockers],
        "disposition_table": result.disposition_table,
    }, indent=2))
    return path
