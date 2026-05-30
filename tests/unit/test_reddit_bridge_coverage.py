"""Additional branch coverage tests for Reddit Devvit bridge functions."""

from __future__ import annotations

from pathlib import Path

from sqlalchemy.orm import Session, sessionmaker

from src.collection.workflows.reddit_devvit_bridge import (
    load_devvit_signal_files,
    normalize_devvit_payload,
    resolve_keyword_id,
    strip_pii_fields,
    validate_devvit_payload,
    write_devvit_reddit_signals,
)
from src.models import Keyword, Niche
from src.models.database import initialize_database


def _session(tmp_path: Path) -> Session:
    db_path = tmp_path / "reddit_bridge_coverage.db"
    engine = initialize_database(database_url=f"sqlite:///{db_path.as_posix()}")
    return sessionmaker(bind=engine, future=True)()


def _seed(session: Session) -> tuple[Niche, Keyword]:
    niche = Niche(slug="support_kb_readiness", name="Support KB", category_path="writing-translation")
    session.add(niche)
    session.flush()
    keyword = Keyword(
        niche_id=int(niche.id),
        keyword="AI chatbot handoff",
        normalized_keyword="ai chatbot handoff",
    )
    session.add(keyword)
    session.commit()
    session.refresh(niche)
    session.refresh(keyword)
    return niche, keyword


def _payload() -> dict[str, object]:
    return {
        "schema_version": "reddit_devvit_signal_v1",
        "niche_id": "support_kb_readiness",
        "keywords": ["AI chatbot handoff"],
        "subreddits_searched": ["OpenAI"],
        "posts_collected": 3,
        "post_count_90d": 2,
        "reddit_top_snippets": [{"post_id": "t3_1", "title": "snippet", "author": "private"}],
        "reddit_demand_intent_score": None,
    }


def test_validator_rejects_payload_with_empty_keywords_list(tmp_path: Path) -> None:
    session = _session(tmp_path)
    _seed(session)
    payload = _payload()
    payload["keywords"] = []
    summary = write_devvit_reddit_signals(normalize_devvit_payload(payload), session, "empty-keywords")
    assert summary["signals_written"] == 0
    assert summary["keywords_resolved"] == 0
    session.close()


def test_validator_allows_minimal_valid_payload() -> None:
    valid, errors = validate_devvit_payload(
        {
            "schema_version": "reddit_devvit_signal_v1",
            "niche_id": "support_kb_readiness",
            "keywords": ["ai chatbot handoff"],
            "subreddits_searched": [],
            "posts_collected": 0,
            "post_count_90d": 0,
            "reddit_top_snippets": [],
        }
    )
    assert valid is True
    assert errors == []


def test_strip_pii_handles_payload_with_no_snippets() -> None:
    payload = _payload()
    payload.pop("reddit_top_snippets", None)
    payload["username"] = "do_not_store"
    stripped = strip_pii_fields(payload)
    assert "username" not in stripped
    assert "reddit_top_snippets" not in stripped


def test_normalize_post_count_90d_defaults_to_zero_when_missing() -> None:
    payload = _payload()
    payload.pop("reddit_post_count_90d", None)
    normalized = normalize_devvit_payload(payload)
    assert normalized["reddit_post_count_90d"] == 0


def test_devvit_bridge_load_returns_empty_for_empty_dir(tmp_path: Path) -> None:
    import_dir = tmp_path / "imports"
    import_dir.mkdir(parents=True, exist_ok=True)
    loaded = load_devvit_signal_files(import_dir)
    assert loaded == []


def test_write_signals_returns_summary_with_correct_counts(tmp_path: Path) -> None:
    session = _session(tmp_path)
    niche, keyword = _seed(session)
    payload = _payload()
    payload["keywords"] = [str(keyword.keyword), "unknown keyword"]
    payload["niche_id"] = str(niche.slug)
    summary = write_devvit_reddit_signals(normalize_devvit_payload(payload), session, "summary-counts")
    assert summary["signals_written"] == 1
    assert summary["keywords_resolved"] == 1
    assert len(summary["warnings"]) == 1
    session.close()


def test_pii_strip_handles_nested_dict_without_snippets_key() -> None:
    payload = _payload()
    payload["extra_context"] = {"author": "private_user", "metadata": {"username": "secret"}}
    stripped = strip_pii_fields(payload)
    assert "author" in stripped["extra_context"]


def test_normalize_demand_intent_score_preserves_null() -> None:
    payload = _payload()
    payload["reddit_demand_intent_score"] = None
    normalized = normalize_devvit_payload(payload)
    assert normalized["reddit_demand_intent_score"] is None


def test_keyword_resolver_none_when_niche_missing(tmp_path: Path) -> None:
    session = _session(tmp_path)
    _seed(session)
    resolved = resolve_keyword_id("missing_niche", "AI chatbot handoff", session)
    assert resolved is None
    session.close()
