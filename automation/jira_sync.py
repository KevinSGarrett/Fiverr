"""
jira_sync.py â€” Automated Jira sync during runner cycle execution.
Implements GJCI-023..030: comment, transition, evidence posting, Done closeout.

Called at key points in the run loop:
  - on_cycle_planned(): post planning comments to selected issues
  - on_agent_complete(): post implementation evidence
  - on_pr_opened(): transition selected issues to In Review
  - on_cycle_merged(): transition to Done, create next control ticket
  - on_repair_exhausted(): create blocker/rework ticket
"""
from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path

REPO_ROOT = Path(__file__).parent.parent

# Jira transition IDs (GJCI-025)
DONE_TRANSITION_ID = "41"       # Done
IN_REVIEW_TRANSITION_ID = "31"  # In Review (adjust if different in your board)
IN_PROGRESS_TRANSITION_ID = "21"  # In Progress


def post_status_map() -> dict:
    """GJCI-025: Return known status/transition map."""
    return {
        "DONE": DONE_TRANSITION_ID,
        "IN_REVIEW": IN_REVIEW_TRANSITION_ID,
        "IN_PROGRESS": IN_PROGRESS_TRANSITION_ID,
    }


def on_cycle_planned(cycle: int, branch: str, agents: list[str],
                     jira_keys: list[str]) -> list[dict]:
    """GJCI-026: Post planning comment to each selected Jira issue."""
    from automation.jira_client import add_comment
    results = []
    now = datetime.now(UTC).isoformat()
    for key in jira_keys:
        try:
            body = (
                f"[Autonomous Runner] Cycle {cycle:03d} planning\n"
                f"Branch: {branch}\n"
                f"Agents: {', '.join(agents)}\n"
                f"Planned at: {now}"
            )
            add_comment(key, body)
            results.append({"key": key, "action": "planning_comment", "status": "ok"})
        except Exception as e:
            results.append({"key": key, "action": "planning_comment", "status": "error", "error": str(e)})
    return results


def on_agent_complete(cycle: int, agent: str, branch: str, pr_number: int | None,
                      files_changed: list[str], validation_passed: bool,
                      jira_keys: list[str]) -> list[dict]:
    """GJCI-027: Post implementation evidence after each agent completes."""
    from automation.jira_client import add_comment
    results = []
    now = datetime.now(UTC).isoformat()
    for key in jira_keys:
        try:
            files_str = "\n".join(f"  - {f}" for f in files_changed[:10]) or "  (none)"
            pr_str = f"PR #{pr_number}" if pr_number else "PR not yet created"
            body = (
                f"[Autonomous Runner] Agent {agent} complete â€” Cycle {cycle:03d}\n"
                f"Branch: {branch}\n"
                f"{pr_str}\n"
                f"Validation: {'PASS' if validation_passed else 'FAIL'}\n"
                f"Files changed:\n{files_str}\n"
                f"Completed at: {now}"
            )
            add_comment(key, body)
            results.append({"key": key, "action": "agent_evidence", "agent": agent, "status": "ok"})
        except Exception as e:
            results.append({"key": key, "action": "agent_evidence", "status": "error", "error": str(e)})
    return results


def on_pr_opened(cycle: int, pr_number: int, branch: str,
                 jira_keys: list[str]) -> list[dict]:
    """GJCI-028: Transition issues to In Review when PR is opened."""
    from automation.jira_client import add_comment, transition_issue
    results = []
    for key in jira_keys:
        try:
            transition_issue(key, IN_REVIEW_TRANSITION_ID)
            add_comment(key, f"[Autonomous Runner] PR #{pr_number} opened for cycle {cycle:03d} branch {branch}")
            results.append({"key": key, "action": "in_review_transition", "status": "ok"})
        except Exception as e:
            results.append({"key": key, "action": "in_review_transition", "status": "error", "error": str(e)})
    return results


def on_cycle_merged(cycle: int, merge_sha: str,
                    jira_keys: list[str]) -> list[dict]:
    """GJCI-029: Transition to Done after merge + full DoD evidence."""
    from automation.jira_client import add_comment, transition_issue
    results = []
    now = datetime.now(UTC).isoformat()
    for key in jira_keys:
        try:
            transition_issue(key, DONE_TRANSITION_ID)
            add_comment(key,
                f"[Autonomous Runner] DONE â€” Cycle {cycle:03d} merged to develop\n"
                f"Merge SHA: {merge_sha}\n"
                f"Closed at: {now}"
            )
            results.append({"key": key, "action": "done_transition", "status": "ok"})
        except Exception as e:
            results.append({"key": key, "action": "done_transition", "status": "error", "error": str(e)})
    return results


def create_blocker_ticket(cycle: int, agent: str, failure_type: str,
                           description: str) -> str | None:
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
