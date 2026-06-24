"""
jira_sync.py — Automated Jira sync during runner cycle execution.
Implements GJCI-023..030: comment, transition, evidence posting, Done closeout.

CRITICAL: Jira is the HIGHEST authority for what needs to be built.
Every story has Acceptance Criteria (AC) and Definition of Done (DOD) that
MUST ALL be verified before a story transitions to Done. The runner:
  - Reads full AC/DOD from every story before dispatching agents
  - Posts detailed evidence comments after each agent run
  - Reads all existing comments to understand project history
  - Only transitions to Done when ALL AC items are verifiably met
  - NEVER transitions to Done based solely on file creation

Called at key points in the run loop:
  - on_cycle_planned(): post planning comments + read existing comments
  - on_agent_complete(): post implementation evidence with AC verification
  - on_pr_opened(): transition to In Review
  - on_cycle_merged(): verify ALL AC/DOD + transition to Done (or block)
  - on_repair_exhausted(): create blocker/rework ticket
"""
from __future__ import annotations

import json
import re
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

REPO_ROOT = Path("C:/Fiverr/Fiverr")

# Jira transition IDs (GJCI-025)
DONE_TRANSITION_ID         = "41"   # Done
IN_REVIEW_TRANSITION_ID    = "31"   # In Review
IN_PROGRESS_TRANSITION_ID  = "21"   # In Progress


def post_status_map() -> dict:
    return {
        "DONE": DONE_TRANSITION_ID,
        "IN_REVIEW": IN_REVIEW_TRANSITION_ID,
        "IN_PROGRESS": IN_PROGRESS_TRANSITION_ID,
    }


# ─── AC/DOD extraction ────────────────────────────────────────────────────────

def extract_ac_items(description: str) -> list[str]:
    """
    Extract Acceptance Criteria items from a Jira story description.
    Returns a list of AC strings that must be verified.
    """
    if not description:
        return []
    # Match bullet points and checklist items
    items = re.findall(
        r"(?:^|\n)\s*[-*•✓□]\s*([^\n]{15,300})",
        description,
        re.MULTILINE,
    )
    # Also match numbered lists
    items += re.findall(
        r"(?:^|\n)\s*\d+\.\s+([^\n]{15,300})",
        description,
        re.MULTILINE,
    )
    # Deduplicate preserving order
    seen: set[str] = set()
    result = []
    for item in items:
        item = item.strip()
        if item not in seen:
            seen.add(item)
            result.append(item)
    return result[:30]  # cap at 30 items


def verify_ac_against_evidence(
    ac_items: list[str],
    evidence_text: str,
) -> dict[str, list[str]]:
    """
    Check which AC items appear to be addressed in the evidence text.
    Returns {"verified": [...], "unverified": [...]}.
    """
    verified, unverified = [], []
    evidence_lower = evidence_text.lower()
    for ac in ac_items:
        # Extract key nouns/verbs from AC item (skip common words)
        words = [w.lower() for w in re.findall(r"\b[a-z]{4,}\b", ac)
                 if w.lower() not in {"that", "with", "from", "this", "when",
                                      "have", "been", "will", "must", "does"}]
        key_words = words[:4]
        # AC is verified if ≥2 key words appear in evidence
        matches = sum(1 for w in key_words if w in evidence_lower)
        if matches >= min(2, len(key_words)):
            verified.append(ac)
        else:
            unverified.append(ac)
    return {"verified": verified, "unverified": unverified}


# ─── Comment reading ─────────────────────────────────────────────────────────

def fetch_story_comments(issue_key: str) -> list[dict[str, Any]]:
    """
    Fetch all comments on a Jira issue for PM context.
    Returns list of {author, body, created} dicts.
    """
    try:
        from automation.jira_client import get_issue
        issue = get_issue(issue_key)
        fields = issue.get("fields", {})
        comments_data = fields.get("comment", {}).get("comments", [])
        result = []
        for c in comments_data:
            body = c.get("body", "")
            if isinstance(body, dict):
                # ADF format — extract text
                def _adf_text(node: dict) -> str:
                    if node.get("type") == "text":
                        return node.get("text", "")
                    return " ".join(_adf_text(child) for child in node.get("content", []))
                body = _adf_text(body)
            result.append({
                "author": c.get("author", {}).get("displayName", "unknown"),
                "body": body[:500],
                "created": c.get("created", ""),
            })
        return result
    except Exception:
        return []


def build_comment_summary(comments: list[dict]) -> str:
    """Summarise existing comments for PM context injection."""
    if not comments:
        return "(no existing comments)"
    lines = [f"Total comments: {len(comments)}"]
    for c in comments[-5:]:  # last 5 comments
        lines.append(f"- [{c['created'][:10]}] {c['author']}: {c['body'][:120]}")
    return "\n".join(lines)


# ─── Jira event handlers ──────────────────────────────────────────────────────

def on_cycle_planned(
    cycle: int,
    branch: str,
    agents: list[str],
    jira_keys: list[str],
) -> list[dict]:
    """
    GJCI-026: Post planning comment to each selected Jira issue.
    Also reads existing comments so PM has full context.
    """
    from automation.jira_client import add_comment, transition_issue
    results = []
    now = datetime.now(UTC).isoformat()
    for key in jira_keys:
        try:
            # Transition to In Progress
            try:
                transition_issue(key, IN_PROGRESS_TRANSITION_ID)
            except Exception:
                pass  # May already be In Progress

            body = (
                f"[Autonomous Runner] Cycle {cycle:03d} — Starting work\n"
                f"Branch: {branch}\n"
                f"Agents: {', '.join(agents)}\n"
                f"This story is now In Progress. Agents will verify all AC items.\n"
                f"Planned at: {now}"
            )
            add_comment(key, body)
            results.append({"key": key, "action": "planning_comment", "status": "ok"})
        except Exception as e:
            results.append({"key": key, "action": "planning_comment", "status": "error", "error": str(e)})
    return results


def on_agent_complete(
    cycle: int,
    agent: str,
    branch: str,
    pr_number: int | None,
    files_changed: list[str],
    validation_passed: bool,
    jira_keys: list[str],
    agent_report_text: str = "",
) -> list[dict]:
    """
    GJCI-027: Post implementation evidence after each agent completes.
    Includes AC verification — checks which AC items were addressed.
    """
    from automation.jira_client import add_comment, get_issue
    results = []
    now = datetime.now(UTC).isoformat()

    for key in jira_keys:
        try:
            # Fetch issue AC for verification
            ac_check: dict = {}
            try:
                issue = get_issue(key)
                fields = issue.get("fields", {})
                description = fields.get("description", "") or ""
                if isinstance(description, dict):
                    # ADF — extract plain text
                    def _t(n: dict) -> str:
                        return n.get("text", "") if n.get("type") == "text" else \
                               " ".join(_t(c) for c in n.get("content", []))
                    description = _t(description)
                ac_items = extract_ac_items(description)
                if ac_items and agent_report_text:
                    ac_check = verify_ac_against_evidence(ac_items, agent_report_text)
            except Exception:
                ac_check = {}

            files_str = "\n".join(f"  - {f}" for f in files_changed[:15]) or "  (none)"
            pr_str = f"PR #{pr_number}" if pr_number else "PR pending"

            # Build AC verification summary
            ac_lines = ""
            if ac_check:
                verified = ac_check.get("verified", [])
                unverified = ac_check.get("unverified", [])
                ac_lines = (
                    f"\nAC Verification ({len(verified)} verified, {len(unverified)} pending):\n"
                    + "\n".join(f"  ✓ {a[:80]}" for a in verified[:5])
                    + ("\n" + "\n".join(f"  ⏳ {a[:80]}" for a in unverified[:5]) if unverified else "")
                )

            body = (
                f"[Autonomous Runner] Agent {agent} complete — Cycle {cycle:03d}\n"
                f"Branch: {branch} | {pr_str}\n"
                f"Validation: {'PASS ✓' if validation_passed else 'FAIL ✗'}\n"
                f"Files changed ({len(files_changed)}):\n{files_str}"
                f"{ac_lines}\n"
                f"Completed at: {now}"
            )
            add_comment(key, body)
            results.append({
                "key": key, "action": "agent_evidence", "agent": agent,
                "status": "ok", "ac_check": ac_check,
            })
        except Exception as e:
            results.append({"key": key, "action": "agent_evidence", "status": "error", "error": str(e)})
    return results


def on_pr_opened(
    cycle: int,
    pr_number: int,
    branch: str,
    jira_keys: list[str],
) -> list[dict]:
    """GJCI-028: Transition issues to In Review when PR is opened."""
    from automation.jira_client import add_comment, transition_issue
    results = []
    for key in jira_keys:
        try:
            transition_issue(key, IN_REVIEW_TRANSITION_ID)
            add_comment(key,
                f"[Autonomous Runner] PR #{pr_number} opened for Cycle {cycle:03d}\n"
                f"Branch: {branch}\n"
                f"CI checks in progress. All AC items must pass before merging."
            )
            results.append({"key": key, "action": "in_review_transition", "status": "ok"})
        except Exception as e:
            results.append({"key": key, "action": "in_review_transition", "status": "error", "error": str(e)})
    return results


def on_cycle_merged(
    cycle: int,
    merge_sha: str,
    jira_keys: list[str],
    ac_verification_results: dict[str, dict] | None = None,
) -> list[dict]:
    """
    GJCI-029: Verify ALL AC/DOD items, then transition to Done.
    BLOCKS Done transition if any AC item is unverified.
    This is the critical gate — stories cannot be marked Done without full AC verification.
    """
    from automation.jira_client import add_comment, transition_issue
    results = []
    now = datetime.now(UTC).isoformat()

    for key in jira_keys:
        ac_result = (ac_verification_results or {}).get(key, {})

        # SAFETY (Codex P1): if NO real AC-verification result was supplied for this
        # story, we CANNOT mark it Done. The old default read the description and set
        # `unverified=[]` ("assume all AC met if tests pass") — which closed EVERY
        # passed story regardless of whether its acceptance criteria were actually met
        # by the merged work. A passing CI run is NOT per-story AC verification. So with
        # no real result, SKIP the transition (the story stays in its current state and
        # is re-checked on a later merge once verification exists). Done requires
        # explicit, real verification passed in by the caller.
        if not ac_result:
            results.append({
                "key": key, "action": "skip_no_ac_verification", "status": "skipped",
            })
            continue

        unverified = ac_result.get("unverified", [])
        verified   = ac_result.get("verified", [])

        if unverified:
            # BLOCK Done transition — unverified AC items
            try:
                add_comment(key,
                    f"[Autonomous Runner] MERGE COMPLETE but AC verification incomplete — Cycle {cycle:03d}\n"
                    f"Merge SHA: {merge_sha}\n"
                    f"AC items NOT YET VERIFIED ({len(unverified)}):\n"
                    + "\n".join(f"  ⏳ {a[:100]}" for a in unverified[:10])
                    + f"\n\nThis story remains In Review until all AC items are verified.\n"
                    f"Merged at: {now}"
                )
            except Exception:
                pass
            results.append({
                "key": key, "action": "merge_incomplete_ac",
                "status": "blocked", "unverified_count": len(unverified),
            })
        else:
            # All AC verified — transition to Done
            try:
                transition_issue(key, DONE_TRANSITION_ID)
                add_comment(key,
                    f"[Autonomous Runner] DONE ✓ — Cycle {cycle:03d} merged\n"
                    f"Merge SHA: {merge_sha}\n"
                    f"All {len(verified)} AC items verified ✓\n"
                    f"Closed at: {now}"
                )
                results.append({"key": key, "action": "done_transition", "status": "ok"})
            except Exception as e:
                results.append({"key": key, "action": "done_transition", "status": "error", "error": str(e)})

    return results


def read_all_story_comments_for_pm_context(
    jira_keys: list[str],
) -> dict[str, str]:
    """
    Read all existing comments on the Wave 11 stories.
    Returns {issue_key: comment_summary} for PM context injection.
    The PM (Claude) reads these to understand history and avoid contradictions.
    """
    summaries: dict[str, str] = {}
    for key in jira_keys:
        comments = fetch_story_comments(key)
        summaries[key] = build_comment_summary(comments)
    return summaries


def create_blocker_ticket(
    cycle: int,
    agent: str,
    failure_type: str,
    description: str,
) -> str | None:
    """GJCI-030: Create bug/rework ticket when repair is exhausted."""
    from automation.jira_client import create_issue
    try:
        summary = f"[C{cycle:03d} A{agent}] Repair exhausted: {failure_type}"
        body = (
            f"Cycle: {cycle:03d}\n"
            f"Agent: {agent}\n"
            f"Failure type: {failure_type}\n"
            f"Created by: Autonomous Runner\n\n"
            f"{description}"
        )
        result = create_issue(
            project_key="SCRUM",
            summary=summary,
            description=body,
            issue_type="Bug",
            labels=["ai-runner", f"cycle:{cycle:03d}"],
        )
        return result.get("key")
    except Exception:
        return None


def write_jira_sync_log(run_dir: Path, updates: list[dict]) -> Path:
    """Write jira_sync.json to the run directory."""
    run_dir.mkdir(parents=True, exist_ok=True)
    path = run_dir / "jira" / "jira_sync.json"
    path.parent.mkdir(exist_ok=True)
    path.write_text(json.dumps({
        "update_count": len(updates),
        "updates": updates,
        "generated_at": datetime.now(UTC).isoformat(),
    }, indent=2))
    return path
