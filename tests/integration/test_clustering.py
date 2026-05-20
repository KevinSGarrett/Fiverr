"""Integration tests for Stage 9 clustering persistence."""

from __future__ import annotations

import asyncio
import json

import numpy as np
from sqlalchemy import select

from src.analysis.keyword_clusterer import run_clustering_for_niche
from src.models.database import create_session_factory, initialize_database
from src.models.market import ClusterAssignment, ClusterLabel, Keyword
from src.models.niche import Niche


def _run(coro):
    return asyncio.run(coro)


def _seed_keyword(session, niche: Niche, keyword_text: str, vector: list[float]) -> Keyword:
    row = Keyword(
        niche_id=niche.id,
        keyword=keyword_text,
        normalized_keyword=keyword_text.lower(),
        embedding_vector=json.dumps(vector),
        external_source="seed",
        metadata_json={},
    )
    session.add(row)
    session.commit()
    session.refresh(row)
    return row


def test_clustering_persists_assignments_labels_and_keyword_updates(monkeypatch) -> None:
    engine = initialize_database("sqlite:///:memory:")
    session_factory = create_session_factory(engine)
    session = session_factory()
    try:
        niche = Niche(slug="ai_saas", name="AI SaaS", category_path="programming-tech/ai")
        session.add(niche)
        session.commit()
        session.refresh(niche)

        seeded = [
            _seed_keyword(session, niche, "ai agent builder", [0.1, 0.2, 0.3]),
            _seed_keyword(session, niche, "agent automation", [0.12, 0.21, 0.31]),
            _seed_keyword(session, niche, "mvp roadmap writer", [0.9, 0.8, 0.7]),
            _seed_keyword(session, niche, "product requirement doc", [0.88, 0.82, 0.74]),
        ]

        monkeypatch.setattr(
            "src.analysis.keyword_clusterer.run_kmeans",
            lambda matrix, n_clusters: (np.array([0, 0, 1, 1], dtype=int), 0.77),
        )
        monkeypatch.setattr("src.analysis.keyword_clusterer.compute_n_clusters", lambda _count, _config: 2)

        result = _run(
            run_clustering_for_niche(
                niche_id="ai_saas",
                run_id="integration-run",
                db=session,
                config={"niches": [{"niche_id": "ai_saas", "depth": "standard"}]},
                llm_client=None,
                cache=None,
            )
        )

        assignment_rows = session.scalars(select(ClusterAssignment).order_by(ClusterAssignment.keyword_id)).all()
        label_rows = session.scalars(select(ClusterLabel).order_by(ClusterLabel.cluster_id)).all()
        refreshed_keywords = [session.get(Keyword, row.id) for row in seeded]

        assert result["clustered"] is True
        assert result["n_clusters"] == 2
        assert len(assignment_rows) == 4
        assert len(label_rows) == 2
        assert [row.cluster_id for row in assignment_rows] == [0, 0, 1, 1]
        assert [row.cluster_id for row in refreshed_keywords if row is not None] == [0, 0, 1, 1]
    finally:
        session.close()
