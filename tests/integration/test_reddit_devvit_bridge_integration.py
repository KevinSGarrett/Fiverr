"""Integration coverage for Reddit Devvit bridge imports."""

from __future__ import annotations

import asyncio
import json
from pathlib import Path
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session, sessionmaker
from src.collection.workflows import reddit_signals
from src.collection.workflows.reddit_devvit_bridge import run_devvit_bridge_import
from src.models import ExternalSignal, Keyword, Niche
from src.models.database import initialize_database


def _run(coro: Any) -> Any:
    return asyncio.run(coro)


def _setup_session(tmp_path: Path) -> Session:
    db_path = tmp_path / "devvit_bridge_integration.db"
    engine = initialize_database(database_url=f"sqlite:///{db_path.as_posix()}")
    return sessionmaker(bind=engine, future=True)()


def _seed_keyword(session: Session) -> None:
    niche = Niche(slug="support_kb_readiness", name="Support KB", category_path="writing-translation")
    session.add(niche)
    session.flush()
    session.add(
        Keyword(
            niche_id=int(niche.id),
            keyword="AI chatbot handoff",
            normalized_keyword="ai chatbot handoff",
        )
    )
    session.commit()


def _payload_with_author() -> dict[str, Any]:
    return {
        "schema_version": "reddit_devvit_signal_v1",
        "niche_id": "support_kb_readiness",
        "keywords": ["AI chatbot handoff"],
        "subreddits_searched": ["OpenAI"],
        "posts_collected": 1,
        "post_count_90d": 1,
        "reddit_post_count_90d": 1,
        "reddit_top_snippets": [{"post_id": "t3_a", "title": "abc", "upvotes": 1, "author": "secret_user"}],
        "reddit_demand_intent_score": None,
        "confidence_metadata": {},
    }


def test_devvit_bridge_import_writes_external_signal_to_db(tmp_path: Path) -> None:
    session = _setup_session(tmp_path)
    _seed_keyword(session)
    import_dir = tmp_path / "imports"
    import_dir.mkdir(parents=True, exist_ok=True)
    (import_dir / "payload.json").write_text(json.dumps(_payload_with_author()), encoding="utf-8")
    run_devvit_bridge_import("support_kb_readiness", ["AI chatbot handoff"], "run-int-1", session, import_dir)
    row = session.execute(select(ExternalSignal)).scalar_one()
    assert row.signal_type == ExternalSignal.SIGNAL_REDDIT_DEMAND
    assert row.collection_method == "reddit_devvit_bridge"
    session.close()


def test_devvit_bridge_import_pii_safe(tmp_path: Path) -> None:
    session = _setup_session(tmp_path)
    _seed_keyword(session)
    import_dir = tmp_path / "imports"
    import_dir.mkdir(parents=True, exist_ok=True)
    (import_dir / "payload.json").write_text(json.dumps(_payload_with_author()), encoding="utf-8")
    run_devvit_bridge_import("support_kb_readiness", ["AI chatbot handoff"], "run-int-2", session, import_dir)
    row = session.execute(select(ExternalSignal)).scalar_one()
    assert "secret_user" not in json.dumps(row.signal_json)
    session.close()


def test_disabled_mode_writes_zero_signals() -> None:
    result = _run(
        reddit_signals.run_reddit_signals_collection(
            niche_id="support_kb_readiness",
            seed_keywords=["AI chatbot handoff"],
            subreddits=["OpenAI"],
            run_id="run-int-3",
            db=None,
            pacing_manager=None,
            dry_run=True,
        )
    )
    assert result["signals_written"] == 0
    assert result["status"] == "skipped"


def test_manual_import_mode_reads_local_json(tmp_path: Path, monkeypatch) -> None:
    session = _setup_session(tmp_path)
    _seed_keyword(session)
    import_dir = tmp_path / "imports"
    import_dir.mkdir(parents=True, exist_ok=True)
    (import_dir / "payload.json").write_text(json.dumps(_payload_with_author()), encoding="utf-8")
    monkeypatch.setenv("REDDIT_SOURCE_MODE", "manual_import")
    monkeypatch.setenv("REDDIT_DEVVIT_IMPORT_DIR", import_dir.as_posix())
    result = _run(
        reddit_signals.run_reddit_signals_collection(
            niche_id="support_kb_readiness",
            seed_keywords=["AI chatbot handoff"],
            subreddits=["OpenAI"],
            run_id="run-int-4",
            db=session,
            pacing_manager=None,
            dry_run=False,
        )
    )
    assert result["signals_written"] == 1
    assert result["source_mode"] == "manual_import"
    session.close()
