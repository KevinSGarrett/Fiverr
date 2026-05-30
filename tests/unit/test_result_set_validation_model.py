"""Unit tests for ResultSetValidation ORM model."""

from __future__ import annotations

from pathlib import Path

from sqlalchemy import select
from sqlalchemy.orm import Session, sessionmaker
from src.models import Keyword, Niche, ResultSetValidation
from src.models.database import initialize_database


def _session(tmp_path: Path) -> Session:
    db_path = tmp_path / "result_set_validation_model.db"
    engine = initialize_database(database_url=f"sqlite:///{db_path.as_posix()}")
    return sessionmaker(bind=engine, future=True)()


def test_result_set_validation_insert_and_keyword_relationship(tmp_path: Path) -> None:
    session = _session(tmp_path)
    niche = Niche(slug="support_kb_readiness", name="Support KB", category_path="writing-translation")
    session.add(niche)
    session.flush()
    keyword = Keyword(niche_id=int(niche.id), keyword="AI chatbot handoff", normalized_keyword="ai chatbot handoff")
    session.add(keyword)
    session.flush()

    row = ResultSetValidation(
        keyword_id=int(keyword.id),
        run_id="run-rsv",
        result_count=25,
        relevant_count=19,
        sponsored_count=2,
        result_set_relevance_score=0.76,
        ghost_market_flag=False,
        validation_method="rule_based",
        search_strictness_used="NONE",
        relevance_deduction=0.0,
    )
    session.add(row)
    session.commit()

    fetched = session.execute(select(ResultSetValidation)).scalar_one()
    assert fetched.keyword_ref.id == keyword.id
    assert fetched.relevant_count == 19
    session.close()
