"""Unit tests for discovery candidate model and helper stubs."""

from __future__ import annotations

import asyncio
import json
from pathlib import Path
from types import SimpleNamespace

from sqlalchemy.orm import Session
from src.discovery import (
    create_discovery_candidate,
    generate_niche_hypotheses,
    get_pending_candidates,
    is_valid_candidate,
    score_hypothesis_signals,
    update_candidate_status,
)
from src.discovery.hypothesis import _coerce_json_payload
from src.models.database import create_session_factory, initialize_database
from src.models.discovery import DiscoveryCandidate


def _init_session(tmp_path: Path, name: str) -> Session:
    db_path = tmp_path / name
    engine = initialize_database(database_url=f"sqlite:///{db_path.as_posix()}")
    return create_session_factory(engine)()


def test_discovery_candidate_table_name() -> None:
    assert DiscoveryCandidate.__tablename__ == "discovery_candidates"


def test_discovery_candidate_insert_minimal(tmp_path: Path) -> None:
    session = _init_session(tmp_path, "discovery_minimal.db")
    candidate = DiscoveryCandidate(
        candidate_id="disc_minimal_1",
        hypothesis_text="AI workflow automation consulting",
        hypothesis_type="adjacent_keyword",
    )
    session.add(candidate)
    session.commit()
    fetched = session.query(DiscoveryCandidate).filter_by(candidate_id="disc_minimal_1").one()
    assert fetched.hypothesis_text == "AI workflow automation consulting"
    session.close()


def test_discovery_candidate_status_enum(tmp_path: Path) -> None:
    session = _init_session(tmp_path, "discovery_status.db")
    statuses = ["PENDING", "EVALUATED", "ACCEPTED", "REJECTED", "MONITORING"]
    for index, status in enumerate(statuses, start=1):
        session.add(
            DiscoveryCandidate(
                candidate_id=f"disc_status_{index}",
                hypothesis_text=f"valid niche hypothesis {index}",
                hypothesis_type="niche_expansion",
                status=status,
            )
        )
    session.commit()
    assert session.query(DiscoveryCandidate).count() == len(statuses)
    session.close()


def test_discovery_candidate_nullable_fields(tmp_path: Path) -> None:
    session = _init_session(tmp_path, "discovery_nullable.db")
    candidate = DiscoveryCandidate(
        candidate_id="disc_nullable_1",
        hypothesis_text="Python integration pipeline services",
        hypothesis_type="trend_signal",
        source_signal=None,
        source_niche_id=None,
        discovery_score=None,
        market_size_signal=None,
        competition_gap_signal=None,
        trend_signal=None,
        llm_hypothesis_text=None,
        llm_reasoning=None,
        evaluated_at=None,
        accepted_at=None,
        run_id=None,
        user_notes=None,
    )
    session.add(candidate)
    session.commit()
    fetched = session.query(DiscoveryCandidate).filter_by(candidate_id="disc_nullable_1").one()
    assert fetched.source_signal is None
    assert fetched.llm_reasoning is None
    session.close()


def test_is_valid_candidate_too_short() -> None:
    valid, reason = is_valid_candidate("automation", [])
    assert valid is False
    assert reason == "hypothesis_too_short"


def test_is_valid_candidate_too_long() -> None:
    text = "a" * 101
    valid, reason = is_valid_candidate(text, [])
    assert valid is False
    assert reason == "hypothesis_too_long"


def test_is_valid_candidate_empty() -> None:
    valid, reason = is_valid_candidate("   ", [])
    assert valid is False
    assert reason == "empty_hypothesis"


def test_is_valid_candidate_valid() -> None:
    valid, reason = is_valid_candidate("AI product roadmap service", ["Website Copy"])
    assert valid is True
    assert reason == "valid"


def test_is_valid_candidate_exact_existing_match() -> None:
    valid, reason = is_valid_candidate("AI Product Roadmap Service", ["ai product roadmap service"])
    assert valid is False
    assert reason == "matches_existing_niche"


def test_is_valid_candidate_blocked_term() -> None:
    valid, reason = is_valid_candidate("Adult AI content generation", [])
    assert valid is False
    assert reason == "blocked_term"


def test_create_candidate_returns_none_for_invalid() -> None:
    created = create_discovery_candidate("short", "adjacent_keyword", None, None, None, db={})
    assert created is None


def test_create_candidate_dict_db() -> None:
    created = create_discovery_candidate(
        "AI agent architecture diagrams",
        "adjacent_keyword",
        "seed_keyword",
        "niche-1",
        "run-1",
        db={},
    )
    assert created is not None
    assert isinstance(created, DiscoveryCandidate)
    assert created.id is None


def test_create_candidate_orm_db(tmp_path: Path) -> None:
    session = _init_session(tmp_path, "discovery_create.db")
    created = create_discovery_candidate(
        "AI workflow process optimization",
        "niche_expansion",
        "keyword:workflow optimization",
        "niche-2",
        "run-2",
        db=session,
    )
    assert created is not None
    fetched = session.query(DiscoveryCandidate).filter_by(candidate_id=created.candidate_id).one_or_none()
    assert fetched is not None
    session.close()


def test_create_candidate_rejects_unknown_type() -> None:
    created = create_discovery_candidate(
        "AI process documentation services",
        "unknown_type",
        None,
        None,
        None,
        db={},
    )
    assert created is None


def test_create_candidate_orm_commit_failure_returns_none(tmp_path: Path) -> None:
    session = _init_session(tmp_path, "discovery_commit_failure.db")
    original_commit = session.commit

    def _raise_commit() -> None:
        raise RuntimeError("forced failure")

    session.commit = _raise_commit  # type: ignore[method-assign]
    created = create_discovery_candidate(
        "AI onboarding sequence optimization",
        "niche_expansion",
        None,
        None,
        None,
        db=session,
    )
    assert created is None
    session.commit = original_commit  # type: ignore[method-assign]
    session.close()


def test_get_pending_candidates_empty(tmp_path: Path) -> None:
    session = _init_session(tmp_path, "discovery_pending_empty.db")
    session.add(
        DiscoveryCandidate(
            candidate_id="disc_not_pending",
            hypothesis_text="Automation testing framework support",
            hypothesis_type="manual_submission",
            status="EVALUATED",
        )
    )
    session.commit()
    assert get_pending_candidates(session) == []
    session.close()


def test_get_pending_candidates_filters_status(tmp_path: Path) -> None:
    session = _init_session(tmp_path, "discovery_pending_filter.db")
    session.add_all(
        [
            DiscoveryCandidate(
                candidate_id="disc_pending_1",
                hypothesis_text="Python API integration playbook",
                hypothesis_type="adjacent_keyword",
                status="PENDING",
            ),
            DiscoveryCandidate(
                candidate_id="disc_rejected_1",
                hypothesis_text="Legacy website copy support",
                hypothesis_type="manual_submission",
                status="REJECTED",
            ),
        ]
    )
    session.commit()
    pending = get_pending_candidates(session)
    assert len(pending) == 1
    assert pending[0].candidate_id == "disc_pending_1"
    session.close()


def test_get_pending_candidates_non_session_returns_empty() -> None:
    assert get_pending_candidates(db={"not": "session"}) == []


def test_update_candidate_status_success(tmp_path: Path) -> None:
    session = _init_session(tmp_path, "discovery_update.db")
    created = create_discovery_candidate(
        "AI onboarding workflow blueprints",
        "adjacent_keyword",
        "seed:workflow",
        "niche-3",
        "run-3",
        db=session,
    )
    assert created is not None
    assert update_candidate_status(created.candidate_id, "EVALUATED", session) is True
    refreshed = session.query(DiscoveryCandidate).filter_by(candidate_id=created.candidate_id).one()
    assert refreshed.status == "EVALUATED"
    assert refreshed.evaluated_at is not None
    session.close()


def test_update_candidate_status_non_session_returns_false() -> None:
    assert update_candidate_status("disc_unknown", "EVALUATED", db={}) is False


def test_update_candidate_status_invalid_status_returns_false(tmp_path: Path) -> None:
    session = _init_session(tmp_path, "discovery_invalid_status.db")
    assert update_candidate_status("missing", "INVALID", session) is False
    session.close()


def test_update_candidate_status_missing_candidate_returns_false(tmp_path: Path) -> None:
    session = _init_session(tmp_path, "discovery_missing_status.db")
    assert update_candidate_status("missing", "EVALUATED", session) is False
    session.close()


def test_update_candidate_status_accepted_sets_timestamp(tmp_path: Path) -> None:
    session = _init_session(tmp_path, "discovery_accept_status.db")
    created = create_discovery_candidate(
        "Python API reliability engineering",
        "adjacent_keyword",
        None,
        None,
        None,
        db=session,
    )
    assert created is not None
    assert update_candidate_status(created.candidate_id, "ACCEPTED", session) is True
    refreshed = session.query(DiscoveryCandidate).filter_by(candidate_id=created.candidate_id).one()
    assert refreshed.accepted_at is not None
    session.close()


def test_update_candidate_status_commit_failure_returns_false(tmp_path: Path) -> None:
    session = _init_session(tmp_path, "discovery_update_commit_failure.db")
    session.add(
        DiscoveryCandidate(
            candidate_id="disc_update_commit_failure",
            hypothesis_text="Python content strategy service",
            hypothesis_type="manual_submission",
        )
    )
    session.commit()
    original_commit = session.commit

    def _raise_commit() -> None:
        raise RuntimeError("forced failure")

    session.commit = _raise_commit  # type: ignore[method-assign]
    assert update_candidate_status("disc_update_commit_failure", "EVALUATED", session) is False
    session.commit = original_commit  # type: ignore[method-assign]
    session.close()


def test_score_hypothesis_signals_all_present() -> None:
    candidate = DiscoveryCandidate(
        candidate_id="disc_score_1",
        hypothesis_text="AI roadmap coaching package",
        hypothesis_type="adjacent_keyword",
    )
    score = score_hypothesis_signals(
        candidate,
        market_size_signal=80.0,
        competition_gap_signal=60.0,
        trend_signal=40.0,
    )
    assert score == 63.0


def test_score_hypothesis_signals_all_none() -> None:
    candidate = DiscoveryCandidate(
        candidate_id="disc_score_2",
        hypothesis_text="AI backlog refinement offer",
        hypothesis_type="adjacent_keyword",
    )
    assert score_hypothesis_signals(candidate, None, None, None) is None


def test_generate_hypotheses_no_llm() -> None:
    result = asyncio.run(
        generate_niche_hypotheses(
            source_niche_id="niche-4",
            existing_keywords=["ai roadmap"],
            llm_client=None,
            cache=None,
        )
    )
    assert result == []


def test_generate_hypotheses_mock_llm() -> None:
    class MockLlmClient:
        async def complete(self, **_: object) -> SimpleNamespace:
            payload = {
                "hypotheses": [
                    {
                        "suggested_keyword": "AI PRD strategy workshop",
                        "mode": "adjacent_keyword",
                        "rationale": "Adjacent to existing PRD demand.",
                    }
                ]
            }
            return SimpleNamespace(text=json.dumps(payload))

    result = asyncio.run(
        generate_niche_hypotheses(
            source_niche_id="niche-5",
            existing_keywords=["ai prd consulting"],
            llm_client=MockLlmClient(),
            cache=None,
        )
    )
    assert len(result) == 1
    assert result[0]["hypothesis_text"] == "AI PRD strategy workshop"
    assert result[0]["hypothesis_type"] == "adjacent_keyword"


def test_generate_hypotheses_sync_llm_client() -> None:
    class SyncClient:
        def complete(self, **_: object) -> SimpleNamespace:
            payload = {"hypotheses": [{"keyword": "Sync LLM keyword", "mode": "adjacent_keyword"}]}
            return SimpleNamespace(text=json.dumps(payload))

    result = asyncio.run(
        generate_niche_hypotheses(
            source_niche_id="niche-sync",
            existing_keywords=["seed"],
            llm_client=SyncClient(),
            cache=None,
        )
    )
    assert len(result) == 1
    assert result[0]["hypothesis_text"] == "Sync LLM keyword"


def test_generate_hypotheses_llm_error_returns_empty() -> None:
    class FailingLlmClient:
        async def complete(self, **_: object) -> SimpleNamespace:
            raise RuntimeError("llm unavailable")

    result = asyncio.run(
        generate_niche_hypotheses(
            source_niche_id="niche-6",
            existing_keywords=[],
            llm_client=FailingLlmClient(),
            cache=None,
        )
    )
    assert result == []


def test_generate_hypotheses_invalid_json_returns_empty() -> None:
    class InvalidJsonClient:
        async def complete(self, **_: object) -> SimpleNamespace:
            return SimpleNamespace(text="{bad-json")

    result = asyncio.run(
        generate_niche_hypotheses(
            source_niche_id="niche-7",
            existing_keywords=[],
            llm_client=InvalidJsonClient(),
            cache=None,
        )
    )
    assert result == []


def test_generate_hypotheses_non_list_payload_returns_empty() -> None:
    class NonListPayloadClient:
        async def complete(self, **_: object) -> dict[str, object]:
            return {"hypotheses": "invalid"}

    result = asyncio.run(
        generate_niche_hypotheses(
            source_niche_id="niche-8",
            existing_keywords=[],
            llm_client=NonListPayloadClient(),
            cache=None,
        )
    )
    assert result == []


def test_generate_hypotheses_skips_malformed_items() -> None:
    class MixedPayloadClient:
        async def complete(self, **_: object) -> dict[str, object]:
            return {
                "hypotheses": [
                    "not-a-dict",
                    {"mode": "adjacent_keyword"},
                    {
                        "keyword": "AI process documentation advisor",
                        "hypothesis_type": "trend_signal",
                        "source_signal": "trend:docs",
                    },
                ]
            }

    result = asyncio.run(
        generate_niche_hypotheses(
            source_niche_id="niche-9",
            existing_keywords=[],
            llm_client=MixedPayloadClient(),
            cache=None,
        )
    )
    assert len(result) == 1
    assert result[0]["hypothesis_text"] == "AI process documentation advisor"


def test_coerce_json_payload_non_string_returns_none() -> None:
    assert _coerce_json_payload(SimpleNamespace(text=123)) is None
