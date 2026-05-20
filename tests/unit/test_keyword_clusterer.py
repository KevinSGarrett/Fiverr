"""Unit tests for Stage 9 keyword clustering module."""

from __future__ import annotations

import asyncio
import json
from types import SimpleNamespace
from unittest.mock import AsyncMock

import numpy as np
from sqlalchemy import select
from src.analysis.keyword_clusterer import (
    _generate_cluster_labels,
    compute_n_clusters,
    load_embeddings_for_niche,
    normalize_embeddings,
    run_clustering_for_niche,
    run_dbscan,
    run_kmeans,
)
from src.models.database import create_session_factory, initialize_database
from src.models.market import ClusterAssignment, ClusterLabel, Keyword
from src.models.niche import Niche


def _run(coro):
    return asyncio.run(coro)


def _build_session():
    engine = initialize_database("sqlite:///:memory:")
    session_factory = create_session_factory(engine)
    session = session_factory()
    niche = Niche(slug="ai_saas", name="AI SaaS", category_path="programming-tech/ai")
    session.add(niche)
    session.commit()
    session.refresh(niche)
    return session, niche


def _insert_keyword(
    session,
    niche: Niche,
    keyword_text: str,
    embedding: list[float] | None,
) -> Keyword:
    row = Keyword(
        niche_id=niche.id,
        keyword=keyword_text,
        normalized_keyword=keyword_text.strip().lower(),
        embedding_vector=json.dumps(embedding) if embedding is not None else None,
        external_source="seed",
        metadata_json={},
    )
    session.add(row)
    session.commit()
    session.refresh(row)
    return row


def test_load_embeddings_returns_ids_and_matrix() -> None:
    session, niche = _build_session()
    try:
        row_one = _insert_keyword(session, niche, "ai agent developer", [0.1, 0.2, 0.3])
        row_two = _insert_keyword(session, niche, "ai automation service", [0.4, 0.5, 0.6])
        ids, matrix = load_embeddings_for_niche("ai_saas", session)
        assert ids == [row_one.id, row_two.id]
        assert matrix.shape == (2, 3)
    finally:
        session.close()


def test_load_embeddings_skips_null_vectors() -> None:
    session, niche = _build_session()
    try:
        row = _insert_keyword(session, niche, "valid keyword", [1.0, 2.0])
        _insert_keyword(session, niche, "null vector", None)
        ids, matrix = load_embeddings_for_niche("ai_saas", session)
        assert ids == [row.id]
        assert matrix.shape == (1, 2)
    finally:
        session.close()


def test_load_embeddings_empty_result() -> None:
    session, _niche = _build_session()
    try:
        ids, matrix = load_embeddings_for_niche("ai_saas", session)
        assert ids == []
        assert matrix.size == 0
    finally:
        session.close()


def test_normalize_embeddings_produces_unit_vectors() -> None:
    matrix = np.array([[3.0, 4.0], [5.0, 12.0]], dtype=np.float32)
    normalized = normalize_embeddings(matrix)
    norms = np.linalg.norm(normalized, axis=1)
    assert np.allclose(norms, np.array([1.0, 1.0]), atol=1e-6)


def test_run_kmeans_returns_labels_and_inertia() -> None:
    matrix = np.array([[0.0, 0.0], [0.1, 0.1], [1.0, 1.0], [1.1, 1.1]], dtype=np.float32)
    labels, inertia = run_kmeans(matrix, n_clusters=2)
    assert len(labels) == 4
    assert isinstance(inertia, float)
    assert inertia >= 0.0


def test_run_kmeans_label_count_matches_keywords() -> None:
    matrix = np.array([[0.0, 0.0], [1.0, 1.0], [2.0, 2.0]], dtype=np.float32)
    labels, _ = run_kmeans(matrix, n_clusters=2)
    assert labels.shape[0] == matrix.shape[0]


def test_compute_n_clusters_sqrt_formula() -> None:
    assert compute_n_clusters(100, {"analysis": {"max_clusters": 20}}) == 7


def test_compute_n_clusters_clamped_at_min() -> None:
    assert compute_n_clusters(1, {"analysis": {"max_clusters": 20}}) == 2


def test_compute_n_clusters_clamped_at_max() -> None:
    assert compute_n_clusters(10_000, {"analysis": {"max_clusters": 5}}) == 5


def test_generate_labels_returns_label_per_cluster() -> None:
    llm_client = SimpleNamespace(
        complete=AsyncMock(return_value='{"label":"AI Agents - Build","opportunity_narrative":"Strong demand."}')
    )
    result = _run(
        _generate_cluster_labels(
            niche_id="ai_saas",
            clusters={0: ["ai agent", "agent builder"], 1: ["automation script"]},
            llm_client=llm_client,
            cache=None,
        )
    )
    assert set(result.keys()) == {0, 1}
    assert result[0]["label"] == "AI Agents - Build"


def test_generate_labels_null_when_no_client() -> None:
    result = _run(
        _generate_cluster_labels(
            niche_id="ai_saas",
            clusters={0: ["ai agent"]},
            llm_client=None,
            cache=None,
        )
    )
    assert result == {0: {"label": None, "opportunity_narrative": None}}


def test_generate_labels_api_error_returns_null() -> None:
    llm_client = SimpleNamespace(complete=AsyncMock(side_effect=RuntimeError("llm down")))
    result = _run(
        _generate_cluster_labels(
            niche_id="ai_saas",
            clusters={0: ["ai agent"]},
            llm_client=llm_client,
            cache=None,
        )
    )
    assert result[0]["label"] is None
    assert result[0]["opportunity_narrative"] is None


def test_clustering_skips_insufficient_data() -> None:
    session, _niche = _build_session()
    try:
        result = _run(
            run_clustering_for_niche(
                niche_id="ai_saas",
                run_id="run-insufficient",
                db=session,
                config={"niches": [{"niche_id": "ai_saas", "depth": "standard"}]},
            )
        )
        assert result["clustered"] is False
        assert result["reason"] == "insufficient_data"
    finally:
        session.close()


def test_clustering_skips_at_feasibility_depth() -> None:
    session, niche = _build_session()
    try:
        _insert_keyword(session, niche, "ai agent", [0.1, 0.2, 0.3])
        result = _run(
            run_clustering_for_niche(
                niche_id="ai_saas",
                run_id="run-feasibility",
                db=session,
                config={"niches": [{"niche_id": "ai_saas", "depth": "feasibility"}]},
            )
        )
        assert result["clustered"] is False
        assert result["reason"] == "feasibility_depth_skip"
    finally:
        session.close()


def test_clustering_returns_correct_cluster_count(monkeypatch) -> None:
    session, niche = _build_session()
    try:
        for idx in range(4):
            _insert_keyword(session, niche, f"kw-{idx}", [float(idx), float(idx) + 0.1])

        monkeypatch.setattr(
            "src.analysis.keyword_clusterer.run_kmeans",
            lambda matrix, n_clusters: (np.array([0, 0, 1, 1], dtype=int), 1.23),
        )
        monkeypatch.setattr("src.analysis.keyword_clusterer.compute_n_clusters", lambda _count, _config: 2)

        result = _run(
            run_clustering_for_niche(
                niche_id="ai_saas",
                run_id="run-cluster-count",
                db=session,
                config={"niches": [{"niche_id": "ai_saas", "depth": "standard"}]},
            )
        )
        assert result["clustered"] is True
        assert result["n_clusters"] == 2
    finally:
        session.close()


def test_clustering_updates_keyword_cluster_ids(monkeypatch) -> None:
    session, niche = _build_session()
    try:
        keywords = [
            _insert_keyword(session, niche, f"kw-{idx}", [float(idx), float(idx) + 0.2])
            for idx in range(4)
        ]
        monkeypatch.setattr(
            "src.analysis.keyword_clusterer.run_kmeans",
            lambda matrix, n_clusters: (np.array([0, 0, 1, 1], dtype=int), 0.5),
        )
        monkeypatch.setattr("src.analysis.keyword_clusterer.compute_n_clusters", lambda _count, _config: 2)

        _run(
            run_clustering_for_niche(
                niche_id="ai_saas",
                run_id="run-update-cluster-id",
                db=session,
                config={"niches": [{"niche_id": "ai_saas", "depth": "standard"}]},
            )
        )
        refreshed = session.scalars(select(Keyword).order_by(Keyword.id)).all()
        assert [row.cluster_id for row in refreshed] == [0, 0, 1, 1]
        assert {row.id for row in refreshed} == {keyword.id for keyword in keywords}
    finally:
        session.close()


def test_clustering_handles_single_keyword() -> None:
    session, niche = _build_session()
    try:
        keyword = _insert_keyword(session, niche, "single keyword", [0.1, 0.2, 0.3])
        result = _run(
            run_clustering_for_niche(
                niche_id="ai_saas",
                run_id="run-single",
                db=session,
                config={"niches": [{"niche_id": "ai_saas", "depth": "standard"}]},
            )
        )
        updated = session.get(Keyword, keyword.id)
        assignments = session.scalars(select(ClusterAssignment)).all()
        assert result["clustered"] is False
        assert result["algorithm"] == "singleton"
        assert updated is not None and updated.cluster_id == 0
        assert len(assignments) == 1
        assert assignments[0].cluster_id == 0
    finally:
        session.close()


def test_clustering_handles_dbscan_algorithm(monkeypatch) -> None:
    session, niche = _build_session()
    try:
        for idx in range(3):
            _insert_keyword(session, niche, f"dbscan-{idx}", [float(idx), float(idx) + 0.4])

        called = {"count": 0}

        def _fake_dbscan(matrix: np.ndarray, eps: float = 0.3, min_samples: int = 3):
            _ = (matrix, eps, min_samples)
            called["count"] += 1
            return np.array([0, 0, -1], dtype=int), None

        monkeypatch.setattr("src.analysis.keyword_clusterer.run_dbscan", _fake_dbscan)
        result = _run(
            run_clustering_for_niche(
                niche_id="ai_saas",
                run_id="run-dbscan",
                db=session,
                config={
                    "niches": [{"niche_id": "ai_saas", "depth": "standard"}],
                    "clustering": {"algorithm": "dbscan", "eps": 0.4, "min_samples": 2},
                },
            )
        )
        assert called["count"] == 1
        assert result["algorithm"] == "dbscan"
    finally:
        session.close()


def test_full_clustering_pipeline_dry_run(monkeypatch) -> None:
    session, niche = _build_session()
    try:
        for idx in range(4):
            _insert_keyword(session, niche, f"pipeline-{idx}", [float(idx), float(idx) + 0.3])
        monkeypatch.setattr(
            "src.analysis.keyword_clusterer.run_kmeans",
            lambda matrix, n_clusters: (np.array([0, 0, 1, 1], dtype=int), 0.8),
        )
        monkeypatch.setattr("src.analysis.keyword_clusterer.compute_n_clusters", lambda _count, _config: 2)

        result = _run(
            run_clustering_for_niche(
                niche_id="ai_saas",
                run_id="run-pipeline",
                db=session,
                config={"niches": [{"niche_id": "ai_saas", "depth": "standard"}]},
            )
        )
        assignments = session.scalars(select(ClusterAssignment)).all()
        labels = session.scalars(select(ClusterLabel)).all()
        assert result["clustered"] is True
        assert len(assignments) == 4
        assert len(labels) == 2
    finally:
        session.close()


def test_clustering_writes_to_db(monkeypatch) -> None:
    session, niche = _build_session()
    try:
        for idx in range(3):
            _insert_keyword(session, niche, f"write-{idx}", [float(idx), float(idx) + 0.5])
        monkeypatch.setattr(
            "src.analysis.keyword_clusterer.run_kmeans",
            lambda matrix, n_clusters: (np.array([0, 0, 1], dtype=int), 0.4),
        )
        monkeypatch.setattr("src.analysis.keyword_clusterer.compute_n_clusters", lambda _count, _config: 2)

        calls: list[tuple[int, int]] = []

        def _capture_assignment(*, keyword_id: int, cluster_id: int, **kwargs):
            _ = kwargs
            calls.append((keyword_id, cluster_id))
            return None

        monkeypatch.setattr("src.analysis.keyword_clusterer.write_cluster_assignment", _capture_assignment)

        _run(
            run_clustering_for_niche(
                niche_id="ai_saas",
                run_id="run-write-db",
                db=session,
                config={"niches": [{"niche_id": "ai_saas", "depth": "standard"}]},
            )
        )
        assert len(calls) == 3
    finally:
        session.close()


def test_clustering_updates_keyword_cluster_id(monkeypatch) -> None:
    session, niche = _build_session()
    try:
        rows = [_insert_keyword(session, niche, f"update-{idx}", [float(idx), float(idx) + 0.7]) for idx in range(2)]
        monkeypatch.setattr(
            "src.analysis.keyword_clusterer.run_kmeans",
            lambda matrix, n_clusters: (np.array([0, 1], dtype=int), 0.1),
        )
        monkeypatch.setattr("src.analysis.keyword_clusterer.compute_n_clusters", lambda _count, _config: 2)
        _run(
            run_clustering_for_niche(
                niche_id="ai_saas",
                run_id="run-update-single",
                db=session,
                config={"niches": [{"niche_id": "ai_saas", "depth": "standard"}]},
            )
        )
        updated_rows = [session.get(Keyword, row.id) for row in rows]
        assert [row.cluster_id for row in updated_rows if row is not None] == [0, 1]
    finally:
        session.close()


def test_run_dbscan_returns_labels() -> None:
    matrix = np.array([[0.0, 0.0], [0.1, 0.1], [3.0, 3.0]], dtype=np.float32)
    labels, inertia = run_dbscan(matrix, eps=0.25, min_samples=2)
    assert labels.shape[0] == 3
    assert inertia is None
