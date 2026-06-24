"""Audit [D] — inject the PM intelligence brief (SECTION 0) into agent prompts.

The brief tells agents what's already built (DO NOT REBUILD) + the existing src files;
it was built then DISCARDED. Injection is SAFE for the calibrated quality gates because
the brief carries NO `### Task N` markers and NO ``` code fences — so the validator's
task_count and PQ-6 (code-fences ÷ tasks) are unaffected; it only adds context.
"""
from __future__ import annotations

import inspect


def test_brief_carries_no_task_or_code_markers():
    # The crux of D's PQ-6-safety: prepending the brief must not change task_count
    # (re.findall r"^### Task \d+") or the code-fence count (```), so PQ-6 is unaffected.
    from automation.pm_intelligence import CycleBrief, ProjectSnapshot
    brief = CycleBrief(snapshot=ProjectSnapshot()).to_prompt_section()
    assert "SECTION 0" in brief, "it should render the PM intelligence brief"
    assert "### Task " not in brief, "brief must add NO tasks (would dilute PQ-6/task floor)"
    assert "```" not in brief, "brief must add NO code fences (would skew PQ-6 numerator)"


def test_validator_task_count_unchanged_by_brief():
    # Concretely: the validator's task counter sees the SAME count with/without the brief.
    import re

    from automation.pm_intelligence import CycleBrief, ProjectSnapshot
    brief = CycleBrief(snapshot=ProjectSnapshot()).to_prompt_section()
    body = "### Task 1: do x\n```bash\necho ok\n```\n### Task 2: do y\n```bash\necho ok\n```\n"
    pat = r"^### Task \d+"
    before = len(re.findall(pat, body, re.MULTILINE))
    after = len(re.findall(pat, brief + "\n" + body, re.MULTILINE))
    assert before == 2 and after == 2, "the brief must not add to the task count"
    # code-fence count likewise unchanged (brief contributes zero ```)
    assert brief.count("```") == 0


def test_brief_threaded_through_generator_and_caller():
    import automation.claude_prompt_creator as cpc
    h = inspect.getsource(cpc._generate_agent_prompt_hybrid)
    assert "brief_section" in h and "brief_section.rstrip()" in h, \
        "the hybrid producer must prepend brief_section to the scaffold head"
    c = inspect.getsource(cpc.create_agent_prompts_via_claude)
    assert "brief_section=brief_section" in c, \
        "create_agent_prompts_via_claude must thread brief_section into the hybrid call"
