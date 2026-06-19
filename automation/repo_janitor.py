#!/usr/bin/env python3
"""
repo_janitor.py - Autonomous repository hygiene for the 24/7 cycle runner.

WHY THIS EXISTS
The repo accumulated 40 local branches / 21 stashes / 9 worktrees under
unattended 24/7 operation. Root cause: the documented hygiene
(PM_Pack/ref/github/08_hygiene/HYGIENE_CHECKLIST.md) classifies branch/stash/
worktree cleanup as *Weekly Hygiene - Human Operator*, which never runs when no
human is in the loop; and the repo's delete-branch-after-merge setting only
removes the *remote* branch on merge - never local branches, stashes, or
worktrees. branch_guard.py PREVENTS unsafe ops and post_cycle_review.py
VERIFIES state, but nothing actively CLEANS. This module is that missing piece.

SQUASH-MERGE AWARENESS
github_policy.yml merges cycle branches with `method: squash`. A squash-merge
creates a NEW commit on develop rather than a fast-forwardable ancestor, so the
merged cycle branch is NOT detectable via `git branch --merged develop`. This
janitor therefore also consults the set of MERGED pull-request head branches
(via gh) and treats those as prunable - the only reliable way to garbage-collect
the squash-merged cycle branches that are the main source of accumulation.

SAFETY MODEL (aligned with PM_Pack/automation/github_policy.yml blocked_operations)
  * DRY-RUN by default - mutations require execute=True.
  * NEVER touches protected branches (main/master/develop) or the current branch.
  * NEVER touches the CI self-hosted runner: any worktree/branch under
    C:/actions-runner/** (or any path containing _work) is hard-excluded.
  * Ancestry-merged branches are removed with `git branch -d` (git's own
    merged-only guard). PR-squash-merged branches are removed with `-D`, but
    ONLY after confirming a MERGED PR for that exact head branch, and a recovery
    tag (branch-janitor-backup-*) is written first so the delete is recoverable.
  * Remote cycle branches are deleted only when ancestry-merged OR PR-merged.
  * Stash drops are gated by an allow-list of auto-created stash name patterns
    AND a minimum age, with a recovery tag (stash-janitor-backup-*) per drop.
  * Worktrees are removed only when clean (no --force) and obsolete.
  * Everything is logged and returned as a structured JanitorReport.

USAGE
    python -m automation.repo_janitor                 # dry-run report
    python -m automation.repo_janitor --execute       # perform cleanup
    python -m automation.repo_janitor --json          # machine-readable
"""
from __future__ import annotations

import json
import re
import subprocess
import time
from dataclasses import dataclass, field
from pathlib import Path

REPO_ROOT = Path("C:/Fiverr/Fiverr")
REPO_SLUG = "KevinSGarrett/Fiverr"
DEFAULT_BASE = "develop"

try:
    from automation.branch_guard import PROTECTED_BRANCHES
except Exception:  # pragma: no cover - fallback if import path differs
    PROTECTED_BRANCHES = {"main", "master", "develop"}

# Auto-created stash name fragments that are safe to garbage-collect once stale.
STALE_STASH_PATTERNS = (
    "preflight", "preserve", "temp", "tmp", "quarantine",
    "auto", "wip-cycle", "pre-cycle", "agent-a", "agentd", "janitor",
)
DEFAULT_STASH_MIN_AGE_H = 72  # never touch stashes newer than 3 days
CYCLE_BRANCH_RE = re.compile(r"^cycle/\d+/integration$")


# ── data model ────────────────────────────────────────────────────────────
@dataclass
class JanitorAction:
    kind: str  # branch_local | branch_remote | stash | worktree
    target: str
    detail: str = ""
    executed: bool = False


@dataclass
class JanitorReport:
    execute: bool
    base: str
    clean_tree: bool = True
    actions: list[JanitorAction] = field(default_factory=list)
    skipped: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)

    def add(self, kind: str, target: str, detail: str = "", executed: bool = False) -> None:
        self.actions.append(JanitorAction(kind, target, detail, executed))

    def counts(self) -> dict[str, int]:
        by: dict[str, int] = {}
        for a in self.actions:
            by[a.kind] = by.get(a.kind, 0) + 1
        return by

    def summary(self) -> str:
        mode = "EXECUTE" if self.execute else "DRY-RUN"
        lines = [f"[repo_janitor {mode}] base={self.base} clean_tree={self.clean_tree}"]
        for k, v in sorted(self.counts().items()):
            lines.append(f"  {k}: {v}")
        if self.skipped:
            lines.append(f"  skipped: {len(self.skipped)}")
        if self.errors:
            lines.append(f"  errors: {len(self.errors)}")
        return "\n".join(lines)

    def to_dict(self) -> dict:
        return {
            "execute": self.execute,
            "base": self.base,
            "clean_tree": self.clean_tree,
            "counts": self.counts(),
            "actions": [vars(a) for a in self.actions],
            "skipped": self.skipped,
            "errors": self.errors,
        }


# ── git / gh helpers ──────────────────────────────────────────────────────
def _git(args: list[str], cwd: Path = REPO_ROOT) -> tuple[int, str]:
    p = subprocess.run(
        ["git", *args], cwd=str(cwd),
        capture_output=True, text=True, errors="replace",
    )
    return p.returncode, ((p.stdout or "") + (p.stderr or "")).strip()


def _is_ci_path(path: str) -> bool:
    p = path.replace("\\", "/").lower()
    return "actions-runner" in p or "/_work/" in p


def current_branch(cwd: Path = REPO_ROOT) -> str:
    _, out = _git(["rev-parse", "--abbrev-ref", "HEAD"], cwd)
    return out.strip()


def verify_clean_tree(cwd: Path = REPO_ROOT) -> bool:
    _, out = _git(["status", "--porcelain"], cwd)
    return out.strip() == ""


def merged_pr_heads(cwd: Path = REPO_ROOT, repo: str = REPO_SLUG) -> set[str]:
    """Head branch names of MERGED pull requests.

    Required because squash-merges (this repo's policy) are not detectable via
    `git branch --merged`. Returns an empty set if gh is unavailable so the
    janitor degrades to ancestry-only detection rather than failing.
    """
    p = subprocess.run(
        ["gh", "pr", "list", "--repo", repo, "--state", "merged",
         "--limit", "300", "--json", "headRefName"],
        cwd=str(cwd), capture_output=True,
    )
    if p.returncode != 0:
        return set()
    try:
        data = json.loads((p.stdout or b"").decode("utf-8", "replace") or "[]")
    except Exception:
        return set()
    return {d.get("headRefName", "") for d in data if d.get("headRefName")}


# ── worktrees ─────────────────────────────────────────────────────────────
def list_worktrees(cwd: Path = REPO_ROOT) -> list[dict]:
    _, out = _git(["worktree", "list", "--porcelain"], cwd)
    trees: list[dict] = []
    cur: dict = {}
    for line in out.splitlines():
        if line.startswith("worktree "):
            if cur:
                trees.append(cur)
            cur = {"path": line[len("worktree "):].strip()}
        elif line.startswith("branch "):
            cur["branch"] = line[len("branch "):].strip().replace("refs/heads/", "")
    if cur:
        trees.append(cur)
    return trees


def find_obsolete_worktrees(cwd: Path = REPO_ROOT) -> list[dict]:
    """Worktrees that are neither the main checkout nor a CI-runner worktree."""
    main = str(cwd).replace("\\", "/").lower().rstrip("/")
    out: list[dict] = []
    for wt in list_worktrees(cwd):
        p = wt.get("path", "")
        pl = p.replace("\\", "/").lower().rstrip("/")
        if pl == main or _is_ci_path(p):
            continue
        out.append(wt)
    return out


def prune_worktrees(report: JanitorReport, cwd: Path = REPO_ROOT) -> None:
    for wt in find_obsolete_worktrees(cwd):
        p = wt["path"]
        if report.execute:
            rc, msg = _git(["worktree", "remove", p], cwd)  # no --force: clean only
            if rc != 0:
                report.skipped.append(f"worktree not removed (dirty/locked?): {p} ({msg[:50]})")
                continue
        report.add("worktree", p, wt.get("branch", ""), executed=report.execute)


# ── local branches ────────────────────────────────────────────────────────
def _ci_branches(cwd: Path = REPO_ROOT) -> set[str]:
    return {
        wt["branch"] for wt in list_worktrees(cwd)
        if _is_ci_path(wt.get("path", "")) and wt.get("branch")
    }


def find_prunable_local_branches(cwd: Path = REPO_ROOT, base: str = DEFAULT_BASE,
                                 pr_heads: set[str] | None = None) -> list[tuple[str, str]]:
    """Return [(branch, mode)] where mode is 'ancestry' (in `git branch
    --merged base`) or 'squash' (head of a merged PR, not an ancestor of base).
    Protected/current/CI/base branches are always excluded.
    """
    keep = PROTECTED_BRANCHES | {current_branch(cwd), base} | _ci_branches(cwd)

    ancestry: set[str] = set()
    rc, out = _git(["branch", "--merged", base], cwd)
    if rc == 0:
        for line in out.splitlines():
            n = line.replace("*", "").strip()
            if n and not n.startswith("(") and n not in keep:
                ancestry.add(n)

    heads = merged_pr_heads(cwd) if pr_heads is None else set(pr_heads)
    local: set[str] = set()
    rc, out = _git(["branch", "--format=%(refname:short)"], cwd)
    if rc == 0:
        local = {ln.strip() for ln in out.splitlines() if ln.strip()}

    result: list[tuple[str, str]] = [(n, "ancestry") for n in sorted(ancestry)]
    for n in sorted(local & heads):
        if n in keep or n in ancestry:
            continue
        result.append((n, "squash"))
    return result


def prune_local_branches(report: JanitorReport, cwd: Path = REPO_ROOT,
                         base: str = DEFAULT_BASE, pr_heads: set[str] | None = None) -> None:
    for name, mode in find_prunable_local_branches(cwd, base, pr_heads):
        if report.execute:
            if mode == "squash":
                rc, sha = _git(["rev-parse", name], cwd)
                if rc == 0 and sha:  # recovery tag: -D stays recoverable
                    tag = "branch-janitor-backup-" + re.sub(r"\W", "-", name) + "-" + sha[:7]
                    _git(["tag", "-f", tag, sha], cwd)
                flag = "-D"  # squash-merge is not ancestry-merged; PR-confirmed merged
            else:
                flag = "-d"  # git refuses unless truly merged
            rc, msg = _git(["branch", flag, name], cwd)
            if rc != 0:
                report.skipped.append(f"local branch not deleted: {name} ({msg[:50]})")
                continue
        report.add("branch_local", name, f"merged({mode})", executed=report.execute)


# ── remote branches ───────────────────────────────────────────────────────
def find_prunable_remote_cycle_branches(cwd: Path = REPO_ROOT, base: str = DEFAULT_BASE,
                                        pr_heads: set[str] | None = None) -> list[str]:
    _git(["fetch", "--prune", "origin"], cwd)
    heads = merged_pr_heads(cwd) if pr_heads is None else set(pr_heads)

    def _short(line: str) -> str | None:
        n = line.strip()
        if "->" in n or not n.startswith("origin/"):
            return None
        s = n[len("origin/"):]
        if s in PROTECTED_BRANCHES or s == base or not CYCLE_BRANCH_RE.match(s):
            return None
        return s

    ancestry: set[str] = set()
    rc, out = _git(["branch", "-r", "--merged", f"origin/{base}"], cwd)
    if rc == 0:
        ancestry = {s for s in (_short(ln) for ln in out.splitlines()) if s}

    remote_cycles: set[str] = set()
    rc, out = _git(["branch", "-r", "--format=%(refname:short)"], cwd)
    if rc == 0:
        remote_cycles = {s for s in (_short(ln) for ln in out.splitlines()) if s}

    return sorted(ancestry | (remote_cycles & heads))


def prune_remote_branches(report: JanitorReport, cwd: Path = REPO_ROOT,
                          base: str = DEFAULT_BASE, pr_heads: set[str] | None = None) -> None:
    for short in find_prunable_remote_cycle_branches(cwd, base, pr_heads):
        if report.execute:
            rc, msg = _git(["push", "origin", "--delete", short], cwd)
            if rc != 0:
                report.skipped.append(f"remote branch not deleted: {short} ({msg[:50]})")
                continue
        report.add("branch_remote", short, "merged", executed=report.execute)


# ── stashes ───────────────────────────────────────────────────────────────
def list_stashes(cwd: Path = REPO_ROOT) -> list[dict]:
    rc, out = _git(["stash", "list", "--format=%gd|%ct|%gs"], cwd)
    if rc != 0:
        return []
    items: list[dict] = []
    for line in out.splitlines():
        parts = line.split("|", 2)
        if len(parts) != 3:
            continue
        ref, ts, msg = parts
        items.append({"ref": ref.strip(),
                      "ts": int(ts) if ts.strip().isdigit() else 0,
                      "msg": msg.strip()})
    return items


def find_stale_stashes(cwd: Path = REPO_ROOT,
                       min_age_h: int = DEFAULT_STASH_MIN_AGE_H,
                       patterns: tuple = STALE_STASH_PATTERNS,
                       now: float | None = None) -> list[dict]:
    now = time.time() if now is None else now
    cutoff = now - min_age_h * 3600
    out: list[dict] = []
    for s in list_stashes(cwd):
        msg = s["msg"].lower()
        if not any(p in msg for p in patterns):
            continue  # not an auto-created stash we own
        if s["ts"] and s["ts"] > cutoff:
            continue  # too new
        out.append(s)
    return out


def drop_stashes(report: JanitorReport, cwd: Path = REPO_ROOT,
                 min_age_h: int = DEFAULT_STASH_MIN_AGE_H) -> None:
    # newest-first so stash@{N} refs stay valid as earlier ones are removed
    stale = sorted(find_stale_stashes(cwd, min_age_h), key=lambda s: s["ref"], reverse=True)
    for s in stale:
        if report.execute:
            rc, sha = _git(["rev-parse", s["ref"]], cwd)
            if rc == 0 and sha:  # recovery tag first - drops stay recoverable
                tag = "stash-janitor-backup-" + re.sub(r"\D", "", s["ref"]) + "-" + sha[:7]
                _git(["tag", "-f", tag, sha], cwd)
            rc, msg = _git(["stash", "drop", s["ref"]], cwd)
            if rc != 0:
                report.skipped.append(f"stash not dropped: {s['ref']} ({msg[:50]})")
                continue
        report.add("stash", s["ref"], s["msg"][:60], executed=report.execute)


# ── orchestration ─────────────────────────────────────────────────────────
def run(execute: bool = False, base: str = DEFAULT_BASE, cwd: Path = REPO_ROOT,
        do_stashes: bool = True, stash_min_age_h: int = DEFAULT_STASH_MIN_AGE_H,
        pr_heads: set[str] | None = None) -> JanitorReport:
    report = JanitorReport(execute=execute, base=base)
    report.clean_tree = verify_clean_tree(cwd)
    if not report.clean_tree:
        report.errors.append(
            "working tree not clean - branch/stash/worktree ops remain safe, "
            "but uncommitted changes should be investigated"
        )
    if pr_heads is None:
        pr_heads = merged_pr_heads(cwd)  # one gh call, reused by local + remote
    for step in (
        lambda: prune_worktrees(report, cwd),
        lambda: prune_local_branches(report, cwd, base, pr_heads),
        lambda: prune_remote_branches(report, cwd, base, pr_heads),
    ):
        try:
            step()
        except Exception as e:  # never let one step abort the rest
            report.errors.append(f"{step}: {e}")
    if do_stashes:
        try:
            drop_stashes(report, cwd, stash_min_age_h)
        except Exception as e:
            report.errors.append(f"stash drop: {e}")
    return report


def _main(argv: list[str] | None = None) -> int:
    import argparse
    ap = argparse.ArgumentParser(description="Autonomous repo hygiene janitor.")
    ap.add_argument("--execute", action="store_true",
                    help="perform deletions (default: dry-run report only)")
    ap.add_argument("--base", default=DEFAULT_BASE, help="integration base branch")
    ap.add_argument("--no-stashes", action="store_true", help="skip stash cleanup")
    ap.add_argument("--stash-min-age-h", type=int, default=DEFAULT_STASH_MIN_AGE_H)
    ap.add_argument("--json", action="store_true", help="emit JSON report")
    a = ap.parse_args(argv)
    rep = run(execute=a.execute, base=a.base, do_stashes=not a.no_stashes,
              stash_min_age_h=a.stash_min_age_h)
    if a.json:
        print(json.dumps(rep.to_dict(), indent=2))
        return 0
    print(rep.summary())
    for act in rep.actions:
        print(f"  [{'x' if act.executed else '-'}] {act.kind}: {act.target}  {act.detail}")
    for s in rep.skipped:
        print(f"  SKIP {s}")
    for e in rep.errors:
        print(f"  ERR  {e}")
    return 0


if __name__ == "__main__":
    raise SystemExit(_main())
