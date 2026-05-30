"""Unit tests for Devvit Reddit bridge payload ingestion."""

from __future__ import annotations

import asyncio
import json
from pathlib import Path
from typing import Any

import pytest
from sqlalchemy import select
from sqlalchemy.orm import Session, sessionmaker

from src.collection.workflows import reddit_signals
from src.collection.workflows.reddit_devvit_bridge import (
    load_devvit_signal_files,
    normalize_devvit_payload,
    resolve_keyword_id,
    run_devvit_bridge_import,
    strip_pii_fields,
    validate_devvit_payload,
    write_devvit_reddit_signals,
)
from src.models import ExternalSignal, Keyword, Niche
from src.models.database import initialize_database


def _run(coro: Any) -> Any:
    return asyncio.run(coro)


def _seed_db(session: Session) -> tuple[Niche, Keyword]:
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


def _session(tmp_path: Path) -> Session:
    db_path = tmp_path / "devvit_bridge_unit.db"
    engine = initialize_database(database_url=f"sqlite:///{db_path.as_posix()}")
    return sessionmaker(bind=engine, future=True)()


def _valid_payload() -> dict[str, Any]:
    return {
        "schema_version": "reddit_devvit_signal_v1",
        "niche_id": "support_kb_readiness",
        "keywords": ["AI chatbot handoff"],
        "subreddits_searched": ["OpenAI"],
        "posts_collected": 1,
        "post_count_90d": 1,
        "reddit_post_count_90d": 1,
        "reddit_top_snippets": [
            {"post_id": "t3_1", "title": "test title", "upvotes": 3, "author": "secret_user", "username": "secret"}
        ],
        "reddit_demand_intent_score": None,
        "confidence_metadata": {"source_confidence": 0.85},
    }


def test_validate_devvit_payload_valid_schema_returns_true() -> None:
    valid, errors = validate_devvit_payload(_valid_payload())
    assert valid is True
    assert errors == []


def test_validate_devvit_payload_wrong_schema_version_returns_false() -> None:
    payload = _valid_payload()
    payload["schema_version"] = "wrong"
    valid, errors = validate_devvit_payload(payload)
    assert valid is False
    assert errors


def test_validate_devvit_payload_missing_required_keys_returns_false() -> None:
    payload = {"schema_version": "reddit_devvit_signal_v1", "niche_id": "x"}
    valid, errors = validate_devvit_payload(payload)
    assert valid is False
    assert any("missing required key" in error for error in errors)


def test_strip_pii_removes_author_field_from_snippets() -> None:
    stripped = strip_pii_fields(_valid_payload())
    assert "author" not in stripped["reddit_top_snippets"][0]


def test_strip_pii_removes_username_from_payload_root() -> None:
    payload = _valid_payload()
    payload["username"] = "abc"
    stripped = strip_pii_fields(payload)
    assert "username" not in stripped


def test_strip_pii_preserves_allowed_fields() -> None:
    stripped = strip_pii_fields(_valid_payload())
    snippet = stripped["reddit_top_snippets"][0]
    assert snippet["post_id"] == "t3_1"
    assert snippet["title"] == "test title"
    assert snippet["upvotes"] == 3


def test_normalize_payload_defaults_missing_reddit_snippets_to_empty_list() -> None:
    payload = _valid_payload()
    payload.pop("reddit_top_snippets")
    normalized = normalize_devvit_payload(payload)
    assert normalized["reddit_top_snippets"] == []


def test_normalize_payload_casts_post_count_to_int() -> None:
    payload = _valid_payload()
    payload["reddit_post_count_90d"] = "7"
    normalized = normalize_devvit_payload(payload)
    assert normalized["reddit_post_count_90d"] == 7


def test_disabled_mode_returns_skipped_status() -> None:
    result = _run(
        reddit_signals.run_reddit_signals_collection(
            niche_id="support_kb_readiness",
            seed_keywords=["AI chatbot handoff"],
            subreddits=["OpenAI"],
            run_id="run",
            db=None,
            pacing_manager=None,
            dry_run=True,
        )
    )
    assert result["status"] == "skipped"
    assert result["signals_written"] == 0


def test_praw_oauth_mode_raises_when_credentials_missing(monkeypatch) -> None:
    monkeypatch.delenv("REDDIT_CLIENT_ID", raising=False)
    monkeypatch.delenv("REDDIT_CLIENT_SECRET", raising=False)
    with pytest.raises(RuntimeError):
        reddit_signals._require_praw_credentials()


def test_devvit_bridge_mode_does_not_require_credentials(tmp_path: Path, monkeypatch) -> None:
    session = _session(tmp_path)
    _seed_db(session)
    import_dir = tmp_path / "imports"
    import_dir.mkdir(parents=True, exist_ok=True)
    (import_dir / "payload.json").write_text(json.dumps(_valid_payload()), encoding="utf-8")
    monkeypatch.setenv("REDDIT_SOURCE_MODE", "devvit_bridge")
    monkeypatch.delenv("REDDIT_CLIENT_ID", raising=False)
    monkeypatch.delenv("REDDIT_CLIENT_SECRET", raising=False)
    monkeypatch.setenv("REDDIT_DEVVIT_IMPORT_DIR", import_dir.as_posix())
    result = _run(
        reddit_signals.run_reddit_signals_collection(
            niche_id="support_kb_readiness",
            seed_keywords=["AI chatbot handoff"],
            subreddits=["OpenAI"],
            run_id="run-1",
            db=session,
            pacing_manager=None,
            dry_run=False,
        )
    )
    assert result["status"] == "ok"
    session.close()


def test_write_devvit_reddit_signals_writes_external_signal_row(tmp_path: Path) -> None:
    session = _session(tmp_path)
    _, keyword = _seed_db(session)
    summary = write_devvit_reddit_signals(normalize_devvit_payload(_valid_payload()), session, "run-2")
    assert summary["signals_written"] == 1
    row = session.execute(select(ExternalSignal).where(ExternalSignal.keyword_id == int(keyword.id))).scalar_one()
    assert row.signal_type == ExternalSignal.SIGNAL_REDDIT_DEMAND
    assert row.collection_method == "reddit_devvit_bridge"
    session.close()


def test_keyword_resolver_returns_none_for_unrecognized_keyword(tmp_path: Path) -> None:
    session = _session(tmp_path)
    _seed_db(session)
    assert resolve_keyword_id("support_kb_readiness", "unknown keyword", session) is None
    session.close()


def test_load_devvit_signal_files_skips_gitkeep(tmp_path: Path) -> None:
    import_dir = tmp_path / "imports"
    import_dir.mkdir(parents=True, exist_ok=True)
    (import_dir / ".gitkeep").write_text("", encoding="utf-8")
    (import_dir / "payload.json").write_text(json.dumps(_valid_payload()), encoding="utf-8")
    loaded = load_devvit_signal_files(import_dir)
    assert len(loaded) == 1


def test_pii_strip_is_idempotent() -> None:
    once = strip_pii_fields(_valid_payload())
    twice = strip_pii_fields(once)
    assert once == twice


def test_run_devvit_bridge_import_aggregates_file_results(tmp_path: Path) -> None:
    session = _session(tmp_path)
    _seed_db(session)
    import_dir = tmp_path / "imports"
    import_dir.mkdir(parents=True, exist_ok=True)
    (import_dir / "payload.json").write_text(json.dumps(_valid_payload()), encoding="utf-8")
    result = run_devvit_bridge_import(
        niche_id="support_kb_readiness",
        seed_keywords=["AI chatbot handoff"],
        run_id="run-3",
        db=session,
        import_dir=import_dir,
    )
    assert result["signals_written"] == 1
    assert result["payload_files"] == 1
    session.close()
