"""Additional branch coverage tests for Reddit Devvit bridge functions."""

from __future__ import annotations

import json
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


def test_validator_rejects_wrong_schema_version() -> None:
    payload = _payload()
    payload["schema_version"] = "reddit_devvit_signal_v0"
    valid, errors = validate_devvit_payload(payload)
    assert valid is False
    assert any("schema_version" in message for message in errors)


def test_validator_rejects_when_required_key_missing() -> None:
    payload = _payload()
    payload.pop("subreddits_searched")
    valid, errors = validate_devvit_payload(payload)
    assert valid is False
    assert any("missing required key: subreddits_searched" == message for message in errors)


def test_normalize_invalid_post_count_coerces_to_zero() -> None:
    payload = _payload()
    payload["reddit_post_count_90d"] = "not-a-number"
    normalized = normalize_devvit_payload(payload)
    assert normalized["reddit_post_count_90d"] == 0


def test_normalize_non_list_snippets_coerces_to_empty_list() -> None:
    payload = _payload()
    payload["reddit_top_snippets"] = {"post_id": "t3_1"}
    normalized = normalize_devvit_payload(payload)
    assert normalized["reddit_top_snippets"] == []


def test_normalize_non_numeric_intent_score_to_none() -> None:
    payload = _payload()
    payload["reddit_demand_intent_score"] = "bad-value"
    normalized = normalize_devvit_payload(payload)
    assert normalized["reddit_demand_intent_score"] is None


def test_strip_pii_removes_root_author_field() -> None:
    payload = _payload()
    payload["author"] = "private_author"
    stripped = strip_pii_fields(payload)
    assert "author" not in stripped


def test_strip_pii_is_idempotent_for_repeated_calls() -> None:
    payload = _payload()
    payload["author"] = "private_author"
    once = strip_pii_fields(payload)
    twice = strip_pii_fields(once)
    assert once == twice


def test_load_files_skips_invalid_json(tmp_path: Path) -> None:
    import_dir = tmp_path / "imports"
    import_dir.mkdir(parents=True, exist_ok=True)
    (import_dir / "bad.json").write_text("{not_json}", encoding="utf-8")
    (import_dir / "good.json").write_text(json.dumps(_payload()), encoding="utf-8")
    loaded = load_devvit_signal_files(import_dir)
    assert len(loaded) == 1


def test_write_signals_with_non_list_keywords_writes_zero(tmp_path: Path) -> None:
    session = _session(tmp_path)
    _seed(session)
    payload = _payload()
    payload["keywords"] = "AI chatbot handoff"
    summary = write_devvit_reddit_signals(normalize_devvit_payload(payload), session, "non-list-keywords")
    assert summary["signals_written"] == 0
    assert summary["keywords_resolved"] == 0
    session.close()


def test_keyword_resolver_returns_none_for_blank_keyword_text(tmp_path: Path) -> None:
    session = _session(tmp_path)
    niche, _ = _seed(session)
    resolved = resolve_keyword_id(str(niche.slug), "   ", session)
    assert resolved is None
    session.close()
