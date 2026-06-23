"""Regression: the cursor-agent no-output watchdog must treat REPO FILE-WRITING as
liveness, not just stdout/stderr growth.

Observed live (cycle-84 agent B): Cursor/Codex-5.3 in --print mode buffered stdout
(stdout_B.log == 0 bytes) while productively writing 40 real src/tests files, but the
watchdog only reset its timer on stdout/stderr file growth — so it killed the working
agent at the no-output threshold ('no_output', exit -1) before it finished and wrote
its AGENT_COMPLETE report. _repo_activity_mtime() gives the missing file-activity
liveness signal that _monitor() now uses.
"""
from __future__ import annotations

import subprocess
import time

from automation.cursor_adapter import _repo_activity_mtime


def _git(repo, *args):
    return subprocess.run(["git", *args], cwd=str(repo), capture_output=True, text=True)


def _init_repo(tmp_path):
    repo = tmp_path / "repo"
    repo.mkdir()
    _git(repo, "init", "-q")
    _git(repo, "config", "user.email", "t@t.t")
    _git(repo, "config", "user.name", "t")
    (repo / "base.py").write_text("x = 1\n")
    _git(repo, "add", "-A")
    _git(repo, "commit", "-qm", "base")
    return repo


def test_clean_repo_has_no_activity(tmp_path):
    repo = _init_repo(tmp_path)
    assert _repo_activity_mtime(str(repo)) == 0.0


def test_new_untracked_file_is_detected_as_activity(tmp_path):
    repo = _init_repo(tmp_path)
    assert _repo_activity_mtime(str(repo)) == 0.0
    # Simulate an agent writing a new source file with no stdout.
    (repo / "agent_wrote_this.py").write_text("y = 2\n")
    assert _repo_activity_mtime(str(repo)) > 0.0, "untracked file write must register as activity"


def test_activity_mtime_advances_on_further_writes(tmp_path):
    repo = _init_repo(tmp_path)
    (repo / "first.py").write_text("a = 1\n")
    first = _repo_activity_mtime(str(repo))
    assert first > 0.0
    time.sleep(0.05)
    # A subsequent write (modify tracked or add another) must advance the signal so the
    # watchdog keeps resetting its no-output timer while the agent keeps working.
    (repo / "base.py").write_text("x = 99\n")
    second = _repo_activity_mtime(str(repo))
    assert second >= first


def test_rename_entry_stats_destination(tmp_path):
    # Codex #134 P2: a rename (R "old -> new") must stat the DESTINATION so a silent
    # agent doing a rename refactor still registers as live.
    repo = _init_repo(tmp_path)
    (repo / "old_name.py").write_text("k = 1\n")
    _git(repo, "add", "-A")
    _git(repo, "commit", "-qm", "add old_name")
    _git(repo, "mv", "old_name.py", "new_name.py")  # staged rename -> "R  old -> new"
    # Sanity: porcelain shows the rename arrow.
    porc = _git(repo, "status", "--porcelain", "-uall").stdout
    assert "->" in porc
    assert _repo_activity_mtime(str(repo)) > 0.0, "rename destination must register as activity"


def test_bad_working_dir_returns_zero_not_raise(tmp_path):
    # Not a git repo / unreadable -> 0.0 (no false liveness, no crash in the monitor thread).
    assert _repo_activity_mtime(str(tmp_path / "does_not_exist")) == 0.0
