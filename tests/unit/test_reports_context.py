"""Unit tests for customer-facing report context builders (real DB queries)."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from src.models.database import create_session_factory, initialize_database
from src.models.job import Job
from src.models.keyword_score import KeywordScore
from src.models.market import Keyword
from src.models.niche import Niche, NicheConfigRecord
from src.models.scoring import Recommendation
from src.reports import context as reports_context


def _make_session() -> Any:
    engine = initialize_database("sqlite:///:memory:")
    session_factory = create_session_factory(engine)
    return session_factory()


def _seed_niche(session: Any, slug: str, name: str, depth: str = "standard") -> Niche:
    niche = Niche(slug=slug, name=name, category_path="programming-tech/testing")
    session.add(niche)
    session.add(
        NicheConfigRecord(
            niche_id=slug, name=name, depth=depth, category_path="programming-tech/testing"
        )
    )
    session.commit()
    session.refresh(niche)
    return niche


def _seed_keyword(session: Any, niche: Niche, text: str) -> Keyword:
    keyword = Keyword(niche_id=niche.id, keyword=text, normalized_keyword=text.lower())
    session.add(keyword)
    session.commit()
    session.refresh(keyword)
    return keyword


def _seed_score(
    session: Any, keyword: Keyword, *, final_score: float, tag: str, scored_at: datetime
) -> KeywordScore:
    score = KeywordScore(
        keyword_id=keyword.id,
        final_score=final_score,
        tag=tag,
        demand_score=70.0,
        competition_score=40.0,
        opportunity_score=60.0,
        feasibility_score=80.0,
        trend_score=55.0,
        confidence_modifier=0.9,
        scored_at=scored_at,
    )
    session.add(score)
    session.commit()
    return score


def test_opportunity_context_uses_latest_score_per_keyword_ranked_descending() -> None:
    session = _make_session()
    try:
        niche = _seed_niche(session, "ai_automation", "AI Automation", depth="full")
        keyword = _seed_keyword(session, niche, "ai workflow automation")
        # Stale score should be superseded by the newer one.
        _seed_score(
            session,
            keyword,
            final_score=40.0,
            tag="MONITOR",
            scored_at=datetime(2026, 1, 1, tzinfo=UTC),
        )
        _seed_score(
            session,
            keyword,
            final_score=88.0,
            tag="STRONG GO",
            scored_at=datetime(2026, 6, 1, tzinfo=UTC),
        )

        context = reports_context.build_opportunity_report_context(session)

        assert context["niches"][0]["name"] == "AI Automation"
        assert context["niches"][0]["depth"] == "full"
        assert context["niches"][0]["keywords"][0]["final_score"] == 88.0
        assert context["niches"][0]["keywords"][0]["tag"] == "STRONG GO"
        assert {m["label"]: m["value"] for m in context["summary_metrics"]}["STRONG GO"] == 1
    finally:
        session.close()


def test_opportunity_context_skips_niches_with_no_scored_keywords() -> None:
    session = _make_session()
    try:
        _seed_niche(session, "empty_niche", "Empty Niche")
        context = reports_context.build_opportunity_report_context(session)
        assert context["niches"] == []
    finally:
        session.close()


def test_opportunity_context_without_session_returns_empty_shape() -> None:
    assert reports_context.build_opportunity_report_context(object()) == {
        "summary_metrics": [],
        "niches": [],
    }


def test_recommendation_context_filters_to_go_tags_and_generation_complete() -> None:
    session = _make_session()
    try:
        niche = _seed_niche(session, "seo_writing", "SEO Writing")
        keyword_go = _seed_keyword(session, niche, "seo blog writing")
        keyword_pass = _seed_keyword(session, niche, "generic writing")

        session.add(
            Recommendation(
                keyword_id=keyword_go.id,
                niche_id=niche.slug,
                tag="STRONG GO",
                final_score=91.0,
                generation_complete=True,
                recommendation_type="keyword_recommendation",
                recommendation_text="strong go",
                gig_titles=[
                    {"title": "I will write seo blog content", "positioning_angle": "authority"}
                ],
                faq_entries=[{"question": "How fast?", "answer": "3 days"}],
                differentiation_angle={
                    "positioning_statement": "Focus on technical SEO depth.",
                    "one_sentence_pitch": "SEO content that ranks.",
                    "differentiators": [{"action": "Publish keyword research alongside copy."}],
                },
                red_flags={"overall_risk_level": "LOW", "red_flags": []},
                niche_viability={
                    "viability_assessment": "Healthy demand.",
                    "timing_assessment": "Good entry window.",
                    "blunt_recommendation": "Go.",
                },
                package_structure={
                    "basic": {
                        "name": "Basic",
                        "price": 50,
                        "deliverables": ["500 words"],
                        "delivery_days": 3,
                        "revisions": 1,
                    },
                    "standard": {
                        "name": "Standard",
                        "price": 100,
                        "deliverables": ["1000 words"],
                        "delivery_days": 5,
                        "revisions": 2,
                    },
                    "premium": {
                        "name": "Premium",
                        "price": 200,
                        "deliverables": ["2000 words"],
                        "delivery_days": 7,
                        "revisions": 3,
                    },
                },
            )
        )
        # Should be excluded: tag not in GO set.
        session.add(
            Recommendation(
                keyword_id=keyword_pass.id,
                niche_id=niche.slug,
                tag="PASS",
                final_score=20.0,
                generation_complete=True,
                recommendation_type="keyword_recommendation",
                recommendation_text="pass",
            )
        )
        # Should be excluded: generation not complete.
        session.add(
            Recommendation(
                keyword_id=keyword_go.id,
                niche_id=niche.slug,
                tag="CONDITIONAL GO",
                final_score=70.0,
                generation_complete=False,
                recommendation_type="keyword_recommendation",
                recommendation_text="incomplete",
            )
        )
        session.commit()

        context = reports_context.build_recommendation_report_context(session)

        assert len(context["recommendations"]) == 1
        rec = context["recommendations"][0]
        assert rec["tag"] == "STRONG GO"
        assert rec["keyword_text"] == "seo blog writing"
        assert rec["viability"]["blunt_recommendation"] == "Go."
        assert rec["differentiation"]["one_sentence_pitch"] == "SEO content that ranks."
        assert rec["package_structure"]["premium"]["price"] == 200
    finally:
        session.close()


def test_run_summary_context_derives_metrics_from_pipeline_results_and_db() -> None:
    session = _make_session()
    try:
        niche = _seed_niche(session, "video_editing", "Video Editing")
        keyword = _seed_keyword(session, niche, "video editing services")
        session.add(
            Recommendation(
                keyword_id=keyword.id,
                niche_id=niche.slug,
                run_id_text="run-abc",
                tag="STRONG GO",
                final_score=93.0,
                generation_complete=True,
                recommendation_type="keyword_recommendation",
                recommendation_text="strong go",
            )
        )
        session.add(
            Job(
                job_id="job-1",
                run_id="run-abc",
                job_type="GIG_DETAIL",
                stage=4,
                niche_id="video_editing",
                priority="STANDARD",
                status="DEAD_LETTER",
                error_log=["timeout", "final failure: max retries exceeded"],
            )
        )
        session.commit()

        context = reports_context.build_run_summary_context(
            run_id="run-abc",
            duration_seconds=125.0,
            collection_result={
                "search_jobs_run": 10,
                "gig_detail_jobs_run": 40,
                "errors": ["one error"],
            },
            scored_count=8,
            recommendations_result={"total_cost_usd": 1.23},
            db=session,
        )

        run = context["run"]
        assert run["duration"] == "2m 5s"
        assert run["llm_cost"] == 1.23
        assert run["keywords_expanded"] == 10
        assert run["gigs_collected"] == 40
        assert run["error_count"] == 1
        assert run["new_strong_go"] == [
            {
                "keyword_text": "video editing services",
                "niche_name": "Video Editing",
                "final_score": 93.0,
            }
        ]
        assert run["dead_letters"] == [
            {"job_type": "GIG_DETAIL", "error_message": "final failure: max retries exceeded"}
        ]
    finally:
        session.close()


def test_run_summary_context_without_db_still_returns_pipeline_derived_metrics() -> None:
    context = reports_context.build_run_summary_context(
        run_id="run-xyz",
        duration_seconds=45.0,
        collection_result={"search_jobs_run": 3, "gig_detail_jobs_run": 5, "errors": []},
        scored_count=2,
        recommendations_result={},
        db=None,
    )
    run = context["run"]
    assert run["duration"] == "45s"
    assert run["llm_cost"] == 0.0
    assert run["new_strong_go"] == []
    assert run["dead_letters"] == []
