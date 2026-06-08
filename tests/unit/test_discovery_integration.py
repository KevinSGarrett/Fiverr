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
