"""GEN-QUALITY — the prompt generator produces prompts that PASS the item-1.3
quality gate with SUBSTANCE (real distinct code-bearing tasks), not filler, and
WITHOUT weakening the gate's anti-degenerate purpose.

2026-06-20 rework. The live milestone run exposed two real defects, fixed here:
  1. PQ-7a (unique-word ratio) was miscalibrated at 0.40 — empirically UNPASSABLE
     by any real prompt (the rigid 55-task code+path+verify skeleton + the 6000-word
     floor force structural repetition; whole-prompt unique ratio lands ~10% for
     genuinely distinct authored tasks, ~3-4% for verbatim recycling). The prior
     "passing" proof fabricated 4200 nonce tokens to clear 0.40 — exactly the
     antipattern the gate should reject. Recalibrated to 0.08, which separates
     recycling (≤4%) from distinct authored content (≥10%). These tests now use
     REALISTIC distinct prose (no nonce padding) and prove a realistic prompt passes.
  2. The single-shot generator could not reliably emit a 55-task fully-scaffolded
     prompt in one call (timeout/truncation/padding). The generator is now a HYBRID:
     a DETERMINISTIC scaffold (all fixed tokens + PQ-0..5 + END OF PROMPT) wraps
     Claude-authored task batches. These tests prove the assembled hybrid prompt
     passes the gate, and that recycled/degenerate batches still fail-closed.
"""
from __future__ import annotations

import os
import tempfile
from pathlib import Path

from automation import claude_prompt_creator as cpc
from automation import prompt_validator

# ── realistic, DISTINCT authored content (genuine variety, NOT nonce padding) ──
_VERBS = ("add wire implement harden extend refactor validate cache stream persist "
          "normalize backfill reconcile throttle paginate dedupe checkpoint snapshot "
          "annotate enrich").split()
_NOUNS = ("selector collector parser scheduler exporter ranker probe sink gate adapter "
          "resolver fetcher batcher emitter indexer sweeper monitor digest registry "
          "mapper").split()
_MODS = ("collection pipeline ranking storage reports dashboard signals ingest scoring "
         "audit retrieval enrichment dispatch telemetry budget reconcile catalog "
         "provenance evidence schema").split()
_ADJ = ("resilient idempotent incremental deterministic concurrent bounded transactional "
        "cached lazy strict tolerant atomic ordered windowed streaming partitioned").split()
_RAT = ("Handles malformed payloads without raising. "
        "Preserves ordering under concurrent writes. "
        "Avoids duplicate emission across retries. "
        "Bounds memory on large inputs. "
        "Recovers cleanly after a mid-run abort. "
        "Emits structured evidence for the cycle report. "
        "Skips rows already persisted this cycle. "
        "Surfaces a typed error on schema drift.").split(". ")


def _authored_task(n: int) -> str:
    """A DISTINCT, realistic, code+path+verify task block (no nonce padding)."""
    v = _VERBS[n % len(_VERBS)]
    no = _NOUNS[(n * 3) % len(_NOUNS)]
    mod = _MODS[(n * 7) % len(_MODS)]
    adj = _ADJ[(n * 5) % len(_ADJ)]
    rat = _RAT[n % len(_RAT)]
    rat2 = _RAT[(n * 2) % len(_RAT)]
    return (
        f"### Task {n}: {v.capitalize()} a {adj} {no} for the {mod} module (SCRUM-{200 + n})\n"
        f"- Jira: SCRUM-{200 + n}\n"
        f"- File: src/{mod}/{no}_{n}.py\n"
        f"- Implementation:\n"
        f"```python\n"
        f"# src/{mod}/{no}_{n}.py\n"
        f"def {v}_{no}_{n}(payload: dict, *, strict: bool = True) -> dict:\n"
        f"    \"\"\"{v.capitalize()} the {adj} {no}; {rat.lower()}.\"\"\"\n"
        f"    return {{'id': payload.get('id'), '{no}': payload.get('{no}'), '{mod}': True}}\n"
        f"```\n"
        f"- Verify:\n"
        f"```bash\n"
        f"python -c \"import src.{mod}.{no}_{n} as m; assert hasattr(m, '{v}_{no}_{n}')\"  "
        f"# expected output: exit 0\n"
        f"```\n"
        f"- Acceptance criteria: {rat} {rat2}\n"
        f"- DOD: implemented in src/{mod}/{no}_{n}.py; pytest for {mod} green; "
        f"SCRUM-{200 + n} updated with the commit SHA and evidence."
    )


def _prose_task(n: int) -> str:
    """A prose-only task (no code/path/verify) — degenerate by design."""
    return (
        f"### Task {n}: discuss capability {n} for module {n}\n"
        f"- Jira: SCRUM-{200 + n}\n"
        f"- Notes: {_RAT[n % len(_RAT)]} {_RAT[(n * 2) % len(_RAT)]} (no authored code)."
    )


def _make_skeleton_prompt(cycle: int, agent: str, n_tasks: int = 60,
                          authored_frac: float = 1.0) -> str:
    """Build a full prompt as the REAL hybrid generator does: the deterministic
    scaffold (cpc._build_scaffold_head/tail — all fixed tokens + PQ-0..5 + END OF
    PROMPT) wrapping the task bodies. Using the real scaffold keeps the fixture a
    faithful representation of generator output (vs a hand-rolled minimal head that
    under-represents real structural vocabulary). At authored_frac=1.0 it passes the
    recalibrated gate; at 0.0 it is a prose-only degenerate prompt that fails PQ-6/7b."""
    head = cpc._build_scaffold_head(agent, cycle, f"cycle/{cycle:03d}/integration",
                                    ["SCRUM-210", "SCRUM-211"])
    tail = cpc._build_scaffold_tail(agent, cycle)
    n_authored = int(n_tasks * authored_frac)
    body = [(_authored_task(n) if n <= n_authored else _prose_task(n))
            for n in range(1, n_tasks + 1)]
    return head + "\n" + "\n\n".join(body) + "\n" + tail


def _make_task_batch(start_n: int, count: int, *, recycled: bool = False) -> str:
    """Return ONLY task blocks (what Claude returns per hybrid batch). recycled=True
    repeats one body verbatim (the anti-paste adversary)."""
    if recycled:
        blocks = []
        for n in range(start_n, start_n + count):
            blocks.append(_authored_task(1).replace("Task 1", f"Task {n}"))
        return "\n\n".join(blocks)
    return "\n\n".join(_authored_task(n) for n in range(start_n, start_n + count))


# ── gate calibration ──────────────────────────────────────────────────────────

def test_pq7a_floor_is_recalibrated_value():
    # Guard against an accidental revert to the unpassable 0.40 floor.
    assert prompt_validator.MIN_UNIQUE_WORD_RATIO == 0.08


def test_primary_anti_degenerate_floors_unchanged():
    # Anti-bypass: the PRIMARY anti-degenerate gates (code ratio, authored ratio,
    # task floor, word floor) are NOT relaxed. Only PQ-7a was recalibrated.
    assert prompt_validator.MIN_CODE_BLOCKS_RATIO == 0.3
    assert prompt_validator.MIN_AUTHORED_RATIO == 0.20
    assert prompt_validator.MIN_TASKS == 55
    assert prompt_validator.MIN_WORD_COUNT == 6000


def test_pq7a_rejects_recycling_admits_distinct(tmp_path):
    # The recalibrated PQ-7a still fail-closed-rejects verbatim recycling while
    # admitting genuinely distinct authored content.
    distinct = _make_skeleton_prompt(99, "B", n_tasks=60)
    pd = tmp_path / "distinct.md"
    pd.write_text(distinct, encoding="utf-8")
    rd = prompt_validator.validate(pd, "B", 99)
    assert rd.passed is True, rd.errors
    assert not any("PQ-7a" in e for e in rd.errors)

    # Verbatim recycling (same authored body repeated 60x, inside the REAL scaffold)
    # -> unique ratio collapses below the floor even though each "task" has code.
    head = cpc._build_scaffold_head("B", 99, "cycle/099/integration",
                                    ["SCRUM-210", "SCRUM-211"])
    tail = cpc._build_scaffold_tail("B", 99)
    one = _authored_task(1)
    recycled = head + "\n" + "\n\n".join(
        one.replace("Task 1", f"Task {n}") for n in range(1, 61)) + "\n" + tail
    pr = tmp_path / "recycled.md"
    pr.write_text(recycled, encoding="utf-8")
    rr = prompt_validator.validate(pr, "B", 99)
    assert rr.passed is False
    assert any("PQ-7a" in e for e in rr.errors)


# ── the per-task skeleton ────────────────────────────────────────────────────

def test_skeleton_prompt_passes_the_gate(tmp_path):
    # A REALISTIC prompt (distinct authored tasks, no nonce padding) passes at the
    # recalibrated default thresholds.
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
    # Anti-bypass: padding ``` fences without a real src path + verify earns no pass.
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


# ── the legacy single-shot request builder (still used when GEN_HYBRID=False) ──

def test_request_includes_skeleton_and_floors():
    req = cpc._build_agent_prompt_request("B", 99, "cycle/099/integration", "PM CONTEXT")
    assert "PER-TASK SKELETON" in req
    assert "### Task N:" in req
    assert "(?:src|automation|tests|docs)/" in req
    assert "expected output:" in req and "exit 0" in req
    assert "GOLD EXAMPLE TASK" in req
    assert ">= 30%" in req and ">= 20%" in req


def test_request_instructs_every_validator_required_token():
    req = cpc._build_agent_prompt_request("B", 99, "cycle/099/integration", "PM CONTEXT")
    for pq in ("PQ-0 identity", "PQ-1 project context", "PQ-2 your role",
               "PQ-3 git instructions", "PQ-4 autonomy", "PQ-5 jira scope"):
        assert pq in req, f"request missing instruction for {pq}"
    assert "Codex 5.3" in req
    assert "medium effort" in req
    assert "Auto model DISABLED" in req
    assert "Autonomy rule:" in req
    assert "ruff check" in req and "mypy src" in req and "pytest" in req
    assert "END OF PROMPT" in req
    assert "cycle/099/integration" in req
    assert "C:/Fiverr/Fiverr" in req
    assert "docs/cycle_reports/CYCLE_099_AGENT_B.md" in req
    assert "SCRUM-NNN" in req


def test_correction_block_names_deficiencies():
    block = cpc._quality_correction_block(
        ["PQ-6: only 2 code blocks for 60 tasks (ratio=3%, floor=30%)",
         "PQ-7b: only 1/60 tasks (2%) have authored code+path+verify"])
    assert "QUALITY GATE FAILURE" in block
    assert "PQ-6" in block and "PQ-7b" in block
    assert "REGENERATE" in block.upper()


# ── HYBRID generation: deterministic scaffold + Claude-authored task batches ───

def test_scaffold_head_emits_all_required_tokens():
    head = cpc._build_scaffold_head("B", 83, "cycle/083/integration",
                                    ["SCRUM-210", "SCRUM-211"])
    tail = cpc._build_scaffold_tail("B", 83)
    blob = head + tail
    # Header / cycle / agent
    assert "AGENT B -- CYCLE 083 PROMPT" in head
    # model block + effort + auto/fallback disabled + autonomy rule
    assert "Codex 5.3" in head and "medium effort" in head
    assert "Auto model DISABLED" in head
    assert "Autonomy rule:" in head
    # PQ-0..5 section headers
    for pq in ("## PQ-0 identity", "## PQ-1 project context", "## PQ-2 your role",
               "## PQ-3 git instructions", "## PQ-4 autonomy", "## PQ-5 jira scope"):
        assert pq in head, f"scaffold missing {pq}"
    # structural tokens
    assert "C:/Fiverr/Fiverr" in head
    assert "cycle/083/integration" in head
    assert "SCRUM-210" in head
    # tail: validation commands + report path + END OF PROMPT exactly once
    assert "python -m ruff check" in tail
    assert "python -m mypy src" in tail
    assert "python -m pytest" in tail
    assert "docs/cycle_reports/CYCLE_083_AGENT_B.md" in tail
    assert blob.count("END OF PROMPT") == 1
    assert tail.rstrip().endswith("END OF PROMPT")


def test_extract_scrum_keys_handles_strings_and_dicts():
    # Accept both dict items ({"key": ...}) and bare-string items; ignore junk;
    # fall back to the pm_context regex, then to SCRUM-207, but never crash.
    keys = cpc._extract_scrum_keys(
        [{"key": "SCRUM-210"}, "SCRUM-211", 42, None, {"nope": 1}], "")
    assert keys == ["SCRUM-210", "SCRUM-211"]
    # context fallback when no structured keys
    assert cpc._extract_scrum_keys([], "see SCRUM-9 and SCRUM-9 again") == ["SCRUM-9"]
    # final fallback keeps the scaffold valid
    assert cpc._extract_scrum_keys(None, "") == ["SCRUM-207"]


def test_hybrid_budget_exhausted_returns_none(tmp_path, monkeypatch):
    # The aggregate wall-clock budget stops batching; with a 0s budget no batch runs
    # and the producer returns None (caller then halts — no degenerate dispatch).
    monkeypatch.setattr(cpc, "GEN_BATCH_BUDGET_S", 0, raising=False)
    called = {"n": 0}

    def _fake(agent_id, cycle, request_text, instruction=None):
        called["n"] += 1
        return _make_task_batch(1, 15)

    monkeypatch.setattr(cpc, "_call_claude_pm", _fake)
    out = cpc._generate_agent_prompt_hybrid(
        "B", 83, "cycle/083/integration", "PM CONTEXT SCRUM-210", [{"key": "SCRUM-210"}])
    assert out is None
    assert called["n"] == 0, "no batch should run once the budget is already spent"


def test_pm_context_embedded_and_sanitized():
    # Codex P2: the PM context must be embedded in the final prompt (PQ-1 points to
    # it), and embedding must not corrupt the validator's structural counts — a stray
    # "END OF PROMPT", "### Task N" heading, or [FILL] stub in the context is neutralized.
    ctx = ("Wave 11 roadmap. SCRUM-210 AC: behavior.\n"
           "### Task 3 leftover heading\n[FILL] placeholder\nEND OF PROMPT in notes\n")
    head = cpc._build_scaffold_head("B", 83, "cycle/083/integration",
                                    ["SCRUM-210"], pm_context=ctx)
    tail = cpc._build_scaffold_tail("B", 83)
    assert "## PM CONTEXT" in head
    assert "Wave 11 roadmap" in head            # real content preserved
    assert "END OF PROMPT" not in head          # neutralized in the embedded context
    assert "### Task 3 leftover" not in head     # heading demoted, won't inflate count
    assert "[FILL]" not in head                  # stub neutralized
    # A full assembled prompt with this context still passes the gate.
    body = "\n\n".join(_authored_task(n) for n in range(1, 61))
    full = head + "\n" + body + "\n" + tail
    fd, p = tempfile.mkstemp(suffix=".md")
    os.close(fd)
    Path(p).write_text(full, encoding="utf-8")
    res = prompt_validator.validate(p, "B", 83)
    assert res.passed is True, res.errors
    assert res.task_count == 60
    assert res.end_of_prompt_count == 1


def test_batch_request_includes_correction():
    # Codex P2: on a hybrid retry the exact validator errors are fed into the batch
    # request so Claude fixes them (convergence parity with the legacy path).
    lane = cpc._agent_lane_info("B")
    correction = cpc._quality_correction_block(
        ["PQ-7a: unique word ratio 5% < 8%", "Word floor violation: 4000 < 6000"])
    req = cpc._build_task_batch_request(
        "B", 83, lane, ["SCRUM-210"], 1, 15, "PM CTX", correction=correction)
    assert "QUALITY GATE FAILURE" in req
    assert "PQ-7a" in req
    # Without a correction the block is absent.
    req0 = cpc._build_task_batch_request("B", 83, lane, ["SCRUM-210"], 1, 15, "PM CTX")
    assert "QUALITY GATE FAILURE" not in req0


def test_renumber_tasks_sequential():
    raw = "### Task 4: alpha\nbody\n\n### Task 9: beta\nbody2\n\n### Task 2: gamma\nbody3"
    out, n = cpc._renumber_tasks(raw)
    assert n == 3
    assert "### Task 1: alpha" in out
    assert "### Task 2: beta" in out
    assert "### Task 3: gamma" in out


def _patch_common(monkeypatch):
    monkeypatch.setattr(cpc, "_verify_claude_subscription",
                        lambda: {"passed": True, "probe": "ok", "latency_ms": 1})
    monkeypatch.setattr(cpc, "_build_pm_context",
                        lambda *a, **k: "PM CONTEXT: SCRUM-210 SCRUM-211; src/ tree present.")
    monkeypatch.setattr(cpc, "PM_INTER_AGENT_DELAY", 0, raising=False)
    monkeypatch.setattr("time.sleep", lambda *a, **k: None)


def test_hybrid_assembly_passes_gate(tmp_path, monkeypatch):
    # Hybrid default path: Claude returns DISTINCT task batches -> the assembled
    # prompt (deterministic scaffold + batches) PASSES the gate at default thresholds.
    def _fake_batch(agent_id, cycle, request_text, instruction=None):
        import re
        m = re.search(r"### Task (\d+) through ### Task (\d+)", request_text)
        a, b = (int(m.group(1)), int(m.group(2))) if m else (1, 15)
        return _make_task_batch(a, b - a + 1)

    monkeypatch.setattr(cpc, "GEN_HYBRID", True, raising=False)
    monkeypatch.setattr(cpc, "_call_claude_pm", _fake_batch)
    _patch_common(monkeypatch)

    written = cpc.create_agent_prompts_via_claude(
        cycle=83, branch="cycle/083/integration", agents=["B"],
        jira_issues=[{"key": "SCRUM-210"}, {"key": "SCRUM-211"}],
        wave={}, prompts_dir=tmp_path)

    assert written and "B" in written
    res = prompt_validator.validate(written["B"], "B", 83)
    assert res.passed is True, res.errors
    assert res.task_count >= 55


def test_hybrid_recycled_batches_fail_closed(tmp_path, monkeypatch):
    # If Claude returns RECYCLED (verbatim-repeated) task bodies, the assembled
    # prompt fails the gate and the agent is NOT added to `written` (caller halts);
    # the degenerate candidate is removed from disk.
    def _fake_recycled(agent_id, cycle, request_text, instruction=None):
        import re
        m = re.search(r"### Task (\d+) through ### Task (\d+)", request_text)
        a, b = (int(m.group(1)), int(m.group(2))) if m else (1, 15)
        return _make_task_batch(a, b - a + 1, recycled=True)

    monkeypatch.setattr(cpc, "GEN_HYBRID", True, raising=False)
    monkeypatch.setattr(cpc, "_call_claude_pm", _fake_recycled)
    monkeypatch.setattr(cpc, "PM_MAX_ATTEMPTS", 2, raising=False)
    _patch_common(monkeypatch)

    written = cpc.create_agent_prompts_via_claude(
        cycle=83, branch="cycle/083/integration", agents=["B"],
        jira_issues=[{"key": "SCRUM-210"}], wave={}, prompts_dir=tmp_path)

    assert not written  # {} or None -> caller halts, no degenerate dispatch
    assert not (tmp_path / "CYCLE_083_AGENT_B_PROMPT.md").exists()


# ── legacy single-shot path (GEN_HYBRID=False) still works ────────────────────

def test_regenerate_loop_converges_on_passing_prompt(tmp_path, monkeypatch):
    # Legacy single-shot: first call returns degenerate -> correction block appended
    # -> second call returns a passing prompt -> accepted.
    calls = {"n": 0, "reqs": []}
    good = _make_skeleton_prompt(99, "B", n_tasks=60)
    bad = _make_skeleton_prompt(99, "B", n_tasks=60, authored_frac=0.0)

    def _fake_call(agent_id, cycle, request_text, instruction=None):
        calls["n"] += 1
        calls["reqs"].append(request_text)
        return bad if calls["n"] == 1 else good

    monkeypatch.setattr(cpc, "GEN_HYBRID", False, raising=False)
    monkeypatch.setattr(cpc, "_call_claude_pm", _fake_call)
    _patch_common(monkeypatch)

    written = cpc.create_agent_prompts_via_claude(
        cycle=99, branch="cycle/099/integration", agents=["B"],
        jira_issues=[], wave={}, prompts_dir=tmp_path)

    assert written and "B" in written
    assert calls["n"] == 2, "should regenerate once after the degenerate first pass"
    assert "QUALITY GATE FAILURE" in calls["reqs"][1]
    assert prompt_validator.validate(written["B"], "B", 99).passed is True


def test_exhausted_quality_failure_is_fail_closed(tmp_path, monkeypatch):
    # Legacy single-shot: if every attempt fails the gate, the agent must NOT appear
    # in `written` and the degenerate prompt must be removed from disk.
    bad = _make_skeleton_prompt(99, "B", n_tasks=60, authored_frac=0.0)
    monkeypatch.setattr(cpc, "GEN_HYBRID", False, raising=False)
    monkeypatch.setattr(cpc, "_call_claude_pm",
                        lambda *a, **k: bad)
    _patch_common(monkeypatch)

    written = cpc.create_agent_prompts_via_claude(
        cycle=99, branch="cycle/099/integration", agents=["B"],
        jira_issues=[], wave={}, prompts_dir=tmp_path)

    assert not written
    assert not (tmp_path / "CYCLE_099_AGENT_B_PROMPT.md").exists()


def test_resume_skips_degenerate_on_disk_prompt(tmp_path):
    # An existing on-disk prompt that fails the gate must NOT be reused by resume.
    p = tmp_path / "CYCLE_099_AGENT_B_PROMPT.md"
    p.write_text(_make_skeleton_prompt(99, "B", n_tasks=60, authored_frac=0.0),
                 encoding="utf-8")
    assert cpc._pm_existing_prompt_ok(p) is True               # legacy size-only
    assert cpc._pm_existing_prompt_ok(p, "B", 99) is False     # re-validates -> reject
    p.write_text(_make_skeleton_prompt(99, "B", n_tasks=60), encoding="utf-8")
    assert cpc._pm_existing_prompt_ok(p, "B", 99) is True      # passing -> reusable
