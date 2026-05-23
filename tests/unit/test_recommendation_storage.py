"""Unit tests for Stage 13 recommendation persistence and export stubs."""

from __future__ import annotations

import asyncio
from datetime import UTC, datetime
from types import SimpleNamespace

import pytest
import src.recommendations.storage as storage
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from src.models import Base, Keyword, Niche, Recommendation
from src.recommendations.contracts import RecommendationContext
from src.recommendations.export import export_recommendation_json, export_recommendation_markdown
from src.recommendations.schemas import RecommendationOutput
from src.recommendations.storage import (
    get_recommendation,
    run_save_recommendations,
    save_recommendation,
)


def _session() -> Session:
    engine = create_engine("sqlite+pysqlite:///:memory:", future=True)
    Base.metadata.create_all(engine)
    return sessionmaker(bind=engine, autoflush=False, autocommit=False, expire_on_commit=False)()


def _seed_keyword(db: Session, keyword_id: int, niche_id: int = 1) -> None:
    if db.query(Niche).filter(Niche.id == niche_id).first() is None:
        db.add(Niche(id=niche_id, slug=f"niche-{niche_id}", name=f"Niche {niche_id}", category_path="programming-tech/test"))
    db.add(
        Keyword(
            id=keyword_id,
            niche_id=niche_id,
            keyword=f"keyword-{keyword_id}",
            normalized_keyword=f"keyword-{keyword_id}",
        )
    )
    db.commit()


def _context(keyword_id: int = 101, run_id: str = "run-storage-1") -> RecommendationContext:
    return RecommendationContext(
        keyword_id=keyword_id,
        keyword_text=f"keyword-{keyword_id}",
        niche_id="1",
        niche_name="Automation",
        run_id=run_id,
        tag="STRONG GO",
        final_score=82.0,
        confidence_modifier=0.84,
        top_competitor_weaknesses=[],
    )


def _full_output(generation_complete: bool = True) -> RecommendationOutput:
    payload = {
        "gig_titles": {
            "titles": [
                {
                    "title": f"I will build automation workflow package option {index} with clear outcomes",
                    "positioning_angle": "outcome",
                    "character_count": 70,
                    "primary_keyword_present": True,
                }
                for index in range(1, 6)
            ]
        },
        "tag_sets": {
            "tag_sets": [
                ["python automation", "workflow scripts", "api integration", "task bot", "etl setup"],
                ["automation expert", "ops workflow", "crm workflow", "zapier flow", "notion setup"],
                ["automation service", "python api", "business process", "data workflow", "automation audit"],
                ["team automation", "saas operations", "process design", "ops support", "automation strategy"],
                ["workflow mapping", "delivery fast", "support setup", "custom scripts", "integration help"],
            ]
        },
        "package_structure": {
            "basic": {
                "name": "Starter Automation",
                "price": 90,
                "deliverables": ["workflow discovery", "one automation flow"],
                "delivery_days": 3,
                "revisions": 1,
            },
            "standard": {
                "name": "Core Automation Build",
                "price": 210,
                "deliverables": ["workflow map", "two automation flows", "handoff doc"],
                "delivery_days": 5,
                "revisions": 2,
            },
            "premium": {
                "name": "Automation System Package",
                "price": 360,
                "deliverables": ["full map", "four automation flows", "training video"],
                "delivery_days": 8,
                "revisions": 3,
            },
        },
        "description_outline": {
            "sections": [
                {
                    "heading": "Benefit First Hook",
                    "copy_direction": "Lead with buyer outcome and reduced manual hours.",
                    "proof_elements": ["past results", "sample workflow"],
                    "estimated_words": 70,
                },
                {
                    "heading": "What You Receive",
                    "copy_direction": "List concrete deliverables with exact counts.",
                    "proof_elements": ["deliverable list"],
                    "estimated_words": 80,
                },
                {
                    "heading": "Why This Process Works",
                    "copy_direction": "Describe process checkpoints and communication rhythm.",
                    "proof_elements": ["timeline", "milestone updates"],
                    "estimated_words": 75,
                },
                {
                    "heading": "Call To Action",
                    "copy_direction": "Close with required inputs and next action.",
                    "proof_elements": ["ready checklist"],
                    "estimated_words": 60,
                },
            ]
        },
        "faq_entries": {
            "faq_entries": [
                {
                    "question": "Can you work with my existing automation stack?",
                    "answer": "Yes. I review your tools first and map compatible steps before delivery.",
                    "addresses_complaint": "tool-compatibility",
                },
                {
                    "question": "What do you need from me to get started?",
                    "answer": "I need process notes, tool access level, and target outcome before kickoff.",
                    "addresses_complaint": None,
                },
                {
                    "question": "Do you provide revisions if logic needs adjustment?",
                    "answer": "Yes. Revisions are included by package tier and scoped to agreed deliverables.",
                    "addresses_complaint": "revision-clarity",
                },
                {
                    "question": "Can you deliver quickly for urgent launches?",
                    "answer": "I can prioritize urgent timelines when scope and dependencies are clear.",
                    "addresses_complaint": "slow-delivery",
                },
                {
                    "question": "What is not included in this service?",
                    "answer": "I do not provide unrelated app development outside workflow scope.",
                    "addresses_complaint": "scope-creep",
                },
            ]
        },
        "differentiation_angle": {
            "positioning_statement": (
                "Most competitors offer generic bundles. This offer focuses on documented handoff, "
                "transparent checkpoints, and practical workflow reliability from day one."
            ),
            "differentiators": [
                {
                    "action": "Publish a clear implementation roadmap in the first message.",
                    "competitor_weakness_exploited": "Unclear onboarding expectations.",
                    "buyer_pain_addressed": "Buyers feel uncertain after ordering.",
                }
            ],
            "one_sentence_pitch": "I turn messy recurring tasks into documented workflows buyers can trust.",
        },
        "buyer_persona": {
            "name": "Alex",
            "role": "Operations Manager",
            "company_stage": "Early growth SaaS",
            "pain_points": ["manual handoffs", "missed updates"],
            "budget_range": "$150-$500",
            "decision_trigger": "Process failures are delaying customer onboarding.",
            "where_they_search": "Fiverr and operations communities",
            "what_makes_them_buy": "Clear scope and confidence in delivery speed.",
        },
        "thumbnail_direction": {
            "concept": "Show before-and-after workflow visibility with clean UI style.",
            "style": "Dark blue with bright accent highlights",
            "elements_to_include": ["workflow icons", "checklist", "timeline"],
            "elements_to_avoid": ["stock-photo faces"],
            "differentiation_note": "Use quantified outcomes to stand out from generic text-only thumbnails.",
        },
        "upsell_structure": {
            "extras": [
                {"name": "Priority 24h update", "price": 25, "description": "Priority response and update cycle."},
                {"name": "Post-launch tuning", "price": 45, "description": "Optimization pass after first week."},
            ]
        },
        "red_flags": {
            "red_flags": [
                {
                    "flag_type": "proof_gap",
                    "description": "Top competitors have long review history and strong social proof.",
                    "severity": "MEDIUM",
                    "mitigation": "Publish case-study assets and milestone updates.",
                }
            ],
            "overall_risk_level": "MEDIUM",
            "proceed_recommendation": "Proceed with a focused launch and tightly scoped packages.",
        },
        "niche_viability": {
            "viability_assessment": (
                "Demand remains healthy and competitor weakness signals suggest room for a clear newcomer "
                "position. Entry is viable when messaging stays specific and onboarding is structured."
            ),
            "timing_assessment": "Timing is favorable while buyer intent is still rising.",
            "risk_summary": "Primary risk is weak trust signals early in launch.",
            "blunt_recommendation": "Enter now with a focused scope and proof-first positioning.",
        },
        "generation_complete": generation_complete,
        "failed_tasks": [],
        "total_llm_cost_usd": 0.11,
    }
    return RecommendationOutput.model_validate(payload)


def test_save_recommendation_writes_all_fields() -> None:
    db = _session()
    _seed_keyword(db, 101)
    context = _context(101, "run-storage-write")
    output = _full_output()

    recommendation_id = save_recommendation(context=context, output=output, db=db)

    row = db.query(Recommendation).filter(Recommendation.id == int(recommendation_id)).one()
    assert row.gig_titles is not None
    assert row.tag_sets is not None
    assert row.package_structure is not None
    assert row.description_outline is not None
    assert row.faq_entries is not None
    assert row.differentiation_angle is not None
    assert row.buyer_persona is not None
    assert row.thumbnail_direction is not None
    assert row.upsell_structure is not None
    assert row.red_flags is not None
    assert row.niche_viability is not None
    assert row.llm_cost_usd == 0.11
    db.close()


def test_save_recommendation_sets_generation_complete() -> None:
    db = _session()
    _seed_keyword(db, 102)
    context = _context(102, "run-storage-complete")
    output = _full_output(generation_complete=True)

    recommendation_id = save_recommendation(context=context, output=output, db=db)

    row = db.query(Recommendation).filter(Recommendation.id == int(recommendation_id)).one()
    assert row.generation_complete is True
    db.close()


def test_run_save_recommendations_returns_counts() -> None:
    db = _session()
    _seed_keyword(db, 201)
    _seed_keyword(db, 202)
    _seed_keyword(db, 203)
    contexts = [_context(201, "run-batch"), _context(202, "run-batch"), _context(203, "run-batch")]
    outputs = [_full_output(), {"total_llm_cost_usd": -1}, None]

    summary = run_save_recommendations(eligible_keywords=contexts, outputs=outputs, db=db)

    assert summary == {"saved": 1, "failed": 1, "skipped": 1}
    db.close()


def test_get_recommendation_returns_output() -> None:
    db = _session()
    _seed_keyword(db, 301)
    context = _context(301, "run-get")
    output = _full_output()
    save_recommendation(context=context, output=output, db=db)

    loaded = get_recommendation(keyword_id=301, db=db)

    assert loaded is not None
    assert loaded.generation_complete is True
    assert loaded.total_llm_cost_usd == 0.11
    assert loaded.gig_titles is not None
    db.close()


def test_get_recommendation_returns_none_when_missing() -> None:
    db = _session()
    assert get_recommendation(keyword_id=9999, db=db) is None
    db.close()


def test_storage_exports_in_package_init() -> None:
    import src.recommendations as recommendations

    assert hasattr(recommendations, "save_recommendation")
    assert hasattr(recommendations, "get_recommendation")
    assert hasattr(recommendations, "run_save_recommendations")


def test_export_markdown_stub() -> None:
    assert asyncio.run(export_recommendation_markdown("rec-1", db=None)) == ""


def test_export_json_stub() -> None:
    assert asyncio.run(export_recommendation_json("rec-1", db=None)) == {}


def test_recommendation_model_has_all_11_task_columns() -> None:
    expected_columns = {
        "gig_titles",
        "tag_sets",
        "package_structure",
        "description_outline",
        "faq_entries",
        "differentiation_angle",
        "buyer_persona",
        "thumbnail_direction",
        "upsell_structure",
        "red_flags",
        "niche_viability",
    }
    assert expected_columns.issubset(set(Recommendation.__table__.columns.keys()))


def test_save_recommendation_raises_when_db_has_no_query_support() -> None:
    class _NoQuery:
        pass

    with pytest.raises(ValueError):
        save_recommendation(context=_context(), output=_full_output(), db=_NoQuery())


def test_save_recommendation_rolls_back_on_commit_failure(monkeypatch: pytest.MonkeyPatch) -> None:
    db = _session()
    _seed_keyword(db, 401)
    context = _context(401, "run-rollback")
    output = _full_output()
    rollback_called = {"value": False}
    original_rollback = db.rollback

    def _raise_commit() -> None:
        raise RuntimeError("commit failed")

    def _mark_rollback() -> None:
        rollback_called["value"] = True
        original_rollback()

    monkeypatch.setattr(db, "commit", _raise_commit)
    monkeypatch.setattr(db, "rollback", _mark_rollback)

    with pytest.raises(RuntimeError, match="commit failed"):
        save_recommendation(context=context, output=output, db=db)
    assert rollback_called["value"] is True
    db.close()


def test_save_recommendation_swallow_rollback_error_and_re_raise_commit_error(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    db = _session()
    _seed_keyword(db, 402)
    context = _context(402, "run-rollback-failure")
    output = _full_output()

    def _raise_commit() -> None:
        raise RuntimeError("commit failed")

    def _raise_rollback() -> None:
        raise RuntimeError("rollback failed")

    monkeypatch.setattr(db, "commit", _raise_commit)
    monkeypatch.setattr(db, "rollback", _raise_rollback)

    with pytest.raises(RuntimeError, match="commit failed"):
        save_recommendation(context=context, output=output, db=db)
    db.close()


def test_run_save_recommendations_counts_failed_when_save_raises(monkeypatch: pytest.MonkeyPatch) -> None:
    context = _context(501, "run-save-fail")
    output = _full_output()

    def _boom(*_args: object, **_kwargs: object) -> str:
        raise RuntimeError("boom")

    monkeypatch.setattr(storage, "save_recommendation", _boom)
    summary = run_save_recommendations(eligible_keywords=[context], outputs=[output], db=object())

    assert summary == {"saved": 0, "failed": 1, "skipped": 0}


def test_get_recommendation_returns_none_when_db_has_no_query() -> None:
    class _NoQuery:
        pass

    assert get_recommendation(keyword_id=77, db=_NoQuery()) is None


def test_get_recommendation_skips_incomplete_and_invalid_rows() -> None:
    incomplete = SimpleNamespace(
        generation_complete=False,
        raw_json={},
        llm_cost_usd=0.1,
    )
    invalid = SimpleNamespace(
        generation_complete=True,
        gig_titles={"bad": "shape"},
        tag_sets=None,
        package_structure=None,
        description_outline=None,
        faq_entries=None,
        differentiation_angle=None,
        buyer_persona=None,
        thumbnail_direction=None,
        upsell_structure=None,
        red_flags=None,
        niche_viability=None,
        raw_json={},
        llm_cost_usd=0.2,
    )

    class _Query:
        def __init__(self, rows: list[object]) -> None:
            self._rows = rows

        def filter(self, *_args: object, **_kwargs: object) -> _Query:
            return self

        def order_by(self, *_args: object, **_kwargs: object) -> _Query:
            return self

        def all(self) -> list[object]:
            return self._rows

    db = SimpleNamespace(query=lambda _model: _Query([incomplete, invalid]))
    assert get_recommendation(keyword_id=88, db=db) is None


def test_load_existing_recommendation_prefers_numeric_run_id() -> None:
    db = _session()
    _seed_keyword(db, 601)
    row = Recommendation(
        keyword_id=601,
        run_id=123,
        run_id_text="run-text",
        recommendation_type="keyword_recommendation",
        recommendation_text="hello",
        generation_complete=True,
    )
    db.add(row)
    db.commit()

    loaded = storage._load_existing_recommendation(keyword_id=601, run_id_int=123, run_id_text="other-run", db=db)

    assert loaded is not None
    assert loaded.id == row.id
    db.close()


def test_storage_helper_branches_cover_fallback_paths() -> None:
    now = datetime.now(UTC)
    assert storage._coerce_datetime(now) is now
    assert storage._coerce_datetime("not-a-date") is None
    assert storage._coerce_datetime(123) is None
    assert storage._safe_query(SimpleNamespace(), Recommendation) is None
    assert (
        storage._safe_query(
            SimpleNamespace(query=lambda _model: (_ for _ in ()).throw(RuntimeError("query failed"))),
            Recommendation,
        )
        is None
    )
    assert storage._coerce_recommendation_output(1234) is None
    assert storage._extract_failed_tasks("bad-json") == []
    assert storage._extract_failed_tasks({"failed_tasks": "not-a-list"}) == []


def test_iter_pairs_and_context_extraction_from_mapping() -> None:
    context = _context(701, "run-map")
    pairs = list(
        storage._iter_context_output_pairs(
            eligible_keywords=[{"context": context}, {"not_context": True}],
            outputs={701: "payload"},
        )
    )

    assert pairs[0] == (context, "payload")
    assert pairs[1] == (None, None)


def test_derive_recommendation_text_from_output_fallbacks() -> None:
    output = _full_output()
    output.niche_viability = None
    assert storage._derive_recommendation_text_from_output(output) == output.differentiation_angle.one_sentence_pitch

    output.differentiation_angle = None
    assert storage._derive_recommendation_text_from_output(output) == "Generated recommendation package"
