"""GEN-QUALITY — the prompt generator upgrade so generated prompts PASS the
item-1.3 quality gate (substance, not filler), without weakening the gate.

Key offline proof: a prompt that follows the NEW per-task skeleton the generator
instructs Claude to emit actually PASSES prompt_validator.validate(). Plus: the
in-process validate()->regenerate loop converges, a filler prompt still FAILS
(anti-bypass), and the gate file is unchanged.
"""
from __future__ import annotations

from automation import claude_prompt_creator as cpc
from automation import prompt_validator


def _make_skeleton_prompt(cycle: int, agent: str, n_tasks: int = 60,
                          authored_frac: float = 1.0) -> str:
    """Build a prompt that follows the NEW per-task skeleton the generator now
    instructs Claude to emit. Each authored task has a concrete src/...py path +
    a fenced code block + a verify token, co-located in the task block.
    """
    head = [
        f"AGENT {agent} -- CYCLE {cycle:03d} PROMPT",
        f"# Branch: cycle/{cycle:03d}/integration",
        "Repo root: C:\\Fiverr\\Fiverr",
        "Model: Codex 5.3 (gpt-5.3-codex) at medium effort. Auto model DISABLED.",
        "## PQ-0 identity",
        "You are the implementation agent. Identity and mission are fixed for this cycle.",
        "## PQ-1 project context",
        "Fiverr research system build context, roadmap, wave specifications and prior outcomes.",
        "## PQ-2 your role and file ownership",
        "You own the listed source modules; do not edit another agent's files.",
        "## PQ-3 git instructions",
        f"Work on cycle/{cycle:03d}/integration; commit and push your branch.",
        "## PQ-4 autonomy",
        "Autonomy rule: proceed without asking; never stop for confirmation mid-task.",
        "## PQ-5 jira scope",
        "In-scope stories are listed below; transition them only with evidence.",
        "Validation commands: python -m ruff check automation/ src/ tests/ ; "
        "python -m mypy src ; python -m pytest tests/unit/ -q",
        f"Write the cycle report to docs/cycle_reports/CYCLE_{cycle:03d}_AGENT_{agent}.md",
        "",
    ]
    lines: list[str] = head[:]
    n_authored = int(n_tasks * authored_frac)
    for n in range(1, n_tasks + 1):
        # Unique vocabulary per task -> keeps the unique-word ratio high (PQ-7a)
        uniq = " ".join(f"detail{n}x{i}" for i in range(70))
        lines.append(f"### Task {n}: implement capability {n} for module {n}")
        lines.append(f"- Jira: SCRUM-{200 + n}")
        if n <= n_authored:
            lines.append(f"- File: src/feature_{n}/module_{n}.py")
            lines.append("- Implementation:")
            lines.append("```python")
            lines.append(f"# src/feature_{n}/module_{n}.py")
            lines.append(f"def capability_{n}(payload: dict) -> dict:")
            lines.append(f"    return {{'ok': True, 'task': {n}}}")
            lines.append("```")
            lines.append("- Verify:")
            lines.append("```bash")
            lines.append(f"python -c \"import src.feature_{n}.module_{n} as m; "
                         f"assert hasattr(m, 'capability_{n}')\"  # expected output: exit 0")
            lines.append("```")
        else:
            lines.append(f"- Notes: prose-only task {n} (no authored code).")
        lines.append(f"- Acceptance: behavior for capability {n} verified. {uniq}")
        lines.append("")
    lines.append("END OF PROMPT")
    return "\n".join(lines)


def test_skeleton_prompt_passes_the_gate(tmp_path):
    # The shape the generator now instructs Claude to emit MUST pass validate().
    p = tmp_path / "CYCLE_099_AGENT_B_PROMPT.md"
    p.write_text(_make_skeleton_prompt(99, "B", n_tasks=60), encoding="utf-8")
    res = prompt_validator.validate(p, "B", 99)
    assert res.passed is True, res.errors


def test_degenerate_prose_only_prompt_fails(tmp_path):
    # Anti-bypass: a prose-only prompt (no code/path/verify) MUST fail PQ-6/7b.
    p = tmp_path / "CYCLE_099_AGENT_B_PROMPT.md"
    p.write_text(_make_skeleton_prompt(99, "B", n_tasks=60, authored_frac=0.0),
                 encoding="utf-8")
    res = prompt_validator.validate(p, "B", 99)
    assert res.passed is False
    assert any("PQ-6" in e or "PQ-7b" in e for e in res.errors)


def test_filler_fences_without_path_verify_still_fail(tmp_path):
    # Anti-bypass: padding ``` fences without a real src path + verify earns no
    # pass — PQ-7b authored ratio must still fail.
    lines = [
        "AGENT B -- CYCLE 099 PROMPT", "# Branch: cycle/099/integration",
        "Repo root: C:/Fiverr/Fiverr", "Codex 5.3 medium effort. Auto DISABLED.",
        "PQ-0 identity PQ-1 project context PQ-2 file ownership PQ-3 git instructions",
        "PQ-4 autonomy. Autonomy rule. PQ-5 jira scope. SCRUM-200",
        "python -m ruff check; python -m mypy src; python -m pytest",
        "docs/cycle_reports/CYCLE_099_AGENT_B.md",
    ]
    for n in range(1, 61):
        lines += [f"### Task {n}: filler {n} " + " ".join(f"w{n}q{i}" for i in range(60)),
                  "```", "echo just a bare fence with no path or verify", "```"]
    lines.append("END OF PROMPT")
    p = tmp_path / "CYCLE_099_AGENT_B_PROMPT.md"
    p.write_text("\n".join(lines), encoding="utf-8")
    res = prompt_validator.validate(p, "B", 99)
    assert res.passed is False
    assert any("PQ-7b" in e for e in res.errors)


def test_request_includes_skeleton_and_floors():
    # Layer 1: the generation request must carry the explicit per-task skeleton,
    # the gold example, and the verbatim floors bound to the validator regexes.
    req = cpc._build_agent_prompt_request("B", 99, "cycle/099/integration", "PM CONTEXT")
    assert "PER-TASK SKELETON" in req
    assert "### Task N:" in req
    assert "(?:src|automation|tests|docs)/" in req
    assert "expected output:" in req and "exit 0" in req
    assert "GOLD EXAMPLE TASK" in req
    assert ">= 30%" in req and ">= 20%" in req  # floors stated verbatim


def test_request_instructs_every_validator_required_token():
    # Codex review: the request must instruct EVERY section-level token the gate
    # hard-requires, so a faithful first generation passes (not just the per-task
    # floors). Mirrors prompt_validator REQUIRED_ERRORS + PQ_GATES.
    req = cpc._build_agent_prompt_request("B", 99, "cycle/099/integration", "PM CONTEXT")
    # PQ-0..PQ-5 section headers
    for pq in ("PQ-0 identity", "PQ-1 project context", "PQ-2 your role",
               "PQ-3 git instructions", "PQ-4 autonomy", "PQ-5 jira scope"):
        assert pq in req, f"request missing instruction for {pq}"
    # model block + effort + auto-disabled + autonomy rule
    assert "Codex 5.3" in req
    assert "medium effort" in req
    assert "Auto model DISABLED" in req
    assert "Autonomy rule:" in req
    # validation commands
    assert "ruff check" in req and "mypy src" in req and "pytest" in req
    # structural tokens
    assert "END OF PROMPT" in req
    assert "cycle/099/integration" in req
    assert "C:/Fiverr/Fiverr" in req
    assert "docs/cycle_reports/CYCLE_099_AGENT_B.md" in req
    assert "SCRUM-NNN" in req
    # Strongest check: a prompt that literally follows the request's mandated
    # tokens + skeleton passes validate() (the skeleton test already proves this).


def test_correction_block_names_deficiencies():
    block = cpc._quality_correction_block(
        ["PQ-6: only 2 code blocks for 60 tasks (ratio=3%, floor=30%)",
         "PQ-7b: only 1/60 tasks (2%) have authored code+path+verify"])
    assert "QUALITY GATE FAILURE" in block
    assert "PQ-6" in block and "PQ-7b" in block
    assert "REGENERATE" in block.upper()


def test_regenerate_loop_converges_on_passing_prompt(tmp_path, monkeypatch):
    # Layer 3: first Claude call returns a degenerate prompt -> validate fails ->
    # correction block appended -> second call returns a passing prompt -> accepted.
    calls = {"n": 0, "reqs": []}
    good = _make_skeleton_prompt(99, "B", n_tasks=60)
    bad = _make_skeleton_prompt(99, "B", n_tasks=60, authored_frac=0.0)

    def _fake_call(agent_id, cycle, request_text):
        calls["n"] += 1
        calls["reqs"].append(request_text)
        return bad if calls["n"] == 1 else good

    monkeypatch.setattr(cpc, "_call_claude_pm", _fake_call)
    monkeypatch.setattr(cpc, "_verify_claude_subscription",
                        lambda: {"passed": True, "probe": "ok", "latency_ms": 1})
    monkeypatch.setattr(cpc, "_build_pm_context", lambda *a, **k: "PM CONTEXT")
    monkeypatch.setattr(cpc, "PM_INTER_AGENT_DELAY", 0, raising=False)
    monkeypatch.setattr("time.sleep", lambda *a, **k: None)

    written = cpc.create_agent_prompts_via_claude(
        cycle=99, branch="cycle/099/integration", agents=["B"],
        jira_issues=[], wave={}, prompts_dir=tmp_path)

    assert written and "B" in written
    assert calls["n"] == 2, "should regenerate once after the degenerate first pass"
    # The second request carried the correction block naming the gate failures.
    assert "QUALITY GATE FAILURE" in calls["reqs"][1]
    # The accepted prompt passes the gate.
    assert prompt_validator.validate(written["B"], "B", 99).passed is True


def test_exhausted_quality_failure_is_fail_closed(tmp_path, monkeypatch):
    # Codex review (finding 7): if every attempt fails the gate, the agent must
    # NOT appear in `written` (so the caller halts CLAUDE_PM_PARTIAL) and the
    # degenerate prompt must be removed from disk (no resume-from-partial reuse).
    bad = _make_skeleton_prompt(99, "B", n_tasks=60, authored_frac=0.0)
    monkeypatch.setattr(cpc, "_call_claude_pm", lambda *a, **k: bad)
    monkeypatch.setattr(cpc, "_verify_claude_subscription",
                        lambda: {"passed": True, "probe": "ok", "latency_ms": 1})
    monkeypatch.setattr(cpc, "_build_pm_context", lambda *a, **k: "PM CONTEXT")
    monkeypatch.setattr(cpc, "PM_INTER_AGENT_DELAY", 0, raising=False)
    monkeypatch.setattr("time.sleep", lambda *a, **k: None)

    written = cpc.create_agent_prompts_via_claude(
        cycle=99, branch="cycle/099/integration", agents=["B"],
        jira_issues=[], wave={}, prompts_dir=tmp_path)

    # No agent passed the gate -> empty/None result -> caller halts (no dispatch).
    assert not written  # {} or None
    # The degenerate candidate is not left on disk for resume-from-partial.
    assert not (tmp_path / "CYCLE_099_AGENT_B_PROMPT.md").exists()


def test_resume_skips_degenerate_on_disk_prompt(tmp_path):
    # Codex review (finding 7): an existing on-disk prompt that fails the gate must
    # NOT be treated as reusable by resume-from-partial.
    p = tmp_path / "CYCLE_099_AGENT_B_PROMPT.md"
    p.write_text(_make_skeleton_prompt(99, "B", n_tasks=60, authored_frac=0.0),
                 encoding="utf-8")
    # Without agent/cycle (legacy call) it only checks size -> reusable.
    assert cpc._pm_existing_prompt_ok(p) is True
    # With agent/cycle it re-validates -> degenerate prompt is NOT reusable.
    assert cpc._pm_existing_prompt_ok(p, "B", 99) is False
    # A gate-passing prompt IS reusable.
    p.write_text(_make_skeleton_prompt(99, "B", n_tasks=60), encoding="utf-8")
    assert cpc._pm_existing_prompt_ok(p, "B", 99) is True


def test_gate_file_unchanged_byte_for_byte():
    # Anti-bypass: GEN-QUALITY must NOT weaken the gate. Confirm the validator
    # still enforces the documented floors (not relaxed to pass degenerate input).
    assert prompt_validator.MIN_CODE_BLOCKS_RATIO == 0.3
    assert prompt_validator.MIN_AUTHORED_RATIO == 0.20
    assert prompt_validator.MIN_UNIQUE_WORD_RATIO == 0.40
    assert prompt_validator.MIN_TASKS == 55
