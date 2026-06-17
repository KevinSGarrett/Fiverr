"""
github_reviewer.py — PM GitHub health audit.

Called by the post-cycle review AND by claude_prompt_creator before writing agent prompts.
Gives Claude PM a complete view of the GitHub repo state so it can:
  1. Identify failing CI checks and root-cause them
  2. Find unresolved review threads that block merge
  3. Detect stale open issues from repair loops
  4. Verify the cycle branch exists and is ahead of develop
  5. Check PR status and whether agents actually delivered code
  6. Build a structured "action list" the PM uses to direct the next cycle

Claude PM reads this report and either:
  A. Directly fixes issues it can resolve autonomously (close issues, resolve threads, etc.)
  B. Injects explicit repair tasks into the cursor agent prompts for issues needing code changes
"""
from __future__ import annotations

import json
import subprocess
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

REPO_ROOT = Path("C:/Fiverr/Fiverr")
REPO      = "KevinSGarrett/Fiverr"


@dataclass
class GitHubHealthReport:
    generated_at: str = ""
    cycle: int = 0
    branch: str = ""

    # Branch
    branch_exists_on_remote: bool = False
    branch_ahead_of_develop: int = 0
    branch_behind_develop: int = 0

    # Open PRs
    open_prs: list[dict] = field(default_factory=list)
    pr_for_cycle: dict | None = None
    pr_checks_failing: list[str] = field(default_factory=list)
    pr_unresolved_threads: list[dict] = field(default_factory=list)

    # CI on develop
    develop_ci_status: str = "unknown"
    develop_last_ci_run: str = ""
    recent_failures: list[dict] = field(default_factory=list)

    # GitHub Issues
    open_runner_issues: list[dict] = field(default_factory=list)

    # Code quality (latest CI run on cycle branch)
    lint_passing: bool | None = None
    tests_passing: bool | None = None
    coverage_ok: bool | None = None
    type_check_passing: bool | None = None

    # Jira sync (cross-reference)
    jira_stories_in_progress: list[str] = field(default_factory=list)

    # Summary
    action_items: list[str] = field(default_factory=list)
    blockers: list[str] = field(default_factory=list)
    health_score: int = 0  # 0-100


def _gh(*args: str) -> tuple[int, str]:
    """Run a gh CLI command. Returns (returncode, stdout)."""
    try:
        r = subprocess.run(
            ["gh", *args],
            capture_output=True, text=True, cwd=str(REPO_ROOT), timeout=30
        )
        return r.returncode, (r.stdout or "").strip()
    except Exception as e:
        return -1, str(e)


def _git(*args: str) -> tuple[int, str]:
    """Run a git command."""
    try:
        r = subprocess.run(
            ["git", *args],
            capture_output=True, text=True, cwd=str(REPO_ROOT), timeout=30
        )
        return r.returncode, (r.stdout or "").strip()
    except Exception as e:
        return -1, str(e)


def _gh_json(field_names: str, *args: str) -> Any:
    """Run gh command with --json and return parsed data."""
    rc, out = _gh(*args, "--json", field_names)
    if rc != 0 or not out:
        return None
    try:
        return json.loads(out)
    except json.JSONDecodeError:
        return None


def audit_branch(report: GitHubHealthReport) -> None:
    """Check if cycle branch exists and how far it is from develop."""
    rc, out = _git("ls-remote", "--heads", "origin", report.branch)
    report.branch_exists_on_remote = rc == 0 and report.branch in out

    if report.branch_exists_on_remote:
        _git("fetch", "origin", report.branch, "develop", "--quiet")
        # Ahead = commits in branch not in develop
        rc, ahead = _git("rev-list", "--count",
                         f"origin/develop..origin/{report.branch}")
        report.branch_ahead_of_develop = int(ahead) if rc == 0 and ahead.isdigit() else 0
        # Behind = commits in develop not in branch
        rc, behind = _git("rev-list", "--count",
                          f"origin/{report.branch}..origin/develop")
        report.branch_behind_develop = int(behind) if rc == 0 and behind.isdigit() else 0
    else:
        report.action_items.append(
            f"CRITICAL: branch {report.branch} does not exist on remote — "
            f"must be created from develop before agents can push"
        )
        report.blockers.append(f"missing_branch:{report.branch}")


def audit_prs(report: GitHubHealthReport) -> None:
    """Fetch open PRs and detailed check/thread status for the cycle PR."""
    data = _gh_json("number,title,headRefName,state,isDraft,additions,deletions,"
                    "reviewDecision,labels,mergeStateStatus,autoMergeRequest",
                    "pr", "list", "--state", "open", "--repo", REPO)
    if data:
        report.open_prs = data
        # Find the PR for this cycle
        for pr in data:
            if pr.get("headRefName") == report.branch:
                report.pr_for_cycle = pr
                break

    if not report.pr_for_cycle:
        report.action_items.append(
            f"No open PR for {report.branch} — Agent D must create the PR after implementation"
        )
        return

    pr_num = report.pr_for_cycle["number"]

    # PR checks
    rc, checks_out = _gh("pr", "checks", str(pr_num), "--repo", REPO)
    if rc == 0 and checks_out:
        for line in checks_out.splitlines():
            parts = line.split("\t")
            if len(parts) >= 2 and parts[1].strip() in ("fail", "failure"):
                report.pr_checks_failing.append(parts[0].strip())

    # Unresolved review threads via GraphQL
    query = (
        'query($pr:Int!,$owner:String!,$repo:String!){'
        'repository(owner:$owner,name:$repo){'
        'pullRequest(number:$pr){'
        'reviewThreads(first:50){'
        'nodes{id isResolved isOutdated '
        'comments(first:1){nodes{author{login} body path}}'
        '}}}}}')
    rc, gql_out = _gh("api", "graphql",
                      "-f", f"query={query}",
                      "-F", f"pr={pr_num}",
                      "-F", "owner=KevinSGarrett",
                      "-F", "repo=Fiverr")
    if rc == 0 and gql_out:
        try:
            gql = json.loads(gql_out)
            threads = (gql.get("data", {})
                       .get("repository", {})
                       .get("pullRequest", {})
                       .get("reviewThreads", {})
                       .get("nodes", []))
            unresolved = [t for t in threads
                          if not t.get("isResolved") and not t.get("isOutdated")]
            report.pr_unresolved_threads = unresolved
            for t in unresolved:
                comment = (t.get("comments", {}).get("nodes") or [{}])[0]
                path = comment.get("path", "?")
                body = (comment.get("body") or "")[:100]
                author = comment.get("author", {}).get("login", "?")
                report.action_items.append(
                    f"UNRESOLVED review thread on PR #{pr_num} by {author} "
                    f"at {path}: {body}"
                )
                report.blockers.append(f"unresolved_thread:{t.get('id','?')}")
        except json.JSONDecodeError:
            pass

    if report.pr_checks_failing:
        for check in report.pr_checks_failing:
            report.blockers.append(f"failing_check:{check}")
            report.action_items.append(
                f"FAILING CI CHECK on PR #{pr_num}: {check} — "
                f"fix the failure before merging"
            )


def audit_ci(report: GitHubHealthReport) -> None:
    """Get recent CI status on develop and the cycle branch."""
    # develop CI
    data = _gh_json(
        "conclusion,status,headBranch,displayTitle,createdAt",
        "run", "list", "--branch", "develop", "--limit", "5",
        "--workflow", "CI", "--repo", REPO
    )
    if data:
        latest = data[0] if data else {}
        report.develop_ci_status = latest.get("conclusion") or latest.get("status", "unknown")
        report.develop_last_ci_run = latest.get("createdAt", "")

    # Recent failures across all branches
    data_all = _gh_json(
        "conclusion,displayTitle,headBranch,workflowName,createdAt,databaseId",
        "run", "list", "--limit", "20", "--repo", REPO
    )
    if data_all:
        report.recent_failures = [
            r for r in data_all
            if r.get("conclusion") == "failure"
        ][:5]

    # CI checks on cycle branch (most recent run)
    if report.branch_exists_on_remote:
        branch_runs = _gh_json(
            "conclusion,workflowName,status",
            "run", "list", "--branch", report.branch,
            "--limit", "5", "--repo", REPO
        )
        if branch_runs:
            for run in branch_runs:
                wf = run.get("workflowName", "")
                conclusion = run.get("conclusion", "")
                if wf == "CI" and conclusion:
                    report.lint_passing      = "lint" not in str(conclusion)
                    report.tests_passing     = conclusion == "success"
                    report.coverage_ok       = conclusion == "success"
                    report.type_check_passing = conclusion == "success"
                    break


def audit_issues(report: GitHubHealthReport) -> None:
    """Find open runner-generated issues."""
    data = _gh_json(
        "number,title,labels,createdAt",
        "issue", "list", "--state", "open",
        "--label", "ai-runner", "--limit", "20", "--repo", REPO
    )
    if data:
        report.open_runner_issues = data
        for issue in data:
            report.action_items.append(
                f"STALE open issue #{issue['number']}: {issue['title'][:80]} — "
                f"close if resolved"
            )


def audit_jira_sync(report: GitHubHealthReport, jira_issues: list[dict]) -> None:
    """Cross-check Jira stories that should be In Progress for this cycle."""
    for issue in jira_issues:
        status = issue.get("status", "")
        if status in ("In Progress", "In Review"):
            report.jira_stories_in_progress.append(issue.get("key", "?"))


def build_health_report(
    cycle: int,
    branch: str,
    jira_issues: list[dict] | None = None,
) -> GitHubHealthReport:
    """Build a complete GitHub health report for the PM to read."""
    report = GitHubHealthReport(
        generated_at=datetime.now(UTC).isoformat(),
        cycle=cycle,
        branch=branch,
    )

    audit_branch(report)
    audit_prs(report)
    audit_ci(report)
    audit_issues(report)
    if jira_issues:
        audit_jira_sync(report, jira_issues)

    # Score: start at 100, deduct for each issue
    score = 100
    score -= len(report.blockers) * 15
    score -= len([a for a in report.action_items if "CRITICAL" in a]) * 20
    score -= len(report.pr_checks_failing) * 10
    score -= len(report.recent_failures) * 3
    score -= len(report.open_runner_issues) * 5
    report.health_score = max(0, score)

    return report


def format_report_for_pm(report: GitHubHealthReport) -> str:
    """Format the health report as readable text for Claude PM context."""
    lines = [
        "=" * 60,
        f"GITHUB HEALTH REPORT — Cycle {report.cycle:03d}",
        f"Generated: {report.generated_at}",
        f"Health score: {report.health_score}/100",
        "=" * 60,
        "",
        "## BRANCH STATE",
        f"  Branch: {report.branch}",
        f"  Exists on remote: {report.branch_exists_on_remote}",
        f"  Ahead of develop: {report.branch_ahead_of_develop} commits",
        f"  Behind develop: {report.branch_behind_develop} commits",
        "",
        "## CI STATUS",
        f"  develop CI: {report.develop_ci_status}",
        f"  Lint passing: {report.lint_passing}",
        f"  Tests passing: {report.tests_passing}",
        f"  Coverage OK: {report.coverage_ok}",
        f"  Type-check passing: {report.type_check_passing}",
        "",
        "## PR STATUS",
    ]

    if report.pr_for_cycle:
        pr = report.pr_for_cycle
        lines += [
            f"  PR #{pr['number']}: {pr.get('title','')[:60]}",
            f"  State: {pr.get('state')}  Draft: {pr.get('isDraft')}",
            f"  Merge state: {pr.get('mergeStateStatus')}",
            f"  Failing checks: {report.pr_checks_failing or 'none'}",
            f"  Unresolved threads: {len(report.pr_unresolved_threads)}",
        ]
    else:
        lines.append("  No PR open for this cycle branch yet")

    lines += [
        "",
        "## FAILING CI CHECKS",
    ]
    if report.pr_checks_failing:
        for c in report.pr_checks_failing:
            lines.append(f"  FAIL: {c}")
    else:
        lines.append("  None")

    lines += [
        "",
        "## UNRESOLVED REVIEW THREADS",
    ]
    if report.pr_unresolved_threads:
        for t in report.pr_unresolved_threads:
            c = (t.get("comments", {}).get("nodes") or [{}])[0]
            lines.append(
                f"  Thread {t.get('id','?')} by {c.get('author',{}).get('login','?')} "
                f"at {c.get('path','?')}: {(c.get('body') or '')[:80]}"
            )
    else:
        lines.append("  None")

    lines += [
        "",
        "## OPEN RUNNER ISSUES (stale — should be closed)",
    ]
    if report.open_runner_issues:
        for issue in report.open_runner_issues:
            lines.append(f"  #{issue['number']}: {issue['title'][:70]}")
    else:
        lines.append("  None (clean)")

    lines += [
        "",
        "## ACTION ITEMS FOR THIS CYCLE",
    ]
    if report.action_items:
        for i, item in enumerate(report.action_items, 1):
            lines.append(f"  {i}. {item}")
    else:
        lines.append("  None — repo is healthy")

    lines += [
        "",
        "## BLOCKERS (must resolve before agents can merge)",
    ]
    if report.blockers:
        for b in report.blockers:
            lines.append(f"  BLOCK: {b}")
    else:
        lines.append("  None")

    lines += [
        "",
        "## JIRA STORIES IN PROGRESS",
        "  " + (", ".join(report.jira_stories_in_progress) or "none"),
        "",
    ]

    return "\n".join(lines)


def auto_fix_what_we_can(report: GitHubHealthReport) -> list[str]:
    """
    Autonomously fix issues the PM can handle without code changes:
    - Close stale runner issues
    - Resolve outdated review threads

    Returns list of actions taken.
    """
    actions_taken = []

    # Close stale runner-generated issues
    for issue in report.open_runner_issues:
        rc, _ = _gh("issue", "close", str(issue["number"]),
                    "--comment",
                    "Auto-closed by PM reviewer: issue superseded by system fixes in subsequent cycles.",
                    "--repo", REPO)
        if rc == 0:
            actions_taken.append(f"Closed stale issue #{issue['number']}: {issue['title'][:50]}")

    # Resolve OUTDATED review threads (not just unresolved — outdated ones block nothing)
    if report.pr_for_cycle:
        pr_num = report.pr_for_cycle["number"]
        query = (
            'query($pr:Int!,$owner:String!,$repo:String!){'
            'repository(owner:$owner,name:$repo){'
            'pullRequest(number:$pr){'
            'reviewThreads(first:50){'
            'nodes{id isResolved isOutdated}}}}}')
        rc, gql_out = _gh("api", "graphql",
                          "-f", f"query={query}",
                          "-F", f"pr={pr_num}",
                          "-F", "owner=KevinSGarrett",
                          "-F", "repo=Fiverr")
        if rc == 0 and gql_out:
            try:
                gql = json.loads(gql_out)
                threads = (gql.get("data", {})
                           .get("repository", {})
                           .get("pullRequest", {})
                           .get("reviewThreads", {})
                           .get("nodes", []))
                for t in threads:
                    if t.get("isOutdated") and not t.get("isResolved"):
                        mutation = (
                            'mutation($id:ID!){'
                            'resolveReviewThread(input:{threadId:$id})'
                            '{thread{isResolved}}}')
                        _gh("api", "graphql",
                            "-f", f"query={mutation}",
                            "-F", f"id={t['id']}")
                        actions_taken.append(
                            f"Resolved outdated thread {t['id']} on PR #{pr_num}"
                        )
            except json.JSONDecodeError:
                pass

    return actions_taken
