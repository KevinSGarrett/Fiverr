"""Unit tests for Cycle 055 discovery relevance gates."""

from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

from sqlalchemy.orm import Session
from src.analysis.pre_validator import DiscoveryPreValidator, DiscoveryVerdict
from src.discovery.contracts import DiscoveryInput
from src.discovery.hypothesis import (
    _gate_hypotheses,
    parse_hypothesis_contracts,
)
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


def _valid_result_set() -> list[dict[str, object]]:
    return [
        {"gig_title": "I will build support help center docs for SaaS", "gig_url": "u1"},
        {"gig_title": "I will write support help center docs and FAQ", "gig_url": "u2"},
        {"gig_title": "I will audit support help center docs workflow", "gig_url": "u3"},
        {"gig_title": "I will improve support help center docs structure", "gig_url": "u4"},
        {"gig_title": "I will optimize support help center docs taxonomy", "gig_url": "u5"},
        {"gig_title": "I will design support help center docs handoff", "gig_url": "u6"},
    ]


def _contaminated_result_set() -> list[dict[str, object]]:
    return [
        {"gig_title": "I will build support knowledge base and help center docs", "gig_url": "u1"},
        {"gig_title": "I will optimize support docs for your help center", "gig_url": "u2"},
        {"gig_title": "I will design logo and social banners", "gig_url": "u3"},
        {"gig_title": "I will edit a wedding invitation video", "gig_url": "u4"},
        {"gig_title": "I will write SEO blog posts for crypto", "gig_url": "u5"},
    ]


def _build_input(
    *,
    run_id: str,
    hypotheses: list[dict[str, str]],
    provisional_result_sets: dict[str, list[dict[str, object]]],
    gates_enabled: bool,
) -> DiscoveryInput:
    return DiscoveryInput(
        run_id=run_id,
        niche_id="support_kb_readiness",
        enabled_modes=["full"],
        llm_context={
            "hypotheses": hypotheses,
            "provisional_result_sets": provisional_result_sets,
            "config": _config(gates_enabled),
        },
    )


def test_low_specificity_hypothesis_rejected() -> None:
    contracts = parse_hypothesis_contracts(
        [{"hypothesis_text": "support", "buyer": None, "deliverable": None}],
        source_niche_id="support_kb_readiness",
    )
    accepted = _gate_hypotheses(contracts)
    assert accepted == []
    assert contracts[0].accepted is False


def test_gate1_rejects_missing_buyer_or_deliverable() -> None:
    contracts = parse_hypothesis_contracts(
        [
            {
                "hypothesis_text": "rewrite help center docs",
                "buyer": None,
                "deliverable": "help center docs",
            },
            {
                "hypothesis_text": "support manager service",
                "buyer": "SaaS support manager",
                "deliverable": None,
            },
        ],
        source_niche_id="support_kb_readiness",
    )
    accepted = _gate_hypotheses(contracts)
    assert accepted == []


def test_gate1_rejects_off_niche_hypothesis() -> None:
    contracts = parse_hypothesis_contracts(
        [
            {
                "hypothesis_text": "social banner design for support teams",
                "buyer": "support team lead",
                "deliverable": "social media banners",
            }
        ],
        source_niche_id="support_kb_readiness",
    )
    accepted = _gate_hypotheses(contracts)
    assert accepted == []
    assert contracts[0].specificity_score < 0.75


def test_gate1_borderline_threshold_behavior() -> None:
    contracts = parse_hypothesis_contracts(
        [
            {
                "hypothesis_text": "support_kb_readiness deliverable",
                "buyer": "support manager",
                "deliverable": "help center docs",
            },
            {
                "hypothesis_text": "support_kb_readiness broad",
                "buyer": "support manager",
                "deliverable": "logo design",
            },
        ],
        source_niche_id="support_kb_readiness",
    )
    accepted_low = _gate_hypotheses(contracts, threshold=0.67)
    accepted_high = _gate_hypotheses(contracts, threshold=0.68)
    assert len(accepted_low) == 2
    assert len(accepted_high) == 1


def test_pre_validator_maps_valid_ghost_and_contaminated() -> None:
    validator = DiscoveryPreValidator()
    assert (
        validator.evaluate(
            candidate="support help center docs",
            niche_id="support_kb_readiness",
            provisional_result_set=_valid_result_set(),
        ).verdict
        is DiscoveryVerdict.VALID
    )
    assert (
        validator.evaluate(
            candidate="support help center docs",
            niche_id="support_kb_readiness",
            provisional_result_set=[],
        ).verdict
        is DiscoveryVerdict.GHOST
    )
    assert (
        validator.evaluate(
            candidate="support help center docs",
            niche_id="support_kb_readiness",
            provisional_result_set=_contaminated_result_set(),
        ).verdict
        is DiscoveryVerdict.CONTAMINATED
    )


def test_ghost_discovery_recorded_as_invalid_not_miss(tmp_path: Path) -> None:
    session = _init_session(tmp_path, "reg25.db")
    orchestrator = DiscoveryOrchestrator(config=_config(True), session=session)
    candidate = "help center rewrite package"
    discovery_input = _build_input(
        run_id="reg25",
        hypotheses=[{"hypothesis_text": candidate, "buyer": "support lead", "deliverable": "help center docs"}],
        provisional_result_sets={candidate: []},
        gates_enabled=True,
    )

    orchestrator.run_cycle(discovery_input)
    session.commit()

    outcome = session.query(DiscoveryOutcome).filter_by(keyword_text=candidate).one()
    assert outcome.is_invalid is True
    assert outcome.is_invalid is not False
    assert session.query(Keyword).filter_by(keyword=candidate).count() == 0
    session.close()


def test_feedback_excludes_contaminated_outcomes(tmp_path: Path) -> None:
    session = _init_session(tmp_path, "reg26.db")
    session.add_all(
        [
            DiscoveryOutcome(
                run_id="reg26",
                niche_id="support_kb_readiness",
                keyword_text="valid-miss",
                is_invalid=False,
                is_contaminated=False,
            ),
            DiscoveryOutcome(
                run_id="reg26",
                niche_id="support_kb_readiness",
                keyword_text="invalid-contaminated",
                is_invalid=True,
                is_contaminated=True,
            ),
            DiscoveryOutcome(
                run_id="reg26",
                niche_id="support_kb_readiness",
                keyword_text="invalid-ghost",
                is_invalid=True,
                is_contaminated=False,
            ),
        ]
    )
    session.commit()

    orchestrator = DiscoveryOrchestrator(config=_config(True), session=session)
    gated_feedback = orchestrator.aggregate_feedback(
        run_id="reg26", session=session, enable_relevance_gates=True
    )
    legacy_feedback = orchestrator.aggregate_feedback(
        run_id="reg26", session=session, enable_relevance_gates=False
    )
    assert gated_feedback["counted_valid"] == 1
    assert gated_feedback["counted_invalid"] == 2
    assert legacy_feedback["counted_valid"] == 3
    session.close()


def test_gate2_valid_candidate_inserted(tmp_path: Path) -> None:
    session = _init_session(tmp_path, "gate2_valid.db")
    orchestrator = DiscoveryOrchestrator(config=_config(True), session=session)
    candidate = "support help center docs"
    discovery_input = _build_input(
        run_id="gate2_valid",
        hypotheses=[{"hypothesis_text": candidate, "buyer": "support lead", "deliverable": "help center docs"}],
        provisional_result_sets={candidate: _valid_result_set()},
        gates_enabled=True,
    )
    orchestrator.run_cycle(discovery_input)
    session.commit()
    assert session.query(Keyword).filter_by(keyword=candidate).count() == 1
    session.close()


def test_gate2_ghost_candidate_not_inserted_and_invalid(tmp_path: Path) -> None:
    session = _init_session(tmp_path, "gate2_ghost.db")
    orchestrator = DiscoveryOrchestrator(config=_config(True), session=session)
    candidate = "support docs cleanup package"
    discovery_input = _build_input(
        run_id="gate2_ghost",
        hypotheses=[{"hypothesis_text": candidate, "buyer": "support lead", "deliverable": "help center docs"}],
        provisional_result_sets={candidate: []},
        gates_enabled=True,
    )
    orchestrator.run_cycle(discovery_input)
    session.commit()
    assert session.query(Keyword).filter_by(keyword=candidate).count() == 0
    outcome = session.query(DiscoveryOutcome).filter_by(keyword_text=candidate).one()
    assert outcome.is_invalid is True
    session.close()


def test_gate2_contaminated_candidate_not_inserted_and_invalid(tmp_path: Path) -> None:
    session = _init_session(tmp_path, "gate2_contaminated.db")
    orchestrator = DiscoveryOrchestrator(config=_config(True), session=session)
    candidate = "support docs optimization package"
    discovery_input = _build_input(
        run_id="gate2_contaminated",
        hypotheses=[{"hypothesis_text": candidate, "buyer": "support lead", "deliverable": "help center docs"}],
        provisional_result_sets={candidate: _contaminated_result_set()},
        gates_enabled=True,
    )
    orchestrator.run_cycle(discovery_input)
    session.commit()
    assert session.query(Keyword).filter_by(keyword=candidate).count() == 0
    outcome = session.query(DiscoveryOutcome).filter_by(keyword_text=candidate).one()
    assert outcome.is_invalid is True
    assert outcome.is_contaminated is True
    session.close()


def test_toggle_off_discovery_legacy_parity_insert_all(tmp_path: Path) -> None:
    session = _init_session(tmp_path, "toggle_off.db")
    orchestrator = DiscoveryOrchestrator(config=_config(False), session=session)
    candidate = "support docs cleanup package"
    discovery_input = _build_input(
        run_id="toggle_off",
        hypotheses=[{"hypothesis_text": candidate, "buyer": "support lead", "deliverable": "help center docs"}],
        provisional_result_sets={candidate: []},
        gates_enabled=False,
    )
    orchestrator.run_cycle(discovery_input)
    session.commit()
    assert session.query(Keyword).filter_by(keyword=candidate).count() == 1
    outcome = session.query(DiscoveryOutcome).filter_by(keyword_text=candidate).one()
    assert outcome.is_invalid is False
    session.close()
