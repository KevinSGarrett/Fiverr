"""Integration tests for gated discovery flow."""

from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

from sqlalchemy.orm import Session
from src.discovery.contracts import DiscoveryInput
from src.discovery.orchestrator import DiscoveryOrchestrator
from src.models.database import create_session_factory, initialize_database
from src.models.discovery_outcome import DiscoveryOutcome
from src.models.market import Keyword


def _init_session(tmp_path: Path, name: str) -> Session:
    db_path = tmp_path / name
    engine = initialize_database(database_url=f"sqlite:///{db_path.as_posix()}")
    return create_session_factory(engine)()


def _config(enable_relevance_gates: bool) -> SimpleNamespace:
    return SimpleNamespace(discovery=SimpleNamespace(enable_relevance_gates=enable_relevance_gates))


def _valid_cards(keyword: str) -> list[dict[str, object]]:
    return [
        {"gig_title": f"I will deliver {keyword} help center support docs", "gig_url": "g1"},
        {"gig_title": f"I will optimize {keyword} knowledge base workflows", "gig_url": "g2"},
        {"gig_title": f"I will audit {keyword} support FAQ content", "gig_url": "g3"},
        {"gig_title": f"I will improve {keyword} chatbot handoff docs", "gig_url": "g4"},
        {"gig_title": f"I will write {keyword} support docs", "gig_url": "g5"},
        {"gig_title": f"I will create {keyword} help center templates", "gig_url": "g6"},
    ]


def _contaminated_cards() -> list[dict[str, object]]:
    return [
        {"gig_title": "I will write support docs help center", "gig_url": "c1"},
        {"gig_title": "I will improve support knowledge base", "gig_url": "c2"},
        {"gig_title": "I will design social media logo", "gig_url": "c3"},
        {"gig_title": "I will edit wedding invitation video", "gig_url": "c4"},
        {"gig_title": "I will create seo crypto blog posts", "gig_url": "c5"},
    ]


def test_discovery_flow_gates_end_to_end(tmp_path: Path) -> None:
    session = _init_session(tmp_path, "discovery_gates_on.db")
    orchestrator = DiscoveryOrchestrator(config=_config(True), session=session)

    valid_candidates = [
        "help center article rewrite package",
        "support kb audit workflow",
        "saas faq restructuring service",
        "support docs information architecture",
        "chatbot handoff support docs setup",
        "knowledge base cleanup and taxonomy",
        "help desk faq refresh",
    ]
    off_niche_candidate = "support team social banner design"
    ghost_candidate = "support docs cleanup special"
    contaminated_candidate = "support docs mixed intent package"

    hypotheses = [
        {"hypothesis_text": keyword, "buyer": "support lead", "deliverable": "help center docs"}
        for keyword in valid_candidates
    ] + [
        {
            "hypothesis_text": off_niche_candidate,
            "buyer": "support lead",
            "deliverable": "social media banners",
        },
        {"hypothesis_text": ghost_candidate, "buyer": "support lead", "deliverable": "help center docs"},
        {
            "hypothesis_text": contaminated_candidate,
            "buyer": "support lead",
            "deliverable": "help center docs",
        },
    ]

    provisional_result_sets = {keyword: _valid_cards(keyword) for keyword in valid_candidates}
    provisional_result_sets[ghost_candidate] = []
    provisional_result_sets[contaminated_candidate] = _contaminated_cards()

    discovery_input = DiscoveryInput(
        run_id="integration-r6-on",
        niche_id="support_kb_readiness",
        enabled_modes=["full"],
        llm_context={
            "hypotheses": hypotheses,
            "provisional_result_sets": provisional_result_sets,
            "config": _config(True),
        },
    )

    output = orchestrator.run_cycle(discovery_input)
    session.commit()

    inserted = {row.keyword for row in session.query(Keyword).all()}
    assert inserted == set(valid_candidates)

    invalid_count = (
        session.query(DiscoveryOutcome)
        .filter(
            DiscoveryOutcome.run_id == "integration-r6-on",
            DiscoveryOutcome.is_invalid.is_(True),
        )
        .count()
    )
    assert invalid_count == 2

    feedback = output.raw_json["feedback"]
    assert feedback["counted_invalid"] == 2
    assert feedback["counted_valid"] == len(valid_candidates)

    rejection_rate = float(output.raw_json["rejection_rate"])
    assert 0.20 <= rejection_rate <= 0.40
    session.close()


def test_discovery_flow_toggle_off_legacy_behavior(tmp_path: Path) -> None:
    session = _init_session(tmp_path, "discovery_gates_off.db")
    orchestrator = DiscoveryOrchestrator(config=_config(False), session=session)

    candidates = [
        "help center article rewrite package",
        "support team social banner design",
        "support docs cleanup special",
    ]
    hypotheses = [
        {
            "hypothesis_text": keyword,
            "buyer": "support lead",
            "deliverable": "help center docs" if "banner" not in keyword else "social media banners",
        }
        for keyword in candidates
    ]
    discovery_input = DiscoveryInput(
        run_id="integration-r6-off",
        niche_id="support_kb_readiness",
        enabled_modes=["full"],
        llm_context={
            "hypotheses": hypotheses,
            "provisional_result_sets": {candidates[2]: []},
            "config": _config(False),
        },
    )

    output = orchestrator.run_cycle(discovery_input)
    session.commit()

    inserted = {row.keyword for row in session.query(Keyword).all()}
    assert inserted == set(candidates)
    assert output.raw_json["rejected_candidates"] == 0
    invalid_outcomes = session.query(DiscoveryOutcome).filter(DiscoveryOutcome.is_invalid.is_(True)).count()
    assert invalid_outcomes == 0
    session.close()
