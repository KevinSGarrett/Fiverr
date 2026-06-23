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
    read_error: str = ""
    disposition_table: list[dict] = field(default_factory=list)

    def summary(self) -> str:
        if self.read_error:
            return f"Codex disposition: READ ERROR ({self.read_error}) — MERGE BLOCKED"
        if not self.threads:
            return "Codex disposition: 0 threads — PASS"
        lines = [f"Codex threads: {len(self.threads)} total"]
        for t in self.threads:
            lines.append(
                f"  [{t.classification}] {t.thread_id[:8]} resolved={t.is_resolved} "
                f"outdated={t.is_outdated}"
            )
        if self.merge_blocked:
            lines.append("MERGE BLOCKED by unresolved review threads")
        return "\n".join(lines)


def read_threads(pr_number: int, repo: str = REPO) -> CodexDispositionResult:
    """Fetch the PR's review THREADS (inline comment threads with GitHub's own
    ``isResolved`` state) via the GraphQL ``reviewThreads`` connection.

    The previous implementation read review SUBMISSIONS (``--json reviews``),
    which does NOT contain the Codex bot's inline findings and silently passed in
    the normal case. This now mirrors GitHub's ``required_conversation_resolution``
    gate exactly: ``merge_blocked`` is True whenever ANY thread is unresolved.

    FAIL-CLOSED: a gh/GraphQL failure sets ``read_error`` and ``merge_blocked=True``
    (the caller's blocking ``codex_review_disposition`` check then fails) rather
    than passing on missing data.
    """
    result = CodexDispositionResult(pr_number=pr_number)
    owner, _, name = repo.partition("/")

    # Paginate ALL review threads (Codex P2): a PR with >100 threads would
    # otherwise be truncated and an unresolved thread on page 2+ would be treated
    # as nonexistent (too loose). Page through with the endCursor; fail closed if
    # another page exists but no cursor is returned, or the page cap is hit.
    query = (
        "query($owner:String!,$name:String!,$number:Int!,$cursor:String){"
        "repository(owner:$owner,name:$name){"
        "pullRequest(number:$number){"
        "reviewThreads(first:100, after:$cursor){"
        "pageInfo{hasNextPage endCursor} "
        "nodes{id isResolved isOutdated comments(first:1){nodes{author{login} body}}}"
        "}}}}"
    )
    nodes: list[dict] = []
    cursor: str | None = None
    _MAX_PAGES = 50  # 5000 threads — defensive bound against an infinite loop
    try:
        for _ in range(_MAX_PAGES):
            args = ["gh", "api", "graphql",
                    "-f", f"query={query}",
                    "-f", f"owner={owner}",
                    "-f", f"name={name}",
                    "-F", f"number={int(pr_number)}"]
            if cursor:
                args += ["-f", f"cursor={cursor}"]
            r = subprocess.run(args, capture_output=True, text=True, timeout=30)
            if r.returncode != 0:
                result.read_error = (r.stderr.strip() or "gh graphql failed")[:200]
                result.merge_blocked = True
                return result
            data = json.loads(r.stdout)
            conn = (
                data.get("data", {}).get("repository", {}).get("pullRequest", {})
                .get("reviewThreads", {})
            ) or {}
            nodes.extend(conn.get("nodes") or [])
            page = conn.get("pageInfo") or {}
            if not page.get("hasNextPage"):
                break
            cursor = page.get("endCursor")
            if not cursor:  # more pages but no cursor — fail closed, don't truncate
                result.read_error = "reviewThreads pagination cursor missing"
                result.merge_blocked = True
                return result
        else:
            # Hit the page cap with more pages remaining — fail closed.
            result.read_error = f"reviewThreads exceeded {_MAX_PAGES} pages"
            result.merge_blocked = True
            return result
    except Exception as e:
        result.read_error = str(e)[:200]
        result.merge_blocked = True
        return result

    for node in nodes:
        first = (node.get("comments", {}).get("nodes") or [{}])[0]
        author = ((first.get("author") or {}).get("login")) or ""
        body = first.get("body", "") or ""
        thread = CodexThread(
            thread_id=str(node.get("id", "unknown")),
            is_resolved=bool(node.get("isResolved")),
            is_outdated=bool(node.get("isOutdated")),
            author=author,
            body=body[:500],
            classification=_classify_body(body),
        )
        result.threads.append(thread)
        # Any unresolved thread blocks (matches required_conversation_resolution).
        if not thread.is_resolved:
            result.blockers.append(thread)

    for t in result.threads:
        result.disposition_table.append({
            "thread_id": t.thread_id[:12],
            "resolved": t.is_resolved,
            "outdated": t.is_outdated,
            "category": t.classification,
            "merge_blocking": not t.is_resolved,
        })

    result.all_resolved = all(t.is_resolved for t in result.threads) if result.threads else True
    result.merge_blocked = bool(result.blockers)
    return result


def codex_has_reviewed(pr_number: int, repo: str = REPO) -> bool | None:
    """Has the Codex second-reviewer actually reviewed this PR yet?

    Closes the empty-threads-before-review RACE: ``read_threads`` returns zero
    threads BOTH when Codex reviewed and found nothing AND when Codex has not run
    yet. Treating the latter as "clean" would merge UNREVIEWED code. We confirm a
    review exists by either (a) a submitted review, or (b) any inline thread, whose
    author login contains ``codex``.

    Returns True (reviewed), False (not yet), or None on read error. Callers that
    gate merge should treat None as "not reviewed" (fail-closed) — bounded by the
    loop's CI-wait cap so a persistent error escalates rather than hangs forever.
    """
    owner, _, name = repo.partition("/")
    query = (
        "query($owner:String!,$name:String!,$number:Int!){"
        "repository(owner:$owner,name:$name){pullRequest(number:$number){"
        "reviews(first:50){nodes{author{login}}} "
        "reviewThreads(first:20){nodes{comments(first:1){nodes{author{login}}}}}"
        "}}}"
    )
    try:
        r = subprocess.run(
            ["gh", "api", "graphql",
             "-f", f"query={query}", "-f", f"owner={owner}", "-f", f"name={name}",
             "-F", f"number={int(pr_number)}"],
            capture_output=True, text=True, timeout=30,
        )
        if r.returncode != 0:
            return None
        pr = (json.loads(r.stdout).get("data", {})
              .get("repository", {}).get("pullRequest", {})) or {}
    except Exception:
        return None

    def _is_codex(login: object) -> bool:
        return "codex" in str(login or "").lower()

    for rv in (pr.get("reviews", {}).get("nodes") or []):
        if _is_codex((rv.get("author") or {}).get("login")):
            return True
    for th in (pr.get("reviewThreads", {}).get("nodes") or []):
        c = (th.get("comments", {}).get("nodes") or [{}])[0]
        if _is_codex((c.get("author") or {}).get("login")):
            return True
    return False


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
