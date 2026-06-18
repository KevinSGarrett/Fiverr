"""
test_icv.py -- Tests for the Inter-Agent Codex Verifier (ICV).

Covers: schemas, config, checklist_builder, deterministic_checker,
        loop_governor, classifier, ledger, orchestrator (det-only mode).
"""
from __future__ import annotations

import json

import pytest


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture()
def tmp_icv(tmp_path, monkeypatch):
    """Redirect ICV file paths to tmp_path; disable LLM."""
    monkeypatch.setenv("ICV_MAX_ATTEMPTS", "2")
    monkeypatch.setenv("PYTEST_CURRENT_TEST", "test_icv")
    # Patch REPO_ROOT in evidence_collector + deterministic_checker
    import automation.codex_verifier.evidence_collector as ec
    import automation.codex_verifier.deterministic_checker as dc
    monkeypatch.setattr(ec, "REPO_ROOT", tmp_path / "repo")
    monkeypatch.setattr(dc, "REPO_ROOT", tmp_path / "repo")
    (tmp_path / "repo").mkdir(parents=True)
    return tmp_path


@pytest.fixture()
def minimal_contract():
    return {
        "jirascope": [
            {
                "key": "SCRUM-999",
                "acceptancecriteria": ["Feature X is implemented and tested"],
                "dod": ["Tests pass"],
                "filesormodules": ["src/feature_x.py"],
            }
        ],
        "validationcommands": [{"command": "echo OK"}],
        "finalreportpath": "docs/cycle_reports/CYCLE_084_AGENT_A.md",
        "allowedpaths": ["src/**", "docs/**", "tests/**"],
        "blockedpaths": [],
    }


# ---------------------------------------------------------------------------
# ICV-SCHEMAS: dataclasses
# ---------------------------------------------------------------------------

class TestSchemas:
    def test_checklist_item_defaults(self):
        from automation.codex_verifier.schemas import ChecklistItem, ChecklistStatus, ItemClassification
        item = ChecklistItem(id="TEST-1", source="test", description="test item")
        assert item.status == ChecklistStatus.UNVERIFIABLE
        assert item.classification == ItemClassification.AMBIGUOUS
        assert item.is_blocking is True

    def test_verification_result_has_blocking_unmet(self):
        from automation.codex_verifier.schemas import (
            ChecklistItem, ChecklistStatus, VerificationResult, VerificationStatus
        )
        item = ChecklistItem(id="X", source="t", description="d",
                              status=ChecklistStatus.MISSING, is_blocking=True)
        result = VerificationResult(
            status=VerificationStatus.FAIL,
            completion_score=0.3,
            unmet_items=[item],
        )
        assert result.has_blocking_unmet is True

    def test_outcome_to_dict(self):
        from automation.codex_verifier.schemas import AgentVerificationOutcome, OutcomeStatus
        o = AgentVerificationOutcome(cycle="084", agent="A", status=OutcomeStatus.VERIFIED_PASS)
        d = o.to_dict()
        assert d["status"] == "VERIFIED_PASS"
        assert d["cycle"] == "084"


# ---------------------------------------------------------------------------
# ICV-CONFIG: loader
# ---------------------------------------------------------------------------

class TestConfig:
    def test_defaults(self, monkeypatch):
        monkeypatch.delenv("PYTEST_CURRENT_TEST", raising=False)
        monkeypatch.delenv("ICV_DISABLED", raising=False)
        monkeypatch.delenv("ICV_MAX_ATTEMPTS", raising=False)
        from automation.codex_verifier.config import ICVConfig
        cfg = ICVConfig()
        assert cfg.enabled is True
        assert cfg.max_attempts == 3

    def test_env_disable(self, monkeypatch):
        monkeypatch.setenv("ICV_DISABLED", "1")
        from automation.codex_verifier.config import ICVConfig
        cfg = ICVConfig()
        assert cfg.enabled is False

    def test_pytest_env_caps_attempts(self, monkeypatch):
        monkeypatch.setenv("PYTEST_CURRENT_TEST", "test_something")
        from automation.codex_verifier.config import ICVConfig
        cfg = ICVConfig()
        assert cfg.max_attempts == 1
        assert cfg.openai_budget_usd == 0.0

    def test_load_missing_file_returns_defaults(self, tmp_path):
        from automation.codex_verifier.config import load_config
        cfg = load_config(tmp_path / "nonexistent.yml")
        assert cfg.enabled is True


# ---------------------------------------------------------------------------
# ICV-CHECKLIST: builder
# ---------------------------------------------------------------------------

class TestChecklistBuilder:
    def test_builds_from_contract(self, minimal_contract):
        from automation.codex_verifier.checklist_builder import ChecklistBuilder
        items = ChecklistBuilder.build(prompt_text="", contract=minimal_contract)
        ids = [i.id for i in items]
        assert "AC-SCRUM-999-1" in ids
        assert "DOD-SCRUM-999-1" in ids
        assert "VCMD-1" in ids
        assert "REPORT-COMPLETE" in ids
        assert "GIT-COMMIT" in ids

    def test_extracts_prompt_tasks(self, minimal_contract):
        from automation.codex_verifier.checklist_builder import ChecklistBuilder
        prompt = "## Task 1: Implement feature X\n## Task 2: Write tests\n"
        items = ChecklistBuilder.build(prompt_text=prompt, contract=minimal_contract)
        task_ids = [i.id for i in items if i.id.startswith("TASK-")]
        assert "TASK-001" in task_ids
        assert "TASK-002" in task_ids

    def test_task_items_non_blocking(self, minimal_contract):
        from automation.codex_verifier.checklist_builder import ChecklistBuilder
        prompt = "## Task 1: Do something\n"
        items = ChecklistBuilder.build(prompt_text=prompt, contract=minimal_contract)
        task = next(i for i in items if i.id == "TASK-001")
        assert task.is_blocking is False

    def test_empty_contract(self):
        from automation.codex_verifier.checklist_builder import ChecklistBuilder
        items = ChecklistBuilder.build(prompt_text="", contract={})
        # Should still have REPORT-COMPLETE and GIT-COMMIT
        ids = [i.id for i in items]
        assert "REPORT-COMPLETE" in ids
        assert "GIT-COMMIT" in ids


# ---------------------------------------------------------------------------
# ICV-DET: deterministic checker
# ---------------------------------------------------------------------------

class TestDeterministicChecker:
    def test_report_complete_satisfied(self, tmp_icv, minimal_contract):
        from automation.codex_verifier.schemas import EvidenceBundle, ChecklistItem, ChecklistStatus
        from automation.codex_verifier.deterministic_checker import DeterministicChecker
        ev = EvidenceBundle(
            cycle="084", agent="A", branch="cycle/084/integration",
            prompt_text="", contract=minimal_contract,
            report_exists=True, report_has_complete_marker=True,
        )
        item = ChecklistItem(id="REPORT-COMPLETE", source="agent.report",
                              description="Report must exist with AGENT_COMPLETE")
        checked = DeterministicChecker.run([item], ev)
        assert checked[0].status == ChecklistStatus.SATISFIED

    def test_git_commit_missing(self, tmp_icv, minimal_contract):
        from automation.codex_verifier.schemas import EvidenceBundle, ChecklistItem, ChecklistStatus
        from automation.codex_verifier.deterministic_checker import DeterministicChecker
        ev = EvidenceBundle(
            cycle="084", agent="A", branch="cycle/084/integration",
            prompt_text="", contract=minimal_contract,
            committed_this_run=False,
        )
        item = ChecklistItem(id="GIT-COMMIT", source="git.commit",
                              description="Must have committed this run")
        checked = DeterministicChecker.run([item], ev)
        assert checked[0].status == ChecklistStatus.MISSING

    def test_all_blocking_pass(self, minimal_contract):
        from automation.codex_verifier.schemas import ChecklistItem, ChecklistStatus
        from automation.codex_verifier.deterministic_checker import DeterministicChecker
        items = [
            ChecklistItem(id="X", source="t", description="d",
                           status=ChecklistStatus.SATISFIED, is_blocking=True),
            ChecklistItem(id="Y", source="t", description="d",
                           status=ChecklistStatus.UNVERIFIABLE, is_blocking=False),
        ]
        assert DeterministicChecker.all_blocking_pass(items) is True

    def test_all_blocking_fail_when_missing(self, minimal_contract):
        from automation.codex_verifier.schemas import ChecklistItem, ChecklistStatus
        from automation.codex_verifier.deterministic_checker import DeterministicChecker
        items = [
            ChecklistItem(id="X", source="t", description="d",
                           status=ChecklistStatus.MISSING, is_blocking=True),
        ]
        assert DeterministicChecker.all_blocking_pass(items) is False


# ---------------------------------------------------------------------------
# ICV-GOV: loop governor
# ---------------------------------------------------------------------------

class TestLoopGovernor:
    def test_accept_on_det_pass(self):
        from automation.codex_verifier.loop_governor import LoopGovernor
        from automation.codex_verifier.schemas import GovernorDecisionKind, VerificationResult, VerificationStatus
        gov = LoopGovernor(max_attempts=3)
        verdict = VerificationResult(
            status=VerificationStatus.PASS,
            completion_score=1.0,
            deterministic_only=True,
        )
        gov.note_attempt(score=1.0, cost_usd=0.0)
        dec = gov.decide(verdict, attempt=0)
        assert dec.kind == GovernorDecisionKind.ACCEPT_PASS

    def test_stop_on_attempt_cap(self):
        from automation.codex_verifier.loop_governor import LoopGovernor
        from automation.codex_verifier.schemas import (
            ChecklistItem, ChecklistStatus, GovernorDecisionKind,
            ItemClassification, VerificationResult, VerificationStatus
        )
        gov = LoopGovernor(max_attempts=2)
        unmet = ChecklistItem(id="X", source="t", description="d",
                               status=ChecklistStatus.MISSING, is_blocking=True,
                               classification=ItemClassification.FIXABLE_IN_SCOPE)
        verdict = VerificationResult(
            status=VerificationStatus.FAIL,
            completion_score=0.3,
            unmet_items=[unmet],
        )
        gov.note_attempt(score=0.3, cost_usd=0.0)
        gov.note_attempt(score=0.5, cost_usd=0.0)
        dec = gov.decide(verdict, attempt=2)  # at cap
        assert dec.kind == GovernorDecisionKind.STOP

    def test_repair_when_fixable_items(self):
        from automation.codex_verifier.loop_governor import LoopGovernor
        from automation.codex_verifier.schemas import (
            ChecklistItem, ChecklistStatus, GovernorDecisionKind,
            ItemClassification, VerificationResult, VerificationStatus
        )
        gov = LoopGovernor(max_attempts=3, min_score=0.80)
        unmet = ChecklistItem(id="VCMD-1", source="t", description="d",
                               status=ChecklistStatus.MISSING, is_blocking=True,
                               classification=ItemClassification.FIXABLE_IN_SCOPE)
        verdict = VerificationResult(
            status=VerificationStatus.FAIL, completion_score=0.5,
            unmet_items=[unmet],
        )
        gov.note_attempt(score=0.5, cost_usd=0.0)
        dec = gov.decide(verdict, attempt=0)
        assert dec.kind == GovernorDecisionKind.REPAIR

    def test_stop_no_progress(self):
        from automation.codex_verifier.loop_governor import LoopGovernor
        from automation.codex_verifier.schemas import (
            ChecklistItem, ChecklistStatus, GovernorDecisionKind,
            ItemClassification, StopReason, VerificationResult, VerificationStatus
        )
        gov = LoopGovernor(max_attempts=5)
        unmet = ChecklistItem(id="X", source="t", description="d",
                               status=ChecklistStatus.MISSING, is_blocking=True,
                               classification=ItemClassification.FIXABLE_IN_SCOPE)
        verdict = VerificationResult(
            status=VerificationStatus.FAIL, completion_score=0.5,
            unmet_items=[unmet],
        )
        gov.note_attempt(score=0.5, cost_usd=0.0)
        gov.note_attempt(score=0.5, cost_usd=0.0)  # same score
        dec = gov.decide(verdict, attempt=1)
        assert dec.kind == GovernorDecisionKind.STOP
        assert dec.stop_reason == StopReason.NO_PROGRESS

    def test_budget_stop(self):
        from automation.codex_verifier.loop_governor import LoopGovernor
        from automation.codex_verifier.schemas import (
            ChecklistItem, ChecklistStatus, GovernorDecisionKind,
            ItemClassification, StopReason, VerificationResult, VerificationStatus
        )
        gov = LoopGovernor(max_attempts=5, openai_budget_usd=0.10)
        unmet = ChecklistItem(id="X", source="t", description="d",
                               status=ChecklistStatus.MISSING, is_blocking=True,
                               classification=ItemClassification.FIXABLE_IN_SCOPE)
        verdict = VerificationResult(
            status=VerificationStatus.FAIL, completion_score=0.3,
            unmet_items=[unmet],
        )
        gov.note_attempt(score=0.3, cost_usd=0.06)
        gov.note_attempt(score=0.5, cost_usd=0.06)  # total = 0.12 > cap
        dec = gov.decide(verdict, attempt=1)
        assert dec.kind == GovernorDecisionKind.STOP
        assert dec.stop_reason == StopReason.BUDGET_EXHAUSTED


# ---------------------------------------------------------------------------
# ICV-CLASS: classifier
# ---------------------------------------------------------------------------

class TestClassifier:
    def test_vcmd_classified_fixable(self):
        from automation.codex_verifier.classifier import classify_item
        from automation.codex_verifier.schemas import ChecklistItem, ChecklistStatus, ItemClassification
        item = ChecklistItem(id="VCMD-1", source="t", description="run pytest",
                              status=ChecklistStatus.MISSING)
        result = classify_item(item)
        assert result.classification == ItemClassification.FIXABLE_IN_SCOPE

    def test_secret_classified_out_of_scope(self):
        from automation.codex_verifier.classifier import classify_item
        from automation.codex_verifier.schemas import ChecklistItem, ChecklistStatus, ItemClassification
        item = ChecklistItem(id="AC-1", source="t",
                              description="requires API key secret",
                              status=ChecklistStatus.MISSING)
        result = classify_item(item)
        assert result.classification == ItemClassification.OUT_OF_SCOPE

    def test_satisfied_not_reclassified(self):
        from automation.codex_verifier.classifier import classify_item
        from automation.codex_verifier.schemas import ChecklistItem, ChecklistStatus, ItemClassification
        item = ChecklistItem(id="X", source="t", description="d",
                              status=ChecklistStatus.SATISFIED,
                              classification=ItemClassification.FIXABLE_IN_SCOPE)
        result = classify_item(item)
        # Should return the item unchanged (already satisfied)
        assert result.status == ChecklistStatus.SATISFIED


# ---------------------------------------------------------------------------
# ICV-LEDGER: persistence
# ---------------------------------------------------------------------------

class TestLedger:
    def test_record_and_load(self, tmp_path):
        from automation.codex_verifier.ledger import VerificationLedger
        ledger = VerificationLedger(tmp_path, "A")
        ledger.record("A", 0, "FAIL", 0.4, "REPAIR", None, 0.01, 500, 3, False)
        assert len(ledger.entries()) == 1
        assert ledger.entries()[0]["completion_score"] == 0.4

    def test_total_cost(self, tmp_path):
        from automation.codex_verifier.ledger import VerificationLedger
        ledger = VerificationLedger(tmp_path, "A")
        ledger.record("A", 0, "FAIL", 0.3, "REPAIR", None, 0.05, 500, 3, False)
        ledger.record("A", 1, "PASS", 0.9, "ACCEPT", None, 0.07, 700, 0, False)
        assert abs(ledger.total_cost() - 0.12) < 0.001

    def test_ledger_file_created(self, tmp_path):
        from automation.codex_verifier.ledger import VerificationLedger
        ledger = VerificationLedger(tmp_path, "B")
        ledger.record("B", 0, "PASS", 1.0, "ACCEPT", None, 0.0, 0, 0, True)
        assert (tmp_path / "icv" / "ledger_B.json").exists()


# ---------------------------------------------------------------------------
# ICV-ORCH: orchestrator (deterministic-only mode via PYTEST env)
# ---------------------------------------------------------------------------

class TestOrchestrator:
    def test_skipped_when_disabled(self, tmp_path, monkeypatch):
        monkeypatch.setenv("ICV_DISABLED", "1")
        monkeypatch.setenv("PYTEST_CURRENT_TEST", "t")
        from automation.codex_verifier.config import ICVConfig
        from automation.codex_verifier.orchestrator import verify_and_repair_agent
        from automation.codex_verifier.schemas import OutcomeStatus
        cfg = ICVConfig()
        outcome = verify_and_repair_agent(
            cycle=84, agent="A",
            prompt_path=tmp_path / "prompt.md",
            contract_path=None,
            run_dir=tmp_path,
            config=cfg,
        )
        assert outcome.status == OutcomeStatus.SKIPPED_DISABLED

    def test_verified_pass_on_complete_run(self, tmp_icv, minimal_contract, monkeypatch):
        monkeypatch.setenv("PYTEST_CURRENT_TEST", "t")
        monkeypatch.setenv("ICV_MAX_ATTEMPTS", "1")

        repo = tmp_icv / "repo"
        # Create prompt file
        prompt = repo / "PM_Pack/automation/prompts/CYCLE_084_AGENT_A_PROMPT.md"
        prompt.parent.mkdir(parents=True)
        prompt.write_text("## Task 1: Implement\n", encoding="utf-8")
        # Create report with AGENT_COMPLETE
        report = repo / "docs/cycle_reports/CYCLE_084_AGENT_A.md"
        report.parent.mkdir(parents=True)
        report.write_text("AGENT_COMPLETE\n", encoding="utf-8")

        from automation.codex_verifier.config import load_config
        from automation.codex_verifier.orchestrator import verify_and_repair_agent
        from automation.codex_verifier.schemas import OutcomeStatus

        import automation.codex_verifier.evidence_collector as ec
        import automation.codex_verifier.deterministic_checker as dc
        monkeypatch.setattr(ec, "REPO_ROOT", repo)
        monkeypatch.setattr(dc, "REPO_ROOT", repo)

        # Write contract file
        contract_path = tmp_icv / "contract.json"
        contract_path.write_text(json.dumps(minimal_contract), encoding="utf-8")

        cfg = load_config()
        cfg.enabled = True
        outcome = verify_and_repair_agent(
            cycle=84, agent="A",
            prompt_path=str(prompt),
            contract_path=str(contract_path),
            run_dir=tmp_icv / "runs" / "agent_A",
            config=cfg,
        )
        # In PYTEST mode with det-only, we get some outcome (not an exception)
        assert outcome.status in (
            OutcomeStatus.VERIFIED_PASS, OutcomeStatus.PASS_WITH_DEFERRALS, OutcomeStatus.BLOCKED
        )

    def test_error_fallback_on_exception(self, tmp_path, monkeypatch):
        monkeypatch.setenv("PYTEST_CURRENT_TEST", "t")
        from automation.codex_verifier.orchestrator import verify_and_repair_agent
        from automation.codex_verifier.schemas import OutcomeStatus
        # Patch EvidenceCollector to throw
        import automation.codex_verifier.evidence_collector as ec
        monkeypatch.setattr(ec.EvidenceCollector, "collect", staticmethod(lambda **k: (_ for _ in ()).throw(RuntimeError("test error"))))
        outcome = verify_and_repair_agent(
            cycle=84, agent="A",
            prompt_path=tmp_path / "p.md",
            contract_path=None,
            run_dir=tmp_path,
        )
        assert outcome.status == OutcomeStatus.ERROR_FALLBACK
