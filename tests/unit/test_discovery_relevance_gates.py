"""Unit tests for Cycle 055 discovery relevance gates."""

from __future__ import annotations

import json
from pathlib import Path
from types import SimpleNamespace

import pytest
from sqlalchemy.orm import Session
from src.analysis.pre_validator import DiscoveryPreValidator, DiscoveryVerdict
from src.discovery.contracts import DiscoveryInput
from src.discovery.hypothesis import (
    _gate_hypotheses,
    generate_niche_hypotheses,
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


def test_gate1_accepts_in_scope_contract_and_keeps_fields() -> None:
    contracts = parse_hypothesis_contracts(
        [
            {
                "hypothesis_text": "help center article rewrite service",
                "buyer": "SaaS support manager",
                "deliverable": "help center docs",
            }
        ],
        source_niche_id="support_kb_readiness",
    )
    accepted = _gate_hypotheses(contracts)
    assert len(accepted) == 1
    assert accepted[0].buyer == "SaaS support manager"
    assert accepted[0].deliverable == "help center docs"
    assert accepted[0].reason == "passed specificity + on-niche"


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
            provisional_result_set=_valid_result_set(),
        ).reason
        == "relevant_result_set"
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
            provisional_result_set=[],
        ).reason
        == "ghost_market_result_set"
    )
    assert (
        validator.evaluate(
            candidate="support help center docs",
            niche_id="support_kb_readiness",
            provisional_result_set=_contaminated_result_set(),
        ).verdict
        is DiscoveryVerdict.CONTAMINATED
    )
    assert (
        validator.evaluate(
            candidate="support help center docs",
            niche_id="support_kb_readiness",
            provisional_result_set=_contaminated_result_set(),
        ).reason
        == "contaminated_result_set"
    )


def test_pre_validator_low_rsv_without_flags_maps_to_contaminated(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def _fake_validate_result_set(*args: object, **kwargs: object) -> SimpleNamespace:
        del args
        del kwargs
        return SimpleNamespace(
            result_set_relevance_score=0.59,
            ghost_market_flag=False,
            category_contamination_flag=False,
        )

    monkeypatch.setattr("src.analysis.pre_validator.validate_result_set", _fake_validate_result_set)
    monkeypatch.setattr("src.analysis.pre_validator.compute_gig_relevance", lambda **_: 0.0)
    result = DiscoveryPreValidator(relevant_threshold=0.60).evaluate(
        candidate="support docs cleanup",
        niche_id="support_kb_readiness",
        provisional_result_set=[{"gig_title": "support docs cleanup", "gig_url": "x"}],
    )
    assert result.verdict is DiscoveryVerdict.CONTAMINATED
    assert result.reason.startswith("rsv_below_threshold:")
    assert result.rsv == 0.59


def test_pre_validator_threshold_boundary_is_valid(monkeypatch: pytest.MonkeyPatch) -> None:
    calls: list[object] = []

    def _fake_validate_result_set(*args: object, **kwargs: object) -> SimpleNamespace:
        calls.append(args[0] if args else kwargs.get("result_set"))
        return SimpleNamespace(
            result_set_relevance_score=0.60,
            ghost_market_flag=False,
            category_contamination_flag=False,
        )

    monkeypatch.setattr("src.analysis.pre_validator.validate_result_set", _fake_validate_result_set)
    monkeypatch.setattr("src.analysis.pre_validator.compute_gig_relevance", lambda **_: 0.9)
    validator = DiscoveryPreValidator(relevant_threshold=0.60)
    provisional = [{"gig_title": "I will rewrite support help center docs", "gig_url": "b1"}]
    result = validator.evaluate(
        candidate="support help center docs",
        niche_id="support_kb_readiness",
        provisional_result_set=provisional,
    )
    assert result.verdict is DiscoveryVerdict.VALID
    assert result.reason == "relevant_result_set"
    assert result.rsv == 0.60
    assert calls == [provisional]


def test_pre_validator_empty_result_set_skips_compute_call(monkeypatch: pytest.MonkeyPatch) -> None:
    compute_calls = {"count": 0}

    def _fake_validate_result_set(*args: object, **kwargs: object) -> SimpleNamespace:
        del args
        del kwargs
        return SimpleNamespace(
            result_set_relevance_score=0.01,
            ghost_market_flag=True,
            category_contamination_flag=False,
        )

    def _fake_compute_gig_relevance(**_: object) -> float:
        compute_calls["count"] += 1
        return 0.0

    monkeypatch.setattr("src.analysis.pre_validator.validate_result_set", _fake_validate_result_set)
    monkeypatch.setattr("src.analysis.pre_validator.compute_gig_relevance", _fake_compute_gig_relevance)
    result = DiscoveryPreValidator().evaluate(
        candidate="support docs cleanup",
        niche_id="support_kb_readiness",
        provisional_result_set=[],
    )
    assert result.verdict is DiscoveryVerdict.GHOST
    assert compute_calls["count"] == 0


def test_gate1_rejects_overbroad_single_term() -> None:
    contracts = parse_hypothesis_contracts(
        [{"hypothesis_text": "support", "buyer": "support lead", "deliverable": "help center docs"}],
        source_niche_id="support_kb_readiness",
    )
    accepted = _gate_hypotheses(contracts)
    assert accepted == []
    assert contracts[0].reason.startswith("specificity ")


@pytest.mark.asyncio
async def test_gate1_toggle_off_uses_legacy_normalization_without_filtering() -> None:
    llm_payload = {
        "hypotheses": [
            {
                "hypothesis_text": "support",
                "mode": "adjacent_keyword",
                "rationale": "legacy broad term still included",
            }
        ]
    }

    class _FakeClient:
        def complete(self, **_: object) -> SimpleNamespace:
            return SimpleNamespace(text=json.dumps(llm_payload))

    hypotheses = await generate_niche_hypotheses(
        source_niche_id="support_kb_readiness",
        existing_keywords=["support docs"],
        llm_client=_FakeClient(),
        cache=None,
        enable_relevance_gates=False,
    )
    assert hypotheses == [
        {
            "hypothesis_text": "support",
            "hypothesis_type": "adjacent_keyword",
            "source_signal": "legacy broad term still included",
        }
    ]


@pytest.mark.asyncio
async def test_gate1_toggle_on_filters_low_specificity_hypothesis() -> None:
    llm_payload = {
        "hypotheses": [
            {
                "hypothesis_text": "support",
                "buyer": None,
                "deliverable": None,
            }
        ]
    }

    class _FakeClient:
        def complete(self, **_: object) -> SimpleNamespace:
            return SimpleNamespace(text=json.dumps(llm_payload))

    hypotheses = await generate_niche_hypotheses(
        source_niche_id="support_kb_readiness",
        existing_keywords=["support docs"],
        llm_client=_FakeClient(),
        cache=None,
        enable_relevance_gates=True,
    )
    assert hypotheses == []


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
    assert outcome.contamination_reason == "ghost_market_result_set"
    assert outcome.relevance_score is not None
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
    assert outcome.contamination_reason == "contaminated_result_set" or (
        isinstance(outcome.contamination_reason, str)
        and outcome.contamination_reason.startswith("rsv_below_threshold:")
    )
    assert outcome.relevance_score is not None
    session.close()


def test_gate3_valid_candidate_records_miss_not_invalid(tmp_path: Path) -> None:
    session = _init_session(tmp_path, "gate3_miss.db")
    orchestrator = DiscoveryOrchestrator(config=_config(True), session=session)
    candidate = "support help center docs"
    discovery_input = _build_input(
        run_id="gate3_miss",
        hypotheses=[{"hypothesis_text": candidate, "buyer": "support lead", "deliverable": "help center docs"}],
        provisional_result_sets={candidate: _valid_result_set()},
        gates_enabled=True,
    )
    orchestrator.run_cycle(discovery_input)
    session.commit()
    outcome = session.query(DiscoveryOutcome).filter_by(keyword_text=candidate).one()
    assert outcome.is_invalid is False
    assert outcome.is_contaminated is False
    assert outcome.contamination_reason == "legacy_miss"
    assert outcome.relevance_score is not None
    session.close()


def test_gate3_gate4_composed_value_match_excludes_written_invalid(tmp_path: Path) -> None:
    session = _init_session(tmp_path, "gate34_composed.db")
    orchestrator = DiscoveryOrchestrator(config=_config(True), session=session)
    valid_candidate = "support help center docs"
    contaminated_candidate = "support docs mixed intent package"
    discovery_input = _build_input(
        run_id="gate34_composed",
        hypotheses=[
            {
                "hypothesis_text": valid_candidate,
                "buyer": "support lead",
                "deliverable": "help center docs",
            },
            {
                "hypothesis_text": contaminated_candidate,
                "buyer": "support lead",
                "deliverable": "help center docs",
            },
        ],
        provisional_result_sets={
            valid_candidate: _valid_result_set(),
            contaminated_candidate: _contaminated_result_set(),
        },
        gates_enabled=True,
    )
    orchestrator.run_cycle(discovery_input)
    session.commit()
    contaminated_outcome = (
        session.query(DiscoveryOutcome).filter_by(keyword_text=contaminated_candidate).one()
    )
    assert contaminated_outcome.is_invalid is True
    assert contaminated_outcome.is_contaminated is True
    gated_feedback = orchestrator.aggregate_feedback(
        run_id="gate34_composed", session=session, enable_relevance_gates=True
    )
    legacy_feedback = orchestrator.aggregate_feedback(
        run_id="gate34_composed", session=session, enable_relevance_gates=False
    )
    assert gated_feedback["counted_valid"] == 1
    assert gated_feedback["counted_invalid"] == 1
    assert legacy_feedback["counted_valid"] == 2
    session.close()


def test_orchestrator_none_safety_for_non_list_payloads(tmp_path: Path) -> None:
    session = _init_session(tmp_path, "none_safety_payloads.db")
    orchestrator = DiscoveryOrchestrator(config=_config(True), session=session)
    discovery_input = DiscoveryInput(
        run_id="none_safety_payloads",
        niche_id="support_kb_readiness",
        enabled_modes=["full"],
        llm_context={
            "hypotheses": "not-a-list",
            "provisional_result_sets": "not-a-dict",
            "config": _config(True),
        },
    )
    output = orchestrator.run_cycle(discovery_input)
    assert output.raw_json["total_candidates"] == 0
    assert output.raw_json["rejected_candidates"] == 0
    assert output.raw_json["rejection_rate"] == 0.0
    session.close()


def test_orchestrator_none_safety_for_non_list_provisional_rows(tmp_path: Path) -> None:
    session = _init_session(tmp_path, "none_safety_provisional.db")
    orchestrator = DiscoveryOrchestrator(config=_config(True), session=session)
    candidate = "support docs cleanup package"
    discovery_input = _build_input(
        run_id="none_safety_provisional",
        hypotheses=[{"hypothesis_text": candidate, "buyer": "support lead", "deliverable": "help center docs"}],
        provisional_result_sets={candidate: None},
        gates_enabled=True,
    )
    orchestrator.run_cycle(discovery_input)
    session.commit()
    outcome = session.query(DiscoveryOutcome).filter_by(keyword_text=candidate).one()
    assert outcome.is_invalid is True
    session.close()


def test_orchestrator_uses_context_session_when_provided(tmp_path: Path) -> None:
    session = _init_session(tmp_path, "context_session.db")
    orchestrator = DiscoveryOrchestrator(config=_config(False), session=None)
    candidate = "support docs context session candidate"
    discovery_input = DiscoveryInput(
        run_id="context_session",
        niche_id="support_kb_readiness",
        enabled_modes=["full"],
        llm_context={
            "hypotheses": [
                {
                    "hypothesis_text": candidate,
                    "buyer": "support lead",
                    "deliverable": "help center docs",
                }
            ],
            "provisional_result_sets": {},
            "config": _config(False),
            "session": session,
        },
    )
    orchestrator.run_cycle(discovery_input)
    session.commit()
    assert session.query(Keyword).filter_by(keyword=candidate).count() == 1
    session.close()


def test_feedback_toggle_off_handles_null_reason_and_rsv(tmp_path: Path) -> None:
    session = _init_session(tmp_path, "feedback_nulls.db")
    session.add_all(
        [
            DiscoveryOutcome(
                run_id="feedback_nulls",
                niche_id="support_kb_readiness",
                keyword_text="legacy-null",
                is_invalid=False,
                is_contaminated=False,
                relevance_score=None,
                contamination_reason=None,
            ),
            DiscoveryOutcome(
                run_id="feedback_nulls",
                niche_id="support_kb_readiness",
                keyword_text="legacy-invalid",
                is_invalid=True,
                is_contaminated=False,
                relevance_score=None,
                contamination_reason=None,
            ),
        ]
    )
    session.commit()
    orchestrator = DiscoveryOrchestrator(config=_config(False), session=session)
    legacy_feedback = orchestrator.aggregate_feedback(
        run_id="feedback_nulls", session=session, enable_relevance_gates=False
    )
    assert legacy_feedback["counted_valid"] == 2
    assert legacy_feedback["counted_invalid"] == 1
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
