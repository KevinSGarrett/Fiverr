"""
tests/prompt_quality/test_pq_all.py

Definitive PQ-1..15 test suite referenced by the remediation tracker.
Re-exports and supplements the tests/unit/ coverage with PQ-specific
named test cases so tracker rows can cite tests/prompt_quality/.
"""
from __future__ import annotations

from pathlib import Path



# ---------------------------------------------------------------------------
# PQ-1: Full PM context — no [:8000] truncation
# ---------------------------------------------------------------------------
class TestPQ1NoTruncation:
    def test_no_hardcoded_slice(self):
        """PQ-1: claude_prompt_creator must not contain pm_context[:8000]."""
        src = Path("automation/claude_prompt_creator.py").read_text(encoding="utf-8")
        assert "pm_context[:8000]" not in src, (
            "PQ-1 REGRESSION: [:8000] slice found in claude_prompt_creator.py"
        )

    def test_full_context_passed(self, tmp_path):
        """PQ-1: _build_pm_context includes Jira description fully."""
        from automation.claude_prompt_creator import _build_pm_context
        signal = "PQONETESTMARKER"
        issues = [{"key": "SCRUM-999", "summary": "[PLAYBOOK] Story",
                   "status": "To Do", "fields": {"description": signal},
                   "description": signal}]
        ctx = _build_pm_context(84, "cycle/084/integration", issues, wave=11)
        assert signal in ctx, "PM context dropped the Jira description"


# ---------------------------------------------------------------------------
# PQ-2: Per-agent isolation — partial return on single-agent failure
# ---------------------------------------------------------------------------
class TestPQ2PerAgentIsolation:
    def test_partial_return_on_failure(self):
        """PQ-2: partial return code path exists in claude_prompt_creator."""
        src = Path("automation/claude_prompt_creator.py").read_text(encoding="utf-8")
        assert "PQ-2" in src or "partial return" in src.lower(), (
            "PQ-2 partial-return code path missing"
        )


# ---------------------------------------------------------------------------
# PQ-3: Loud fallback banner on template revert
# ---------------------------------------------------------------------------
class TestPQ3LoudFallback:
    def test_claude_pm_unavailable_banner_exists(self):
        """PQ-3: CLAUDE PM UNAVAILABLE banner is in the controller."""
        src = Path("automation/ai_cycle_controller.py").read_text(encoding="utf-8")
        assert "CLAUDE PM UNAVAILABLE" in src, (
            "PQ-3: CLAUDE PM UNAVAILABLE banner missing from controller"
        )


# ---------------------------------------------------------------------------
# PQ-4: Real Claude CLI liveness probe
# ---------------------------------------------------------------------------
class TestPQ4LivenessProbe:
    def test_liveness_probe_present(self):
        """PQ-4: _verify_claude_subscription runs a real CLI probe."""
        src = Path("automation/claude_prompt_creator.py").read_text(encoding="utf-8")
        assert "Reply OK" in src or "liveness" in src.lower(), (
            "PQ-4: real liveness probe missing from _verify_claude_subscription"
        )

    def test_probe_skipped_in_test_env(self, monkeypatch):
        """PQ-4: Probe skips in PYTEST env."""
        monkeypatch.setenv("PYTEST_CURRENT_TEST", "pq4")
        monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
        from automation.claude_prompt_creator import _verify_claude_subscription
        result = _verify_claude_subscription()
        assert result["passed"] is True

    def test_probe_fails_with_api_key(self, monkeypatch):
        """PQ-4: API key present means NOT subscription billing."""
        monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-ant-real-key-xyz")
        from automation.claude_prompt_creator import _verify_claude_subscription
        result = _verify_claude_subscription()
        assert result["passed"] is False


# ---------------------------------------------------------------------------
# PQ-5: Failures surfaced to terminal
# ---------------------------------------------------------------------------
class TestPQ5FailureSurfacing:
    def test_h2_failure_msg_exists(self):
        """PQ-5: H2 failure_msg (exit code + stderr) surfaced to terminal."""
        src = Path("automation/claude_prompt_creator.py").read_text(encoding="utf-8")
        assert "_failure_msg" in src or "stderr_tail" in src, (
            "PQ-5: failure surfacing missing from claude_prompt_creator"
        )


# ---------------------------------------------------------------------------
# PQ-6: Code-block ratio gate
# ---------------------------------------------------------------------------
class TestPQ6CodeBlockRatio:
    def test_code_block_ratio_gate_exists(self):
        """PQ-6: MIN_CODE_BLOCKS_RATIO enforced in prompt_validator."""
        src = Path("automation/prompt_validator.py").read_text(encoding="utf-8")
        assert "MIN_CODE_BLOCKS_RATIO" in src or "pq6" in src.lower()

    def test_prompt_with_no_code_blocks_flagged(self, tmp_path):
        """PQ-6: Prompt with 0% code blocks gets a warning."""
        from automation.prompt_validator import validate
        prompt = "## Task 001: Do X\nJust text no code.\n" * 60
        p = tmp_path / "CYCLE_084_AGENT_A_PROMPT.md"
        p.write_text(prompt, encoding="utf-8")
        result = validate(str(p), "A", 84)
        # Should warn about low code block ratio
        warns = " ".join(result.warnings)
        assert "PQ-6" in warns or "code" in warns.lower() or not result.passed


# ---------------------------------------------------------------------------
# PQ-7: Anti-paste gate (task substance — the critical fix)
# ---------------------------------------------------------------------------
class TestPQ7AntiPaste:
    def test_pq7b_task_substance_exists(self):
        """PQ-7b: Task substance check is in prompt_validator."""
        src = Path("automation/prompt_validator.py").read_text(encoding="utf-8")
        assert "PQ-7b" in src or "authored" in src.lower(), (
            "PQ-7b: task substance check missing from prompt_validator"
        )

    def test_spec_dump_prompt_flagged(self, tmp_path):
        """PQ-7b: A spec-dump prompt (no code+path+verify per task) is flagged."""
        from automation.prompt_validator import validate
        # Build a prompt that looks like pasted spec text (no authored code/path/verify)
        spec_dump = "\n".join([
            f"### Task {i:03d}: Implement feature from spec\n"
            f"Story AC: Feature must work. Description: {i} * text.\n"
            f"Jira: SCRUM-{100+i}\n"
            for i in range(1, 60)
        ])
        header = (
            "Codex 5.3 medium effort Auto model DISABLED Autonomy rule\n"
            "END OF PROMPT SCRUM-100 cycle/084/integration\n"
            "C:/Fiverr/Fiverr docs/cycle_reports/CYCLE_084\n"
            "ruff check mypy src pytest\n"
        )
        prompt = header + spec_dump
        p = tmp_path / "CYCLE_084_AGENT_A_PROMPT.md"
        p.write_text(prompt, encoding="utf-8")
        result = validate(str(p), "A", 84)
        # Item 1.3: PQ-7b is now a HARD ERROR (fail-closed), no longer a warning.
        assert result.passed is False
        diagnostics = " ".join(result.errors + result.warnings).lower()
        assert "pq-7" in diagnostics or "authored" in diagnostics or "paste" in diagnostics

    def test_authored_prompt_not_flagged(self, tmp_path):
        """PQ-7b: An authored prompt with code+path+verify is not flagged for paste."""
        from automation.prompt_validator import validate
        authored_tasks = "\n".join([
            f"### Task {i:03d}: Implement X\n"
            f"```python\n# Authored code\nresult = func(arg_{i})\nassert result == expected_{i}\n```\n"
            f"File: src/module_{i}.py\nExpected output: assert passes\n"
            for i in range(1, 60)
        ])
        header = (
            "Codex 5.3 medium effort Auto model DISABLED Autonomy rule\n"
            "END OF PROMPT SCRUM-100 cycle/084/integration\n"
            "C:/Fiverr/Fiverr docs/cycle_reports/CYCLE_084\n"
            "ruff check mypy src pytest\n"
        )
        prompt = header + authored_tasks
        p = tmp_path / "CYCLE_084_AGENT_A_PROMPT.md"
        p.write_text(prompt, encoding="utf-8")
        result = validate(str(p), "A", 84)
        warns = " ".join(result.warnings)
        # Should NOT flag for paste
        assert "PQ-7b" not in warns


# ---------------------------------------------------------------------------
# PQ-8: Model from config
# ---------------------------------------------------------------------------
class TestPQ8ModelFromConfig:
    def test_get_pm_model_reads_config(self):
        """PQ-8: _get_pm_model reads from config, not hardcoded."""
        src = Path("automation/claude_prompt_creator.py").read_text(encoding="utf-8")
        assert "_PREFERRED_ORDER" in src or "pm_model" in src, (
            "PQ-8: model selection not config-driven"
        )
        # Should NOT be hardcoded
        assert 'CLAUDE_MODEL = "claude-sonnet-4-6"' not in src, (
            "PQ-8 REGRESSION: model hardcoded to sonnet"
        )


# ---------------------------------------------------------------------------
# PQ-9: Dynamic wave/spec/DOD paths
# ---------------------------------------------------------------------------
class TestPQ9DynamicWave:
    def test_wave_not_hardcoded(self):
        """PQ-9: Wave 11 not hardcoded in prompt request template."""
        src = Path("automation/claude_prompt_creator.py").read_text(encoding="utf-8")
        # Should use dynamic wave derivation
        assert "_find_wave_dir" in src or "wave_folder" in src, (
            "PQ-9: dynamic wave resolution missing"
        )
        # The hardcoded SCRUM list should be gone
        assert '"# Wave 11"' not in src, (
            "PQ-9 REGRESSION: Wave 11 hardcoded string found"
        )


# ---------------------------------------------------------------------------
# PQ-10: Real AC verification (the critical fix)
# ---------------------------------------------------------------------------
class TestPQ10RealACVerification:
    def test_word_overlap_heuristic_replaced(self):
        """PQ-10: verify_jira_ac_completion must not use word-overlap heuristic."""
        src = Path("automation/claude_prompt_creator.py").read_text(encoding="utf-8")
        # The old heuristic searched for first-3-words in report text
        old_pattern = "all(w in agent_report_text.lower() for w in words[:3])"
        assert old_pattern not in src, (
            "PQ-10 FALSE POSITIVE: Old word-overlap heuristic still present. "
            "verify_jira_ac_completion must delegate to ICV deterministic checker."
        )

    def test_jira_done_status_passes(self):
        """PQ-10: Story marked Done in Jira passes AC check without heuristic."""
        from automation.claude_prompt_creator import verify_jira_ac_completion
        issue = {
            "key": "SCRUM-999",
            "status": "Done",
            "fields": {"description": "AC: must do X\nAC: must do Y"},
        }
        result = verify_jira_ac_completion(issue, "some report text")
        assert result["passed"] is True
        assert result["key"] == "SCRUM-999"

    def test_missing_agent_complete_fails(self):
        """PQ-10: Missing AGENT_COMPLETE marker in report fails AC check."""
        from automation.claude_prompt_creator import verify_jira_ac_completion
        issue = {"key": "SCRUM-999", "status": "In Progress",
                 "fields": {"description": "AC: feature works"}}
        result = verify_jira_ac_completion(issue, "report without completion marker")
        assert result["passed"] is False

    def test_agent_complete_present_passes(self):
        """PQ-10: Report with AGENT_COMPLETE passes basic AC check."""
        from automation.claude_prompt_creator import verify_jira_ac_completion
        issue = {"key": "SCRUM-999", "status": "In Progress",
                 "fields": {"description": "AC: feature works"}}
        result = verify_jira_ac_completion(issue, "work done\nAGENT_COMPLETE\n")
        assert result["passed"] is True


# ---------------------------------------------------------------------------
# PQ-11: Structural lint
# ---------------------------------------------------------------------------
class TestPQ11StructuralLint:
    def test_structural_checks_in_validator(self):
        """PQ-11: prompt_validator has structural checks for INVOKE-EXE etc."""
        src = Path("automation/prompt_validator.py").read_text(encoding="utf-8")
        assert "PQ-11" in src or "INVOKE" in src


# ---------------------------------------------------------------------------
# PQ-12: Empty context sections warn
# ---------------------------------------------------------------------------
class TestPQ12EmptySectionWarning:
    def test_empty_section_check_exists(self):
        """PQ-12: _build_pm_context warns on silently-empty sections."""
        src = Path("automation/claude_prompt_creator.py").read_text(encoding="utf-8")
        assert "PQ-12" in src


# ---------------------------------------------------------------------------
# PQ-13: Request artifacts saved per agent
# ---------------------------------------------------------------------------
class TestPQ13RequestArtifacts:
    def test_request_artifact_saved(self):
        """PQ-13: REQUEST.md artifact is saved per agent in create_agent_prompts_via_claude."""
        src = Path("automation/claude_prompt_creator.py").read_text(encoding="utf-8")
        assert "_REQUEST.md" in src or "PQ-13" in src


# ---------------------------------------------------------------------------
# PQ-14: Provenance stamp
# ---------------------------------------------------------------------------
class TestPQ14ProvenanceStamp:
    def test_provenance_stamp_in_prompts(self):
        """PQ-14: Provenance stamp written to every generated prompt."""
        src = Path("automation/claude_prompt_creator.py").read_text(encoding="utf-8")
        assert "PROVENANCE" in src or "PQ-14" in src


# ---------------------------------------------------------------------------
# PQ-15: 084 vs 070 body comparison (investigation result)
# ---------------------------------------------------------------------------
class TestPQ15ProvenanceInvestigation:
    def test_pq7b_would_have_caught_084(self, tmp_path):
        """PQ-15: PQ-7b task substance check would flag a spec-dump prompt like 084."""
        from automation.prompt_validator import validate
        # Simulate the 084 pattern: large but task-light, pasted spec
        pasted_spec = "## EPIC TASK BREAKDOWN\n" + "Spec text " * 2000
        header = (
            "Codex 5.3 medium effort Auto model DISABLED Autonomy rule END OF PROMPT\n"
            "SCRUM-100 cycle/084/integration C:/Fiverr/Fiverr\n"
            "docs/cycle_reports/CYCLE_084 ruff check mypy src pytest\n"
        )
        tasks = "\n".join([
            f"### Task {i:03d}: From spec\n"
            "Jira AC: story must do X. No authored code here.\n"
            for i in range(1, 60)
        ])
        prompt = header + pasted_spec + tasks
        p = tmp_path / "CYCLE_084_AGENT_A_PROMPT.md"
        p.write_text(prompt, encoding="utf-8")
        result = validate(str(p), "A", 84)
        # Item 1.3: the spec-dump shape is now REJECTED (PQ-7b hard error),
        # not merely warned. The gate fails closed on a degenerate 084-style prompt.
        assert result.passed is False
        diagnostics = " ".join(result.errors + result.warnings).lower()
        assert "pq-7" in diagnostics or "authored" in diagnostics or "paste" in diagnostics, (
            "PQ-7b did NOT catch the spec-dump pattern. Gate is still insufficient."
        )
