"""Smoke tests for scaffolded module stubs — SCRUM-273.

Covers contracts and orchestrator stubs for src/scoring/, src/pricing/,
src/discovery/, and collection_runtime models to ensure patch coverage
meets the 90% gate.
"""

from __future__ import annotations

from pathlib import Path

# ---------------------------------------------------------------------------
# src/scoring/ scaffold tests
# ---------------------------------------------------------------------------


class TestScoringScaffold:
    def test_imports(self) -> None:
        from src.scoring import ScoringInput, ScoringOrchestrator, ScoringOutput
        assert ScoringInput
        assert ScoringOrchestrator
        assert ScoringOutput

    def test_score_dimension_weighted_contribution(self) -> None:
        from src.scoring.contracts import ScoreDimension
        d = ScoreDimension(name="demand", value=0.8, weight=0.2)
        assert abs(d.weighted_contribution() - 0.16) < 1e-9

    def test_score_dimension_zero_weight(self) -> None:
        from src.scoring.contracts import ScoreDimension
        d = ScoreDimension(name="demand", value=1.0, weight=0.0)
        assert d.weighted_contribution() == 0.0

    def test_scoring_output_is_go(self) -> None:
        from src.scoring.contracts import ScoringOutput
        assert ScoringOutput(verdict="GO").is_go is True
        assert ScoringOutput(verdict="CONDITIONAL_GO").is_go is True
        assert ScoringOutput(verdict="NO_GO").is_go is False
        assert ScoringOutput(verdict="UNSCORED").is_go is False

    def test_orchestrator_score_stub(self) -> None:
        from src.scoring import ScoringInput, ScoringOrchestrator
        orch = ScoringOrchestrator()
        result = orch.score(ScoringInput(niche_id="test", run_id=1))
        assert result.verdict == "UNSCORED"
        assert result.composite_score == 0.0
        assert result.run_id == 1

    def test_orchestrator_score_batch(self) -> None:
        from src.scoring import ScoringInput, ScoringOrchestrator
        orch = ScoringOrchestrator()
        results = orch.score_batch([ScoringInput(niche_id="a"), ScoringInput(niche_id="b")])
        assert len(results) == 2
        assert all(r.verdict == "UNSCORED" for r in results)

    def test_orchestrator_compute_composite_empty(self) -> None:
        from src.scoring import ScoringOrchestrator
        orch = ScoringOrchestrator()
        assert orch._compute_composite([]) == 0.0

    def test_orchestrator_compute_composite_with_dimensions(self) -> None:
        from src.scoring import ScoringOrchestrator
        from src.scoring.contracts import ScoreDimension
        dims = [ScoreDimension("a", 0.8, 0.5), ScoreDimension("b", 0.6, 0.5)]
        orch = ScoringOrchestrator()
        result = orch._compute_composite(dims)
        assert 0.0 < result <= 1.0

    def test_orchestrator_compute_composite_zero_weights(self) -> None:
        from src.scoring import ScoringOrchestrator
        from src.scoring.contracts import ScoreDimension
        dims = [ScoreDimension("a", 1.0, 0.0)]
        orch = ScoringOrchestrator()
        assert orch._compute_composite(dims) == 0.0

    def test_custom_weights(self) -> None:
        from src.scoring import ScoringOrchestrator
        orch = ScoringOrchestrator(weights={"demand": 1.0})
        assert orch._weights["demand"] == 1.0


# ---------------------------------------------------------------------------
# src/pricing/ scaffold tests
# ---------------------------------------------------------------------------


class TestPricingScaffold:
    def test_imports(self) -> None:
        from src.pricing import (
            EntryPricingRecommendation,
            PriceDistribution,
            PricingInput,
            PricingOrchestrator,
            PricingOutput,
        )
        assert PricingOrchestrator
        assert PricingInput
        assert PricingOutput
        assert PriceDistribution
        assert EntryPricingRecommendation

    def test_analyze_stub(self) -> None:
        from src.pricing import PricingInput, PricingOrchestrator
        orch = PricingOrchestrator()
        out = orch.analyze(PricingInput(niche_id="prd_ai_saas", run_id=42))
        assert out.niche_id == "prd_ai_saas"
        assert out.run_id == 42
        assert out.entry_recommendation is None

    def test_compute_distribution_stub(self) -> None:
        from src.pricing import PricingOrchestrator
        orch = PricingOrchestrator()
        dist = orch.compute_distribution([50.0, 100.0, 200.0], "test_niche", "python automation")
        assert dist.sample_count == 3
        assert dist.niche_id == "test_niche"
        assert dist.raw_prices == [50.0, 100.0, 200.0]

    def test_compute_distribution_empty(self) -> None:
        from src.pricing import PricingOrchestrator
        orch = PricingOrchestrator()
        dist = orch.compute_distribution([], "niche", "kw")
        assert dist.sample_count == 0

    def test_recommend_entry_pricing_stub(self) -> None:
        from src.pricing import PriceDistribution, PricingOrchestrator
        orch = PricingOrchestrator()
        dist = PriceDistribution(niche_id="test", keyword="kw")
        rec = orch.recommend_entry_pricing(dist, 50.0, 125.0, 250.0)
        assert rec.basic_price == 50.0
        assert rec.standard_price == 125.0
        assert rec.premium_price == 250.0
        assert rec.confidence == 0.0


# ---------------------------------------------------------------------------
# src/discovery/ scaffold tests
# ---------------------------------------------------------------------------


class TestDiscoveryScaffold:
    def test_imports(self) -> None:
        from src.discovery import (
            DiscoveryHypothesisResult,
            DiscoveryInput,
            DiscoveryOrchestrator,
            DiscoveryOutput,
            HypothesisMode,
            HypothesisStatus,
        )
        assert DiscoveryOrchestrator
        assert DiscoveryInput
        assert DiscoveryOutput
        assert HypothesisMode
        assert HypothesisStatus
        assert DiscoveryHypothesisResult

    def test_hypothesis_mode_values(self) -> None:
        from src.discovery import HypothesisMode
        assert HypothesisMode.ADJACENT_KEYWORD.value == "adjacent_keyword"
        assert HypothesisMode.ADJACENT_NICHE.value == "adjacent_niche"
        assert HypothesisMode.GAP_OPPORTUNITY.value == "gap_opportunity"
        assert HypothesisMode.TREND_CHASE.value == "trend_chase"

    def test_hypothesis_status_values(self) -> None:
        from src.discovery import HypothesisStatus
        assert HypothesisStatus.PENDING.value == "pending"
        assert HypothesisStatus.PROMOTED.value == "promoted"
        assert HypothesisStatus.REJECTED.value == "rejected"

    def test_discovery_output_properties(self) -> None:
        from src.discovery import DiscoveryHypothesisResult, DiscoveryOutput
        h = DiscoveryHypothesisResult(
            keyword="test kw", normalized_keyword="test kw", hypothesis_type="adjacent_keyword"
        )
        out = DiscoveryOutput(hypotheses=[h], promoted_keywords=["test kw"])
        assert out.hypothesis_count == 1
        assert out.promoted_count == 1

    def test_discovery_output_empty(self) -> None:
        from src.discovery import DiscoveryOutput
        out = DiscoveryOutput()
        assert out.hypothesis_count == 0
        assert out.promoted_count == 0

    def test_run_cycle_stub(self) -> None:
        from src.discovery import DiscoveryInput, DiscoveryOrchestrator
        orch = DiscoveryOrchestrator()
        out = orch.run_cycle(DiscoveryInput(niche_id="ai_saas", niche_name="AI SaaS"))
        assert out.niche_id == "ai_saas"
        assert out.hypothesis_count == 0

    def test_generate_hypotheses_stub(self) -> None:
        from src.discovery import DiscoveryInput, DiscoveryOrchestrator, HypothesisMode
        orch = DiscoveryOrchestrator()
        results = orch.generate_hypotheses(
            DiscoveryInput(niche_id="test"),
            HypothesisMode.ADJACENT_KEYWORD,
        )
        assert results == []

    def test_score_and_filter_stub(self) -> None:
        from src.discovery import DiscoveryHypothesisResult, DiscoveryOrchestrator
        orch = DiscoveryOrchestrator()
        h = DiscoveryHypothesisResult(
            keyword="kw", normalized_keyword="kw", hypothesis_type="adjacent_keyword",
            confidence=0.9,
        )
        result = orch.score_and_filter([h])
        assert len(result) == 1

    def test_promote_keywords_stub(self) -> None:
        from src.discovery import DiscoveryHypothesisResult, DiscoveryOrchestrator
        orch = DiscoveryOrchestrator()
        h = DiscoveryHypothesisResult(
            keyword="high confidence kw", normalized_keyword="high confidence kw",
            hypothesis_type="trend_chase", confidence=0.95,
        )
        promoted = orch.promote_keywords([h])
        assert promoted == []


# ---------------------------------------------------------------------------
# src/models/collection_runtime model smoke tests
# ---------------------------------------------------------------------------


class TestCollectionRuntimeModels:
    def test_model_imports(self) -> None:
        from src.models.collection_runtime import (
            CollectionCheckpoint,
            CollectionProxyEvent,
            CollectionQueueItem,
            CollectionSelectorAudit,
            CollectionSessionEvent,
        )
        assert CollectionCheckpoint.__tablename__ == "collection_checkpoints"
        assert CollectionProxyEvent.__tablename__ == "collection_proxy_events"
        assert CollectionQueueItem.__tablename__ == "collection_queue_items"
        assert CollectionSelectorAudit.__tablename__ == "collection_selector_audits"
        assert CollectionSessionEvent.__tablename__ == "collection_session_events"

    def test_models_insert_into_db(self, tmp_path: Path) -> None:
        from sqlalchemy.orm import Session
        from src.models.collection_runtime import (
            CollectionCheckpoint,
            CollectionProxyEvent,
            CollectionQueueItem,
            CollectionSelectorAudit,
            CollectionSessionEvent,
        )
        from src.models.database import initialize_database

        db = tmp_path / "cr.db"
        engine = initialize_database(database_url=f"sqlite:///{db.as_posix()}")

        with Session(engine) as session:
            session.add(CollectionCheckpoint(
                run_key="run-001", stage="collect", items_processed=5, items_total=10
            ))
            session.add(CollectionProxyEvent(run_key="run-001", event_type="connect"))
            session.add(CollectionQueueItem(
                run_key="run-001", item_type="search", item_key="python automation"
            ))
            session.add(CollectionSelectorAudit(
                selector="div.gig-title", selector_type="css", matched=True, matched_count=3
            ))
            session.add(CollectionSessionEvent(
                run_key="run-001", event_type="page_load",
                target_url="https://www.fiverr.com"
            ))
            session.commit()

        with Session(engine) as session:
            assert session.query(CollectionCheckpoint).count() == 1
            assert session.query(CollectionProxyEvent).count() == 1
            assert session.query(CollectionQueueItem).count() == 1
            assert session.query(CollectionSelectorAudit).count() == 1
            assert session.query(CollectionSessionEvent).count() == 1

    def test_report_models_insert_into_db(self, tmp_path: Path) -> None:
        from sqlalchemy.orm import Session
        from src.models.database import initialize_database
        from src.models.runtime import ReportRun, ReportSection

        db = tmp_path / "rr.db"
        engine = initialize_database(database_url=f"sqlite:///{db.as_posix()}")

        with Session(engine) as session:
            rr = ReportRun(
                niche_id="prd_ai_saas", report_type="market_summary",
                title="PRD AI SaaS Market Summary"
            )
            session.add(rr)
            session.flush()
            section = ReportSection(
                report_run_id=rr.id, section_key="executive_summary",
                title="Executive Summary", order_index=0,
                content="Market looks strong for new sellers."
            )
            session.add(section)
            session.commit()

        with Session(engine) as session:
            assert session.query(ReportRun).count() == 1
            assert session.query(ReportSection).count() == 1
