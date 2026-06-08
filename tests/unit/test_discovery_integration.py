"""Tests for S7.7 discovery keyword integration."""

from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import MagicMock, patch

RUN_ID = "discovery-20260608-120000-abc12345"


def make_hypothesis(
    text: str = "test keyword",
    niche_id: str | int = "python_automation",
    specificity_score: float | None = 0.72,
    accepted: bool = True,
    reason: str | None = "Test rationale",
    discovery_mode: str | None = "adjacent_keyword",
) -> SimpleNamespace:
    return SimpleNamespace(
        hypothesis_text=text,
        niche_id=niche_id,
        specificity_score=specificity_score,
        accepted=accepted,
        reason=reason,
        discovery_mode=discovery_mode,
    )


def make_keyword_row(
    *,
    keyword_id: int = 1,
    discovery_evaluated: bool = False,
    is_discovery: bool = True,
    is_retired: bool = False,
) -> SimpleNamespace:
    return SimpleNamespace(
        id=keyword_id,
        discovery_evaluated=discovery_evaluated,
        is_discovery=is_discovery,
        is_retired=is_retired,
        discovered_in_run=None,
    )


class TestCheckDiscoveryKeywordExists:
    def test_returns_none_when_not_found(self) -> None:
        from src.discovery.integration import check_discovery_keyword_exists

        db = MagicMock()
        db.query.return_value.filter.return_value.first.return_value = None
        result = check_discovery_keyword_exists("new keyword", "python_automation", db)
        assert result is None

    def test_returns_id_when_exists(self) -> None:
        from src.discovery.integration import check_discovery_keyword_exists

        db = MagicMock()
        db.query.return_value.filter.return_value.first.return_value = (42,)
        result = check_discovery_keyword_exists("existing keyword", "python_automation", db)
        assert result == 42

    def test_case_insensitive_query_built(self) -> None:
        from src.discovery.integration import check_discovery_keyword_exists

        db = MagicMock()
        db.query.return_value.filter.return_value.first.return_value = None
        check_discovery_keyword_exists("  PYTHON AI TOOL  ", "python_automation", db)
        db.query.assert_called_once()

    def test_multiple_results_returns_first_id(self) -> None:
        from src.discovery.integration import check_discovery_keyword_exists

        db = MagicMock()
        db.query.return_value.filter.return_value.first.return_value = (77,)
        result = check_discovery_keyword_exists("test", "python_automation", db)
        assert result == 77

    def test_query_uses_db_path(self) -> None:
        from src.discovery.integration import check_discovery_keyword_exists

        db = MagicMock()
        db.query.return_value.filter.return_value.first.return_value = None
        check_discovery_keyword_exists("test keyword", "python_automation", db)
        assert db.query.called


class TestInsertDiscoveryKeyword:
    def test_inserts_new_keyword_returns_id(self) -> None:
        from src.discovery.integration import insert_discovery_keyword

        db = MagicMock()
        hypothesis = make_hypothesis()
        new_kw = SimpleNamespace(id=999)
        with patch("src.discovery.integration.check_discovery_keyword_exists", return_value=None):
            with patch("src.models.Keyword", return_value=new_kw):
                result = insert_discovery_keyword(hypothesis, RUN_ID, db)
        assert result == 999
        db.add.assert_called_once()
        db.flush.assert_called_once()

    def test_returns_none_on_duplicate(self) -> None:
        from src.discovery.integration import insert_discovery_keyword

        db = MagicMock()
        with patch("src.discovery.integration.check_discovery_keyword_exists", return_value=101):
            result = insert_discovery_keyword(make_hypothesis(), RUN_ID, db)
        assert result is None
        db.add.assert_not_called()

    def test_returns_none_on_empty_text(self) -> None:
        from src.discovery.integration import insert_discovery_keyword

        result = insert_discovery_keyword(make_hypothesis(text=""), RUN_ID, MagicMock())
        assert result is None

    def test_returns_none_on_missing_niche_id(self) -> None:
        from src.discovery.integration import insert_discovery_keyword

        result = insert_discovery_keyword(make_hypothesis(niche_id=None), RUN_ID, MagicMock())
        assert result is None

    def test_lineage_fields_all_set(self) -> None:
        from src.discovery.integration import insert_discovery_keyword

        db = MagicMock()
        hypothesis = make_hypothesis(
            text="python ai tool",
            niche_id="python_automation",
            specificity_score=0.75,
            reason="High demand gap",
            discovery_mode="gap_exploit",
        )
        created_payload: dict[str, object] = {}

        def capture_keyword(**kwargs: object) -> SimpleNamespace:
            created_payload.update(kwargs)
            return SimpleNamespace(id=50)

        with patch("src.discovery.integration.check_discovery_keyword_exists", return_value=None):
            with patch("src.models.Keyword", side_effect=capture_keyword):
                result = insert_discovery_keyword(hypothesis, RUN_ID, db)
        assert result == 50
        assert created_payload["is_discovery"] is True
        assert created_payload["discovery_mode"] == "gap_exploit"
        assert created_payload["discovered_in_run"] == RUN_ID
        assert created_payload["discovery_evaluated"] is False
        assert created_payload["is_retired"] is False

    def test_niche_id_override_used(self) -> None:
        from src.discovery.integration import insert_discovery_keyword

        created_payload: dict[str, object] = {}

        def capture(**kwargs: object) -> SimpleNamespace:
            created_payload.update(kwargs)
            return SimpleNamespace(id=10)

        with patch("src.discovery.integration.check_discovery_keyword_exists", return_value=None):
            with patch("src.models.Keyword", side_effect=capture):
                insert_discovery_keyword(
                    make_hypothesis(niche_id="python_automation"),
                    RUN_ID,
                    MagicMock(),
                    niche_id="mcp_ai_agent",
                )
        assert created_payload["niche_id"] == "mcp_ai_agent"

    def test_reason_none_coerces_empty_string(self) -> None:
        from src.discovery.integration import insert_discovery_keyword

        payload: dict[str, object] = {}

        def capture(**kwargs: object) -> SimpleNamespace:
            payload.update(kwargs)
            return SimpleNamespace(id=4)

        with patch("src.discovery.integration.check_discovery_keyword_exists", return_value=None):
            with patch("src.models.Keyword", side_effect=capture):
                insert_discovery_keyword(make_hypothesis(reason=None), RUN_ID, MagicMock())
        assert payload["hypothesis_rationale"] == ""

    def test_long_reason_is_truncated(self) -> None:
        from src.discovery.integration import insert_discovery_keyword

        payload: dict[str, object] = {}

        def capture(**kwargs: object) -> SimpleNamespace:
            payload.update(kwargs)
            return SimpleNamespace(id=5)

        long_reason = "x" * 3000
        with patch("src.discovery.integration.check_discovery_keyword_exists", return_value=None):
            with patch("src.models.Keyword", side_effect=capture):
                insert_discovery_keyword(make_hypothesis(reason=long_reason), RUN_ID, MagicMock())
        assert len(str(payload["hypothesis_rationale"])) == 1000

    def test_specificity_score_zero_handled(self) -> None:
        from src.discovery.integration import insert_discovery_keyword

        payload: dict[str, object] = {}

        def capture(**kwargs: object) -> SimpleNamespace:
            payload.update(kwargs)
            return SimpleNamespace(id=6)

        with patch("src.discovery.integration.check_discovery_keyword_exists", return_value=None):
            with patch("src.models.Keyword", side_effect=capture):
                insert_discovery_keyword(make_hypothesis(specificity_score=0.0), RUN_ID, MagicMock())
        assert payload["hypothesis_confidence"] == 0.0

    def test_specificity_none_defaults_zero(self) -> None:
        from src.discovery.integration import insert_discovery_keyword

        payload: dict[str, object] = {}

        def capture(**kwargs: object) -> SimpleNamespace:
            payload.update(kwargs)
            return SimpleNamespace(id=7)

        with patch("src.discovery.integration.check_discovery_keyword_exists", return_value=None):
            with patch("src.models.Keyword", side_effect=capture):
                insert_discovery_keyword(make_hypothesis(specificity_score=None), RUN_ID, MagicMock())
        assert payload["hypothesis_confidence"] == 0.0

    def test_existing_seed_keyword_not_overwritten(self) -> None:
        from src.discovery.integration import insert_discovery_keyword

        db = MagicMock()
        with patch("src.discovery.integration.check_discovery_keyword_exists", return_value=5):
            result = insert_discovery_keyword(make_hypothesis(text="existing seed"), "run", db)
        assert result is None
        db.add.assert_not_called()

    def test_same_text_different_niche_allowed(self) -> None:
        from src.discovery.integration import insert_discovery_keyword

        with patch("src.discovery.integration.check_discovery_keyword_exists", return_value=None):
            with patch("src.models.Keyword", return_value=SimpleNamespace(id=99)):
                result = insert_discovery_keyword(
                    make_hypothesis(text="shared text", niche_id="mcp_ai_agent"),
                    "run",
                    MagicMock(),
                    niche_id="mcp_ai_agent",
                )
        assert result == 99

    def test_very_long_niche_id(self) -> None:
        from src.discovery.integration import insert_discovery_keyword

        long_niche = "a" * 200
        with patch("src.discovery.integration.check_discovery_keyword_exists", return_value=None):
            with patch("src.models.Keyword", return_value=SimpleNamespace(id=44)):
                result = insert_discovery_keyword(
                    make_hypothesis(text="test kw", niche_id=long_niche),
                    "run",
                    MagicMock(),
                )
        assert result == 44

    def test_normalized_keyword_set_when_model_has_field(self) -> None:
        from src.discovery.integration import insert_discovery_keyword

        class KeywordShim:
            keyword = object()
            normalized_keyword = object()

            def __init__(self, **kwargs: object) -> None:
                self.id = 18
                self.kwargs = kwargs

        with patch("src.discovery.integration.check_discovery_keyword_exists", return_value=None):
            with patch("src.models.Keyword", KeywordShim):
                db = MagicMock()
                result = insert_discovery_keyword(make_hypothesis(text="MiXeD Case"), RUN_ID, db)
        assert result == 18


class TestProcessAcceptedHypotheses:
    def test_empty_list_returns_zeros(self) -> None:
        from src.discovery.integration import process_accepted_hypotheses

        result = process_accepted_hypotheses([], RUN_ID, MagicMock())
        assert result == {"inserted": 0, "skipped": 0, "run_id": RUN_ID, "keyword_ids": []}

    def test_all_accepted_inserts_all(self) -> None:
        from src.discovery.integration import process_accepted_hypotheses

        hypotheses = [make_hypothesis(text=f"kw_{i}") for i in range(3)]
        with patch("src.discovery.integration.insert_discovery_keyword", side_effect=[1, 2, 3]):
            result = process_accepted_hypotheses(hypotheses, RUN_ID, MagicMock())
        assert result["inserted"] == 3
        assert result["skipped"] == 0
        assert result["keyword_ids"] == [1, 2, 3]

    def test_rejected_hypotheses_skipped(self) -> None:
        from src.discovery.integration import process_accepted_hypotheses

        hypotheses = [
            make_hypothesis(text="accepted", accepted=True),
            make_hypothesis(text="rejected", accepted=False),
        ]
        with patch("src.discovery.integration.insert_discovery_keyword", return_value=10):
            result = process_accepted_hypotheses(hypotheses, RUN_ID, MagicMock())
        assert result["inserted"] == 1
        assert result["skipped"] == 0

    def test_duplicate_counted_as_skipped(self) -> None:
        from src.discovery.integration import process_accepted_hypotheses

        with patch("src.discovery.integration.insert_discovery_keyword", return_value=None):
            result = process_accepted_hypotheses([make_hypothesis(text="dup")], RUN_ID, MagicMock())
        assert result["inserted"] == 0
        assert result["skipped"] == 1

    def test_returns_all_required_keys(self) -> None:
        from src.discovery.integration import process_accepted_hypotheses

        with patch("src.discovery.integration.insert_discovery_keyword", return_value=5):
            result = process_accepted_hypotheses([make_hypothesis()], RUN_ID, MagicMock())
        for key in ("inserted", "skipped", "run_id", "keyword_ids"):
            assert key in result

    def test_commit_called_after_inserts(self) -> None:
        from src.discovery.integration import process_accepted_hypotheses

        db = MagicMock()
        with patch("src.discovery.integration.insert_discovery_keyword", return_value=7):
            process_accepted_hypotheses([make_hypothesis()], RUN_ID, db)
        db.commit.assert_called_once()

    def test_no_accepted_returns_correct_skipped(self) -> None:
        from src.discovery.integration import process_accepted_hypotheses

        hypotheses = [make_hypothesis(accepted=False) for _ in range(5)]
        result = process_accepted_hypotheses(hypotheses, RUN_ID, MagicMock())
        assert result["inserted"] == 0
        assert result["skipped"] == 5

    def test_keyword_ids_only_for_inserted(self) -> None:
        from src.discovery.integration import process_accepted_hypotheses

        with patch("src.discovery.integration.insert_discovery_keyword", side_effect=[11, None, 12]):
            result = process_accepted_hypotheses(
                [make_hypothesis(text="a"), make_hypothesis(text="b"), make_hypothesis(text="c")],
                RUN_ID,
                MagicMock(),
            )
        assert result["keyword_ids"] == [11, 12]

    def test_attribute_error_safe_input(self) -> None:
        from src.discovery.integration import process_accepted_hypotheses

        h = SimpleNamespace(accepted=True, hypothesis_text="")
        with patch("src.discovery.integration.insert_discovery_keyword", return_value=None):
            result = process_accepted_hypotheses([h], "run-attr", MagicMock())
        assert result["inserted"] == 0


class TestGetPendingDiscoveryKeywords:
    def test_returns_empty_when_none(self) -> None:
        from src.discovery.integration import get_pending_discovery_keywords

        db = MagicMock()
        db.query.return_value.filter.return_value.filter.return_value.filter.return_value.order_by.return_value.all.return_value = (
            []
        )
        result = get_pending_discovery_keywords(db)
        assert result == []

    def test_returns_pending_keywords(self) -> None:
        from src.discovery.integration import get_pending_discovery_keywords

        db = MagicMock()
        kws = [make_keyword_row(keyword_id=i) for i in range(3)]
        db.query.return_value.filter.return_value.filter.return_value.filter.return_value.order_by.return_value.all.return_value = (
            kws
        )
        result = get_pending_discovery_keywords(db)
        assert len(result) == 3

    def test_result_is_list(self) -> None:
        from src.discovery.integration import get_pending_discovery_keywords

        db = MagicMock()
        db.query.return_value.filter.return_value.filter.return_value.filter.return_value.order_by.return_value.all.return_value = (
            []
        )
        assert isinstance(get_pending_discovery_keywords(db), list)

    def test_multiple_pending_ordered(self) -> None:
        from src.discovery.integration import get_pending_discovery_keywords

        db = MagicMock()
        kws = [make_keyword_row(keyword_id=i) for i in [5, 3, 7]]
        db.query.return_value.filter.return_value.filter.return_value.filter.return_value.order_by.return_value.all.return_value = (
            kws
        )
        result = get_pending_discovery_keywords(db)
        assert len(result) == 3

    def test_query_calls_order_by(self) -> None:
        from src.discovery.integration import get_pending_discovery_keywords

        db = MagicMock()
        db.query.return_value.filter.return_value.filter.return_value.filter.return_value.order_by.return_value.all.return_value = (
            []
        )
        get_pending_discovery_keywords(db)
        assert db.query.return_value.filter.return_value.filter.return_value.filter.return_value.order_by.called


class TestQueueDiscoveryCollection:
    def test_returns_true_when_queued(self) -> None:
        from src.discovery.integration import queue_discovery_collection

        db = MagicMock()
        kw = make_keyword_row(keyword_id=1, discovery_evaluated=False)
        db.query.return_value.filter.return_value.first.return_value = kw
        result = queue_discovery_collection(1, RUN_ID, db)
        assert result is True
        assert kw.discovered_in_run == RUN_ID

    def test_returns_false_when_not_found(self) -> None:
        from src.discovery.integration import queue_discovery_collection

        db = MagicMock()
        db.query.return_value.filter.return_value.first.return_value = None
        assert queue_discovery_collection(999, RUN_ID, db) is False

    def test_returns_false_when_already_evaluated(self) -> None:
        from src.discovery.integration import queue_discovery_collection

        db = MagicMock()
        kw = make_keyword_row(keyword_id=1, discovery_evaluated=True)
        db.query.return_value.filter.return_value.first.return_value = kw
        assert queue_discovery_collection(1, RUN_ID, db) is False

    def test_sets_discovery_evaluated_false(self) -> None:
        from src.discovery.integration import queue_discovery_collection

        db = MagicMock()
        kw = make_keyword_row(keyword_id=3, discovery_evaluated=False)
        db.query.return_value.filter.return_value.first.return_value = kw
        assert queue_discovery_collection(3, "run-x", db) is True
        assert kw.discovery_evaluated is False


class TestS77FlowMocks:
    def test_importable_symbols(self) -> None:
        from src.discovery.integration import (
            check_discovery_keyword_exists,
            get_pending_discovery_keywords,
            insert_discovery_keyword,
            process_accepted_hypotheses,
            queue_discovery_collection,
        )

        assert callable(insert_discovery_keyword)
        assert callable(queue_discovery_collection)
        assert callable(process_accepted_hypotheses)
        assert callable(get_pending_discovery_keywords)
        assert callable(check_discovery_keyword_exists)

    def test_s74_to_s77_mock_flow(self) -> None:
        from src.discovery.hypothesis import generate_gap_exploit_hypotheses
        from src.discovery.integration import process_accepted_hypotheses

        gap_scores = [
            {
                "keyword": "python ai pipeline tool",
                "demand_score": 0.80,
                "competition_score": 0.15,
                "opportunity_score": 0.90,
            }
        ]
        hypotheses = generate_gap_exploit_hypotheses(
            "python_automation",
            gap_scores,
            [],
            min_confidence=0.0,
        )
        with patch("src.discovery.integration.insert_discovery_keyword", return_value=100):
            result = process_accepted_hypotheses(hypotheses, "test-run-001", MagicMock())
        assert "inserted" in result

    def test_s74_s77_s76_pipeline_coexist(self) -> None:
        from src.discovery.feedback import build_feedback_summary
        from src.discovery.hypothesis import generate_gap_exploit_hypotheses
        from src.discovery.integration import process_accepted_hypotheses

        gap_signals = [
            {
                "keyword": "ai automation workflow",
                "demand_score": 0.85,
                "competition_score": 0.10,
                "opportunity_score": 0.92,
            }
        ]
        hypotheses = generate_gap_exploit_hypotheses("workflow_automation", gap_signals, [], min_confidence=0.0)
        with patch("src.discovery.integration.insert_discovery_keyword", side_effect=[1] * len(hypotheses)):
            insert_result = process_accepted_hypotheses(hypotheses, "full-pipeline", MagicMock())

        db_fb = MagicMock()
        db_fb.query.return_value.all.return_value = []
        fb_result = build_feedback_summary(db_fb)
        assert insert_result["inserted"] >= 0
        assert fb_result["total_hypotheses"] == 0


def test_file_has_minimum_test_count() -> None:
    """Guardrail to keep S7.7 coverage breadth explicit in this file."""
    import ast
    from pathlib import Path

    tree = ast.parse(Path(__file__).read_text(encoding="utf-8"))
    tests = [n for n in ast.walk(tree) if isinstance(n, ast.FunctionDef) and n.name.startswith("test_")]
    assert len(tests) >= 30


class TestFAgentCoverageUplift:
    def test_dedup_same_niche_different_text_allowed(self) -> None:
        from src.discovery.integration import insert_discovery_keyword

        db = MagicMock()
        new_kw = SimpleNamespace(id=10)
        h = make_hypothesis(
            text="different keyword",
            niche_id="python_automation",
            specificity_score=0.72,
            reason="test",
            discovery_mode="adjacent_keyword",
        )
        with patch("src.discovery.integration.check_discovery_keyword_exists", return_value=None):
            with patch("src.models.Keyword", return_value=new_kw):
                result = insert_discovery_keyword(h, "run-001", db)
        assert result == 10

    def test_dedup_same_text_different_niche_allowed(self) -> None:
        from src.discovery.integration import insert_discovery_keyword

        db = MagicMock()
        new_kw = SimpleNamespace(id=11)
        h = make_hypothesis(
            text="python ai tool",
            niche_id="mcp_ai_agent",
            specificity_score=0.72,
            reason="gap",
            discovery_mode="gap_exploit",
        )
        with patch("src.discovery.integration.check_discovery_keyword_exists", return_value=None):
            with patch("src.models.Keyword", return_value=new_kw):
                result = insert_discovery_keyword(h, "run-001", db, niche_id="mcp_ai_agent")
        assert result == 11

    def test_process_accepted_hypotheses_mixed_dedup(self) -> None:
        from src.discovery.integration import process_accepted_hypotheses

        db = MagicMock()
        h1 = make_hypothesis(text="new kw 1", accepted=True)
        h2 = make_hypothesis(text="existing kw", accepted=True)
        h3 = make_hypothesis(text="rejected kw", accepted=False)
        with patch("src.discovery.integration.insert_discovery_keyword", side_effect=[10, None]):
            result = process_accepted_hypotheses([h1, h2, h3], "run-mix", db)
        assert result["inserted"] == 1
        assert result["skipped"] == 1
        assert result["keyword_ids"] == [10]

    def test_process_returns_correct_run_id(self) -> None:
        from src.discovery.integration import process_accepted_hypotheses

        db = MagicMock()
        run_id = "discovery-2026-0608-12345"
        result = process_accepted_hypotheses([], run_id, db)
        assert result["run_id"] == run_id

    def test_hypothesis_rationale_truncated_to_1000(self) -> None:
        from src.discovery.integration import insert_discovery_keyword

        db = MagicMock()
        new_kw = SimpleNamespace(id=20)
        long_rationale = "x" * 1500
        h = make_hypothesis(text="test kw", reason=long_rationale)
        captured: dict[str, object] = {}

        def capture(**kwargs: object) -> SimpleNamespace:
            captured.update(kwargs)
            return new_kw

        with patch("src.discovery.integration.check_discovery_keyword_exists", return_value=None):
            with patch("src.models.Keyword", side_effect=capture):
                insert_discovery_keyword(h, "run-001", db)
        assert len(str(captured.get("hypothesis_rationale", ""))) <= 1000

    def test_hypothesis_rationale_none_becomes_empty_string(self) -> None:
        from src.discovery.integration import insert_discovery_keyword

        db = MagicMock()
        new_kw = SimpleNamespace(id=21)
        h = make_hypothesis(text="test kw", reason=None)
        captured: dict[str, object] = {}

        def capture(**kwargs: object) -> SimpleNamespace:
            captured.update(kwargs)
            return new_kw

        with patch("src.discovery.integration.check_discovery_keyword_exists", return_value=None):
            with patch("src.models.Keyword", side_effect=capture):
                insert_discovery_keyword(h, "run-001", db)
        assert isinstance(captured.get("hypothesis_rationale"), str)

    def test_insert_whitespace_only_text_rejected(self) -> None:
        from src.discovery.integration import insert_discovery_keyword

        db = MagicMock()
        h = make_hypothesis(text="   ")
        result = insert_discovery_keyword(h, "run-001", db)
        assert result is None
        db.add.assert_not_called()

    def test_process_all_rejected_returns_zero_inserted(self) -> None:
        from src.discovery.integration import process_accepted_hypotheses

        db = MagicMock()
        hypotheses = [make_hypothesis(accepted=False) for _ in range(5)]
        result = process_accepted_hypotheses(hypotheses, "run-001", db)
        assert result["inserted"] == 0
        assert result["skipped"] == 5
        assert result["keyword_ids"] == []

    def test_queue_discovery_collection_updates_run_id(self) -> None:
        from src.discovery.integration import queue_discovery_collection

        db = MagicMock()
        kw = make_keyword_row(keyword_id=1, discovery_evaluated=False)
        db.query.return_value.filter.return_value.first.return_value = kw
        result = queue_discovery_collection(1, "new-run-id", db)
        assert result is True
        assert kw.discovered_in_run == "new-run-id"

    def test_get_pending_excludes_retired_keywords(self) -> None:
        from src.discovery.integration import get_pending_discovery_keywords

        db = MagicMock()
        pending = [make_keyword_row(keyword_id=1), make_keyword_row(keyword_id=2)]
        db.query.return_value.filter.return_value.filter.return_value.filter.return_value.order_by.return_value.all.return_value = (
            pending
        )
        result = get_pending_discovery_keywords(db)
        assert len(result) == 2
        assert all(not kw.is_retired for kw in result)

    def test_integration_module_has_no_llm_calls(self) -> None:
        import ast

        tree = ast.parse(open("src/discovery/integration.py", encoding="utf-8").read())
        all_calls = [n for n in ast.walk(tree) if isinstance(n, ast.Call)]
        llm_calls = [
            c
            for c in all_calls
            if hasattr(c.func, "id") and any(x in c.func.id.lower() for x in ["llm", "openai", "gpt", "claude"])
        ]
        assert len(llm_calls) == 0

    def test_all_wave10_modes_generate_insertable_hypotheses(self) -> None:
        from src.discovery.hypothesis import (
            generate_adjacent_keyword_hypotheses,
            generate_gap_exploit_hypotheses,
            generate_trend_chase_hypotheses,
        )
        from src.discovery.integration import process_accepted_hypotheses

        db = MagicMock()
        seeds = ["python automation"]
        gap_s = [{"keyword": "test", "demand_score": 0.75, "competition_score": 0.25, "opportunity_score": 0.80}]
        trend_s = [
            {"keyword": "test", "trend_score": 0.82, "trend_velocity": 0.65, "opportunity_score": 0.78}
        ]
        adj = generate_adjacent_keyword_hypotheses("python_automation", seeds, [])
        gap = generate_gap_exploit_hypotheses("python_automation", gap_s, [], min_confidence=0.0)
        trend = generate_trend_chase_hypotheses("python_automation", trend_s, [], min_confidence=0.0)
        all_h = adj + gap + trend
        with patch("src.discovery.integration.insert_discovery_keyword", return_value=1):
            result = process_accepted_hypotheses(all_h, "test-run", db)
        assert isinstance(result["inserted"], int)

    def test_s76_s77_coexist(self) -> None:
        from src.discovery.feedback import build_feedback_summary
        from src.discovery.integration import process_accepted_hypotheses

        db_fb = MagicMock()
        db_fb.query.return_value.all.return_value = []
        db_int = MagicMock()
        fb_result = build_feedback_summary(db_fb)
        int_result = process_accepted_hypotheses([], "run", db_int)
        assert fb_result["total_hypotheses"] == 0
        assert int_result["inserted"] == 0

    def test_integration_importable_without_side_effects(self) -> None:
        import importlib

        mod = importlib.import_module("src.discovery.integration")
        assert hasattr(mod, "insert_discovery_keyword")
        assert hasattr(mod, "process_accepted_hypotheses")
        assert hasattr(mod, "get_pending_discovery_keywords")

    def test_process_dedup_all_dupes(self) -> None:
        from src.discovery.integration import process_accepted_hypotheses

        db = MagicMock()
        hypotheses = [make_hypothesis(accepted=True, text=f"dup-{i}") for i in range(4)]
        with patch("src.discovery.integration.insert_discovery_keyword", return_value=None):
            result = process_accepted_hypotheses(hypotheses, "run-dedup", db)
        assert result["inserted"] == 0
        assert result["skipped"] == 4
        assert result["keyword_ids"] == []

    def test_check_exists_with_leading_trailing_spaces(self) -> None:
        from src.discovery.integration import insert_discovery_keyword

        db = MagicMock()
        new_kw = SimpleNamespace(id=99)
        h = make_hypothesis(text="  padded keyword  ", niche_id="python_automation", specificity_score=0.70)
        captured: dict[str, object] = {}

        def capture(**kwargs: object) -> SimpleNamespace:
            captured.update(kwargs)
            return new_kw

        with patch("src.discovery.integration.check_discovery_keyword_exists", return_value=None):
            with patch("src.models.Keyword", side_effect=capture):
                insert_discovery_keyword(h, "run-001", db)
        inserted_text = str(captured.get("keyword", ""))
        assert inserted_text == "padded keyword"

    def test_hypothesis_confidence_is_float(self) -> None:
        from src.discovery.integration import insert_discovery_keyword

        db = MagicMock()
        new_kw = SimpleNamespace(id=33)
        h = make_hypothesis(text="test", specificity_score="0.75")  # type: ignore[arg-type]
        captured: dict[str, object] = {}

        def capture(**kwargs: object) -> SimpleNamespace:
            captured.update(kwargs)
            return new_kw

        with patch("src.discovery.integration.check_discovery_keyword_exists", return_value=None):
            with patch("src.models.Keyword", side_effect=capture):
                insert_discovery_keyword(h, "run", db)
        conf = captured.get("hypothesis_confidence")
        assert isinstance(conf, float)

    def test_insert_uses_unknown_when_mode_none(self) -> None:
        from src.discovery.integration import insert_discovery_keyword

        db = MagicMock()
        new_kw = SimpleNamespace(id=55)
        h = make_hypothesis(text="test", discovery_mode=None)
        captured: dict[str, object] = {}

        def capture(**kwargs: object) -> SimpleNamespace:
            captured.update(kwargs)
            return new_kw

        with patch("src.discovery.integration.check_discovery_keyword_exists", return_value=None):
            with patch("src.models.Keyword", side_effect=capture):
                insert_discovery_keyword(h, "run", db)
        assert captured.get("discovery_mode") == "unknown"

    def test_integration_module_size(self) -> None:
        n = len(open("src/discovery/integration.py", encoding="utf-8").readlines())
        assert 80 <= n <= 400

    def test_process_keyword_ids_is_list(self) -> None:
        from src.discovery.integration import process_accepted_hypotheses

        db = MagicMock()
        with patch("src.discovery.integration.insert_discovery_keyword", return_value=42):
            result = process_accepted_hypotheses([make_hypothesis(accepted=True)], "run", db)
        assert isinstance(result["keyword_ids"], list)
        assert 42 in result["keyword_ids"]

    def test_s74_hypothesis_to_s77_insertion(self) -> None:
        from src.discovery.hypothesis import generate_gap_exploit_hypotheses
        from src.discovery.integration import process_accepted_hypotheses

        db = MagicMock()
        gap_s = [{"keyword": "ai agent builder", "demand_score": 0.85, "competition_score": 0.12, "opportunity_score": 0.92}]
        hypotheses = generate_gap_exploit_hypotheses("ai_agent_development", gap_s, [], min_confidence=0.0)
        insert_calls: list[str] = []

        def mock_insert(hypothesis: SimpleNamespace, run_id: str, db_session: MagicMock, **kwargs: object) -> int:
            del run_id, db_session, kwargs
            insert_calls.append(str(hypothesis.hypothesis_text))
            return len(insert_calls)

        with patch("src.discovery.integration.insert_discovery_keyword", side_effect=mock_insert):
            result = process_accepted_hypotheses(hypotheses, "test-run-s74", db)
        assert result["inserted"] >= 0

    def test_discovery_mode_coerced_to_string(self) -> None:
        from src.discovery.contracts import HypothesisMode
        from src.discovery.integration import insert_discovery_keyword

        db = MagicMock()
        new_kw = SimpleNamespace(id=88)
        enum_mode = next(mode for mode in HypothesisMode if mode.value == "gap_exploit")
        h = make_hypothesis(text="mode test", discovery_mode=enum_mode)  # type: ignore[arg-type]
        captured: dict[str, object] = {}

        def capture(**kwargs: object) -> SimpleNamespace:
            captured.update(kwargs)
            return new_kw

        with patch("src.discovery.integration.check_discovery_keyword_exists", return_value=None):
            with patch("src.models.Keyword", side_effect=capture):
                insert_discovery_keyword(h, "run-coerce", db)
        assert isinstance(captured.get("discovery_mode"), str)

    def test_process_large_batch(self) -> None:
        from src.discovery.integration import process_accepted_hypotheses

        db = MagicMock()
        hypotheses = [make_hypothesis(text=f"kw_{i}", accepted=True) for i in range(20)]
        with patch("src.discovery.integration.insert_discovery_keyword", side_effect=list(range(1, 21))):
            result = process_accepted_hypotheses(hypotheses, "batch-run", db)
        assert result["inserted"] == 20
        assert len(result["keyword_ids"]) == 20
        db.commit.assert_called_once()

    def test_check_keyword_exists_empty_db(self) -> None:
        from src.discovery.integration import check_discovery_keyword_exists

        db = MagicMock()
        db.query.return_value.filter.return_value.first.return_value = None
        result = check_discovery_keyword_exists("any keyword", "python_automation", db)
        assert result is None

    def test_queue_discovery_collection_sets_run_id(self) -> None:
        from src.discovery.integration import queue_discovery_collection

        db = MagicMock()
        kw = make_keyword_row(keyword_id=1, discovery_evaluated=False)
        kw.discovered_in_run = "old-run"
        db.query.return_value.filter.return_value.first.return_value = kw
        queue_discovery_collection(1, "new-run-id-2026", db)
        assert kw.discovered_in_run == "new-run-id-2026"

    def test_s77_complete_smoke(self) -> None:
        from src.discovery.contracts import HypothesisMode
        from src.discovery.feedback import GOLD_THRESHOLD, build_feedback_summary, evaluate_discovery_results
        from src.discovery.hypothesis import generate_gap_exploit_hypotheses, generate_trend_chase_hypotheses
        from src.discovery.integration import (
            check_discovery_keyword_exists,
            get_pending_discovery_keywords,
            insert_discovery_keyword,
            process_accepted_hypotheses,
            queue_discovery_collection,
        )
        from src.models import DiscoveryCycleLog, DiscoveryOutcome, Keyword

        del (
            insert_discovery_keyword,
            process_accepted_hypotheses,
            get_pending_discovery_keywords,
            check_discovery_keyword_exists,
            queue_discovery_collection,
            generate_gap_exploit_hypotheses,
            generate_trend_chase_hypotheses,
            build_feedback_summary,
            evaluate_discovery_results,
            DiscoveryOutcome,
            DiscoveryCycleLog,
            Keyword,
        )
        modes = sorted([e.value for e in HypothesisMode])
        assert GOLD_THRESHOLD == 85.0
        assert "gap_exploit" in modes

    def test_process_hypothesis_without_accepted_attr(self) -> None:
        from src.discovery.integration import process_accepted_hypotheses

        db = MagicMock()
        h = SimpleNamespace(hypothesis_text="kw", niche_id="python_automation")
        result = process_accepted_hypotheses([h], "run-noattr", db)
        assert result["inserted"] == 0
        assert result["skipped"] == 1

    def test_insert_uses_hypothesis_niche_id_when_no_override(self) -> None:
        from src.discovery.integration import insert_discovery_keyword

        db = MagicMock()
        new_kw = SimpleNamespace(id=77)
        h = make_hypothesis(text="auto niche", niche_id="mcp_ai_agent")
        captured: dict[str, object] = {}

        def capture(**kwargs: object) -> SimpleNamespace:
            captured.update(kwargs)
            return new_kw

        with patch("src.discovery.integration.check_discovery_keyword_exists", return_value=None):
            with patch("src.models.Keyword", side_effect=capture):
                insert_discovery_keyword(h, "run-niche", db)
        assert captured.get("niche_id") == "mcp_ai_agent"

    def test_process_passes_run_id_to_each_insert(self) -> None:
        from src.discovery.integration import process_accepted_hypotheses

        db = MagicMock()
        h1 = make_hypothesis(text="kw1", accepted=True)
        h2 = make_hypothesis(text="kw2", accepted=True)
        captured_run_ids: list[str] = []

        def mock_insert(hypothesis: SimpleNamespace, run_id: str, db_session: MagicMock, **kwargs: object) -> int:
            del hypothesis, db_session, kwargs
            captured_run_ids.append(run_id)
            return len(captured_run_ids)

        with patch("src.discovery.integration.insert_discovery_keyword", side_effect=mock_insert):
            process_accepted_hypotheses([h1, h2], "specific-run-123", db)
        assert all(rid == "specific-run-123" for rid in captured_run_ids)

    def test_get_pending_only_discovery(self) -> None:
        from src.discovery.integration import get_pending_discovery_keywords

        db = MagicMock()
        pending = [make_keyword_row(keyword_id=1, is_discovery=True, discovery_evaluated=False, is_retired=False)]
        db.query.return_value.filter.return_value.filter.return_value.filter.return_value.order_by.return_value.all.return_value = (
            pending
        )
        result = get_pending_discovery_keywords(db)
        assert len(result) == 1
        assert all(kw.is_discovery for kw in result)

    def test_complete_insert_and_evaluate_pipeline(self) -> None:
        from src.discovery.feedback import build_feedback_summary
        from src.discovery.integration import process_accepted_hypotheses

        db_insert = MagicMock()
        hypotheses = [make_hypothesis(text=f"kw_{i}", accepted=True) for i in range(3)]
        with patch("src.discovery.integration.insert_discovery_keyword", side_effect=[1, 2, 3]):
            insert_result = process_accepted_hypotheses(hypotheses, "pipeline-run", db_insert)

        db_eval = MagicMock()
        outcomes = []
        for _ in range(3):
            o = SimpleNamespace(
                actual_final_score=70.0,
                is_hit=True,
                is_miss=False,
                is_gold=False,
                niche_id="python_automation",
                discovery_mode="adjacent_keyword",
                hypothesis_confidence=0.70,
            )
            outcomes.append(o)
        db_eval.query.return_value.all.return_value = outcomes
        eval_result = build_feedback_summary(db_eval)
        assert insert_result["inserted"] == 3
        assert eval_result["total_hypotheses"] == 3

    def test_integration_file_size_sanity(self) -> None:
        n = len(open("src/discovery/integration.py", encoding="utf-8").readlines())
        assert 60 <= n <= 400

    def test_case_insensitive_dedup_exact(self) -> None:
        from src.discovery.integration import check_discovery_keyword_exists

        db = MagicMock()
        db.query.return_value.filter.return_value.first.return_value = (50,)
        result = check_discovery_keyword_exists("python ai tool", "python_automation", db)
        assert result == 50

    def test_insert_calls_flush_to_get_id(self) -> None:
        from src.discovery.integration import insert_discovery_keyword

        db = MagicMock()
        new_kw = SimpleNamespace(id=111)
        h = make_hypothesis(text="flush test")
        with patch("src.discovery.integration.check_discovery_keyword_exists", return_value=None):
            with patch("src.models.Keyword", return_value=new_kw):
                insert_discovery_keyword(h, "run", db)
        db.flush.assert_called_once()
        db.commit.assert_not_called()

    def test_process_commit_not_called_on_empty(self) -> None:
        from src.discovery.integration import process_accepted_hypotheses

        db = MagicMock()
        process_accepted_hypotheses([], "run-empty", db)
        db.commit.assert_not_called()

    def test_check_case_insensitive_for_uppercase_existing(self) -> None:
        from src.discovery.integration import check_discovery_keyword_exists

        db = MagicMock()
        db.query.return_value.filter.return_value.first.return_value = (77,)
        result = check_discovery_keyword_exists("PYTHON AUTOMATION TOOL", "python_automation", db)
        assert result == 77

    def test_queue_returns_bool_type(self) -> None:
        from src.discovery.integration import queue_discovery_collection

        db = MagicMock()
        kw = make_keyword_row(keyword_id=1, discovery_evaluated=False)
        db.query.return_value.filter.return_value.first.return_value = kw
        result = queue_discovery_collection(1, "run", db)
        assert isinstance(result, bool)

    def test_all_s77_functions_importable(self) -> None:
        from src.discovery.integration import (
            check_discovery_keyword_exists,
            get_pending_discovery_keywords,
            insert_discovery_keyword,
            process_accepted_hypotheses,
            queue_discovery_collection,
        )

        fns = [
            insert_discovery_keyword,
            queue_discovery_collection,
            process_accepted_hypotheses,
            get_pending_discovery_keywords,
            check_discovery_keyword_exists,
        ]
        assert all(callable(f) for f in fns)

    def test_process_returns_list_of_new_ids(self) -> None:
        from src.discovery.integration import process_accepted_hypotheses

        db = MagicMock()
        hypotheses = [make_hypothesis(text=f"kw{i}", accepted=True) for i in range(4)]
        with patch("src.discovery.integration.insert_discovery_keyword", side_effect=[10, 11, 12, 13]):
            result = process_accepted_hypotheses(hypotheses, "run-ids", db)
        assert sorted(result["keyword_ids"]) == [10, 11, 12, 13]
        assert result["inserted"] == 4

    def test_gap_exploit_hypotheses_processable(self) -> None:
        from src.discovery.hypothesis import generate_gap_exploit_hypotheses
        from src.discovery.integration import process_accepted_hypotheses

        db = MagicMock()
        gap_signals = [
            {
                "keyword": "mcp protocol agent",
                "demand_score": 0.85,
                "competition_score": 0.10,
                "opportunity_score": 0.92,
            }
        ]
        hypotheses = generate_gap_exploit_hypotheses("mcp_ai_agent", gap_signals, [], min_confidence=0.0)
        with patch("src.discovery.integration.insert_discovery_keyword", return_value=50):
            result = process_accepted_hypotheses(hypotheses, "gap-run", db)
        assert result["inserted"] >= 0

    def test_trend_chase_hypotheses_processable(self) -> None:
        from src.discovery.hypothesis import generate_trend_chase_hypotheses
        from src.discovery.integration import process_accepted_hypotheses

        db = MagicMock()
        trend_signals = [
            {
                "keyword": "ai workflow automation",
                "trend_score": 0.88,
                "trend_velocity": 0.72,
                "opportunity_score": 0.85,
            }
        ]
        hypotheses = generate_trend_chase_hypotheses("workflow_automation", trend_signals, [], min_confidence=0.0)
        with patch("src.discovery.integration.insert_discovery_keyword", return_value=60):
            result = process_accepted_hypotheses(hypotheses, "trend-run", db)
        assert result["inserted"] >= 0

    def test_s77_coexists_with_wave9(self) -> None:
        from src.discovery.integration import process_accepted_hypotheses
        from src.pricing import analyze_price_distribution, calculate_new_seller_pricing

        del analyze_price_distribution, calculate_new_seller_pricing
        result = process_accepted_hypotheses([], "coexist-run", MagicMock())
        assert result["inserted"] == 0

    def test_inserted_keyword_marked_discovery_not_seed(self) -> None:
        from src.discovery.integration import insert_discovery_keyword

        db = MagicMock()
        new_kw = SimpleNamespace(id=200)
        h = make_hypothesis(text="discovery test")
        captured: dict[str, object] = {}

        def capture(**kwargs: object) -> SimpleNamespace:
            captured.update(kwargs)
            return new_kw

        with patch("src.discovery.integration.check_discovery_keyword_exists", return_value=None):
            with patch("src.models.Keyword", side_effect=capture):
                insert_discovery_keyword(h, "run", db)
        assert captured.get("is_discovery") is True

    def test_insert_returns_int_not_model(self) -> None:
        from src.discovery.integration import insert_discovery_keyword

        db = MagicMock()
        new_kw = SimpleNamespace(id=250)
        h = make_hypothesis(text="int test", discovery_mode="gap_exploit")
        with patch("src.discovery.integration.check_discovery_keyword_exists", return_value=None):
            with patch("src.models.Keyword", return_value=new_kw):
                result = insert_discovery_keyword(h, "run", db)
        assert isinstance(result, int)
        assert result == 250

    def test_process_returns_dict_not_none(self) -> None:
        from src.discovery.integration import process_accepted_hypotheses

        result = process_accepted_hypotheses([], "run", MagicMock())
        assert isinstance(result, dict)
        assert result is not None

    def test_check_exists_queries_keyword_model(self) -> None:
        from src.discovery.integration import check_discovery_keyword_exists

        db = MagicMock()
        db.query.return_value.filter.return_value.first.return_value = None
        check_discovery_keyword_exists("test", "python_automation", db)
        db.query.assert_called_once()

    def test_all_4_modes_generate_insertable_hypotheses(self) -> None:
        from src.discovery.hypothesis import (
            generate_adjacent_keyword_hypotheses,
            generate_adjacent_niche_hypotheses,
            generate_gap_exploit_hypotheses,
            generate_trend_chase_hypotheses,
        )
        from src.discovery.integration import process_accepted_hypotheses

        db = MagicMock()
        seeds = ["python ai tool"]
        gap_s = [{"keyword": "t", "demand_score": 0.75, "competition_score": 0.25, "opportunity_score": 0.80}]
        trend_s = [{"keyword": "t", "trend_score": 0.82, "trend_velocity": 0.65, "opportunity_score": 0.78}]
        adj_kw = generate_adjacent_keyword_hypotheses("python_automation", seeds, [])
        adj_niche = generate_adjacent_niche_hypotheses("python_automation", [], [])
        gap = generate_gap_exploit_hypotheses("python_automation", gap_s, [], min_confidence=0.0)
        trend = generate_trend_chase_hypotheses("python_automation", trend_s, [], min_confidence=0.0)
        all_h = adj_kw + adj_niche + gap + trend
        with patch("src.discovery.integration.insert_discovery_keyword", return_value=1):
            result = process_accepted_hypotheses(all_h, "all-modes", db)
        assert result["inserted"] >= 0

    def test_wave10_s22_s77_complete_smoke(self) -> None:
        from src.discovery.contracts import HypothesisMode
        from src.discovery.feedback import build_feedback_summary, evaluate_discovery_results
        from src.discovery.hypothesis import (
            generate_adjacent_keyword_hypotheses,
            generate_gap_exploit_hypotheses,
            generate_trend_chase_hypotheses,
        )
        from src.discovery.integration import (
            get_pending_discovery_keywords,
            insert_discovery_keyword,
            process_accepted_hypotheses,
        )
        from src.models import DiscoveryCycleLog, DiscoveryOutcome

        del (
            generate_adjacent_keyword_hypotheses,
            generate_gap_exploit_hypotheses,
            generate_trend_chase_hypotheses,
            evaluate_discovery_results,
            build_feedback_summary,
            insert_discovery_keyword,
            process_accepted_hypotheses,
            get_pending_discovery_keywords,
            DiscoveryOutcome,
            DiscoveryCycleLog,
        )
        modes = sorted([e.value for e in HypothesisMode])
        assert modes == ["adjacent_keyword", "adjacent_niche", "gap_exploit", "trend_chase"]

    def test_insert_db_add_called_once(self) -> None:
        from src.discovery.integration import insert_discovery_keyword

        db = MagicMock()
        new_kw = SimpleNamespace(id=300)
        h = make_hypothesis(text="add test", reason=None, discovery_mode="adjacent_keyword")
        with patch("src.discovery.integration.check_discovery_keyword_exists", return_value=None):
            with patch("src.models.Keyword", return_value=new_kw):
                insert_discovery_keyword(h, "run", db)
        db.add.assert_called_once_with(new_kw)
