"""Stage 9 keyword clustering orchestration and persistence helpers."""

from __future__ import annotations

import hashlib
import json
import logging
import math
from collections import defaultdict
from pathlib import Path
from typing import Any

import numpy as np
from sklearn.cluster import DBSCAN, KMeans
from sklearn.preprocessing import normalize
from sqlalchemy.orm import Session

from src.llm import TemplateRenderer
from src.models.market import Keyword, write_cluster_assignment, write_cluster_label
from src.models.niche import Niche

logger = logging.getLogger(__name__)

_STAGE09_TEMPLATE_RENDERER = TemplateRenderer(
    template_dir=Path(__file__).resolve().parents[1] / "llm" / "templates"
)


def _is_session(db: Any) -> bool:
    return isinstance(db, Session)


def _resolve_niche_pk(niche_id: str, db: Any) -> int | None:
    if niche_id.isdigit():
        return int(niche_id)
    if not _is_session(db):
        return None
    try:
        row = db.query(Niche).filter(Niche.slug == niche_id).one_or_none()
    except Exception:
        return None
    return None if row is None else int(row.id)


def _safe_float_vector(raw_vector: Any) -> list[float] | None:
    vector_payload = raw_vector
    if isinstance(raw_vector, str):
        try:
            vector_payload = json.loads(raw_vector)
        except json.JSONDecodeError:
            return None
    if not isinstance(vector_payload, list):
        return None

    parsed: list[float] = []
    for value in vector_payload:
        if isinstance(value, bool) or not isinstance(value, int | float):
            return None
        parsed.append(float(value))
    return parsed if parsed else None


def load_embeddings_for_niche(niche_id: str, db: Any) -> tuple[list[int], np.ndarray]:
    """
    Load keyword embeddings for a niche.

    Returns `(keyword_ids, matrix)` where matrix shape is `(n, d)` or empty array.
    """
    if not _is_session(db):
        return [], np.array([], dtype=np.float32)

    niche_pk = _resolve_niche_pk(niche_id, db)
    if niche_pk is None:
        return [], np.array([], dtype=np.float32)

    rows = (
        db.query(Keyword.id, Keyword.embedding_vector)
        .filter(
            Keyword.niche_id == niche_pk,
            Keyword.status == "active",
            Keyword.embedding_vector.isnot(None),
        )
        .all()
    )
    if not rows:
        return [], np.array([], dtype=np.float32)

    keyword_ids: list[int] = []
    vectors: list[list[float]] = []
    expected_dims: int | None = None
    for row_id, row_vector in rows:
        vector = _safe_float_vector(row_vector)
        if vector is None:
            logger.warning(
                "Skipping malformed embedding vector niche=%s keyword_id=%s",
                niche_id,
                row_id,
            )
            continue
        if expected_dims is None:
            expected_dims = len(vector)
        if len(vector) != expected_dims:
            logger.warning(
                "Skipping embedding with mismatched dimensions niche=%s keyword_id=%s expected=%s got=%s",
                niche_id,
                row_id,
                expected_dims,
                len(vector),
            )
            continue
        keyword_ids.append(int(row_id))
        vectors.append(vector)

    if not vectors:
        return [], np.array([], dtype=np.float32)
    return keyword_ids, np.array(vectors, dtype=np.float32)


def normalize_embeddings(matrix: np.ndarray) -> np.ndarray:
    """L2-normalize embedding vectors for cosine-distance clustering."""
    if matrix.size == 0:
        return matrix
    return normalize(matrix, norm="l2")


def run_kmeans(matrix: np.ndarray, n_clusters: int) -> tuple[np.ndarray, float]:
    """Run deterministic KMeans and return labels + inertia."""
    model = KMeans(
        n_clusters=n_clusters,
        init="k-means++",
        n_init=10,
        max_iter=300,
        random_state=42,
        algorithm="lloyd",
    )
    labels = model.fit_predict(matrix)
    return labels, model.inertia_


def run_dbscan(matrix: np.ndarray, eps: float = 0.3, min_samples: int = 3) -> tuple[np.ndarray, None]:
    """Run DBSCAN and return labels (`-1` marks noise/unclustered)."""
    model = DBSCAN(
        eps=eps,
        min_samples=min_samples,
        metric="euclidean",
        n_jobs=-1,
    )
    labels = model.fit_predict(matrix)
    return labels, None


def _config_section(config: dict[str, Any], key: str) -> dict[str, Any]:
    section = config.get(key, {}) if isinstance(config, dict) else {}
    return section if isinstance(section, dict) else {}


def _coerce_int(value: Any, default: int) -> int:
    if isinstance(value, bool):
        return default
    if isinstance(value, int):
        return value
    if isinstance(value, float):
        return int(value)
    if isinstance(value, str):
        try:
            return int(float(value))
        except ValueError:
            return default
    return default


def _coerce_float(value: Any, default: float) -> float:
    if isinstance(value, bool):
        return default
    if isinstance(value, int | float):
        return float(value)
    if isinstance(value, str):
        try:
            return float(value)
        except ValueError:
            return default
    return default


def compute_n_clusters(n_keywords: int, config: dict[str, Any]) -> int:
    """Compute auto cluster count using sqrt heuristic with min/max clamps."""
    analysis_cfg = _config_section(config, "analysis")
    clustering_cfg = _config_section(config, "clustering")
    max_clusters = _coerce_int(analysis_cfg.get("max_clusters", clustering_cfg.get("max_clusters", 20)), 20)
    raw = int(math.sqrt(max(1, n_keywords) / 2))
    return max(2, min(raw, max_clusters))


def select_algorithm(config: dict[str, Any]) -> str:
    """Select clustering algorithm from config, defaulting to kmeans."""
    clustering_cfg = _config_section(config, "clustering")
    selected = str(clustering_cfg.get("algorithm", "kmeans")).strip().lower()
    return selected if selected in {"kmeans", "dbscan"} else "kmeans"


def _resolve_depth_for_niche(niche_id: str, config: dict[str, Any]) -> str:
    niches = config.get("niches", []) if isinstance(config, dict) else []
    if isinstance(niches, list):
        for niche in niches:
            if not isinstance(niche, dict):
                continue
            if str(niche.get("niche_id", "")) == niche_id:
                return str(niche.get("depth", "standard")).strip().lower()
    return "standard"


def _extract_niche_ids(config: dict[str, Any]) -> list[str]:
    niches = config.get("niches", []) if isinstance(config, dict) else []
    results: list[str] = []
    if isinstance(niches, list):
        for niche in niches:
            if not isinstance(niche, dict):
                continue
            if niche.get("is_active", True) is False:
                continue
            niche_id = niche.get("niche_id")
            if isinstance(niche_id, str) and niche_id.strip():
                results.append(niche_id.strip())
    return results


def _keyword_text_map(keyword_ids: list[int], db: Any) -> dict[int, str]:
    if not keyword_ids or not _is_session(db):
        return {}
    rows = db.query(Keyword.id, Keyword.keyword).filter(Keyword.id.in_(keyword_ids)).all()
    return {
        row_id: keyword_text
        for row_id, keyword_text in rows
        if isinstance(keyword_text, str) and keyword_text.strip()
    }


async def _resolve_maybe_await(value: Any) -> Any:
    if hasattr(value, "__await__"):
        return await value
    return value


def _cluster_labels_cache_key(niche_id: str, clusters: dict[int, list[str]]) -> str:
    fingerprint = json.dumps(
        {
            "niche_id": niche_id,
            "clusters": {str(cid): sorted(keywords) for cid, keywords in sorted(clusters.items())},
        },
        sort_keys=True,
    )
    digest = hashlib.sha256(fingerprint.encode("utf-8")).hexdigest()
    return f"cluster_labels_v1:{digest}"


async def _cache_get(cache: Any, key: str) -> Any:
    if cache is None or not hasattr(cache, "get"):
        return None
    try:
        return await _resolve_maybe_await(cache.get(key))
    except Exception:
        return None


async def _cache_set(cache: Any, key: str, value: Any) -> None:
    if cache is None or not hasattr(cache, "set"):
        return
    try:
        await _resolve_maybe_await(cache.set(key, value))
        return
    except TypeError:
        pass
    except Exception:
        return

    try:
        await _resolve_maybe_await(
            cache.set(
                key,
                value,
                model="gpt-4o-mini",
                temperature=0.0,
                prompt_text=key,
            )
        )
    except Exception:
        return


def _render_cluster_label_prompt(niche_id: str, keywords: list[str]) -> str:
    return _STAGE09_TEMPLATE_RENDERER.render_template(
        "stage09_clustering/cluster_label.j2",
        {
            "niche_name": niche_id,
            "representative_keywords": keywords,
        },
    )


def _coerce_label_payload(raw_text: str) -> dict[str, str | None]:
    try:
        payload = json.loads(raw_text)
    except json.JSONDecodeError:
        normalized_label = raw_text.strip() or None
        return {
            "label": normalized_label,
            "opportunity_narrative": None,
        }

    if not isinstance(payload, dict):
        return {"label": None, "opportunity_narrative": None}

    label_value = payload.get("label")
    narrative_value = payload.get("opportunity_narrative")
    return {
        "label": label_value.strip() if isinstance(label_value, str) and label_value.strip() else None,
        "opportunity_narrative": (
            narrative_value.strip()
            if isinstance(narrative_value, str) and narrative_value.strip()
            else None
        ),
    }


async def _generate_cluster_labels(
    niche_id: str,
    clusters: dict[int, list[str]],
    llm_client: Any,
    cache: Any,
) -> dict[int, dict[str, str | None]]:
    """
    Generate cluster labels/narratives.

    Returns `{cluster_id: {"label": str|None, "opportunity_narrative": str|None}}`.
    """
    if not clusters:
        return {}

    if llm_client is None:
        return {
            cluster_id: {"label": None, "opportunity_narrative": None}
            for cluster_id in sorted(clusters)
        }

    cache_key = _cluster_labels_cache_key(niche_id, clusters)
    cached_payload = await _cache_get(cache, cache_key)
    if isinstance(cached_payload, dict):
        try:
            return {
                int(cluster_id): {
                    "label": (
                        payload.get("label")
                        if isinstance(payload, dict) and isinstance(payload.get("label"), str | type(None))
                        else None
                    ),
                    "opportunity_narrative": (
                        payload.get("opportunity_narrative")
                        if isinstance(payload, dict)
                        and isinstance(payload.get("opportunity_narrative"), str | type(None))
                        else None
                    ),
                }
                for cluster_id, payload in cached_payload.items()
            }
        except Exception:
            logger.debug("Ignoring malformed cached cluster label payload.", exc_info=True)

    labels: dict[int, dict[str, str | None]] = {}
    for cluster_id, keywords in sorted(clusters.items()):
        prompt = _render_cluster_label_prompt(niche_id, keywords)
        try:
            try:
                completion = llm_client.complete(
                    prompt=prompt,
                    model="gpt-4o-mini",
                    response_format={"type": "json_object"},
                )
            except TypeError:
                completion = llm_client.complete(prompt=prompt, model="gpt-4o-mini")
            response = await _resolve_maybe_await(completion)
            if isinstance(response, str):
                response_text = response
            else:
                response_text = getattr(response, "text", str(response))
            labels[cluster_id] = _coerce_label_payload(str(response_text))
        except Exception as exc:
            logger.warning(
                "Cluster label generation failed niche=%s cluster_id=%s: %s",
                niche_id,
                cluster_id,
                exc,
            )
            labels[cluster_id] = {"label": None, "opportunity_narrative": None}

    await _cache_set(cache, cache_key, labels)
    return labels


def _dbscan_config(config: dict[str, Any]) -> tuple[float, int]:
    clustering_cfg = _config_section(config, "clustering")
    eps = _coerce_float(clustering_cfg.get("eps", clustering_cfg.get("dbscan_eps", 0.3)), 0.3)
    min_samples = _coerce_int(clustering_cfg.get("min_samples", clustering_cfg.get("dbscan_min_samples", 3)), 3)
    return eps, min_samples


async def run_clustering_for_niche(
    niche_id: str,
    run_id: str,
    db: Any,
    config: dict[str, Any],
    llm_client: Any = None,
    cache: Any = None,
) -> dict[str, Any]:
    """Run Stage 9 keyword clustering for one niche."""
    if _resolve_depth_for_niche(niche_id, config) == "feasibility":
        return {
            "niche_id": niche_id,
            "run_id": run_id,
            "clustered": False,
            "reason": "feasibility_depth_skip",
        }

    keyword_ids, matrix = load_embeddings_for_niche(niche_id, db)
    if len(keyword_ids) == 0:
        return {
            "niche_id": niche_id,
            "run_id": run_id,
            "clustered": False,
            "reason": "insufficient_data",
            "n_keywords": 0,
            "n_clusters": 0,
        }

    if len(keyword_ids) == 1:
        if _is_session(db):
            write_cluster_assignment(
                keyword_id=keyword_ids[0],
                niche_id=niche_id,
                cluster_id=0,
                run_id=run_id,
                algorithm="singleton",
                db=db,
                commit=False,
            )
            keyword_row = db.query(Keyword).filter(Keyword.id == keyword_ids[0]).one_or_none()
            if keyword_row is not None:
                keyword_row.cluster_id = 0
            write_cluster_label(
                niche_id=niche_id,
                cluster_id=0,
                run_id=run_id,
                label_text=None,
                opportunity_narrative=None,
                keyword_count=1,
                db=db,
                commit=False,
            )
            db.commit()
        return {
            "niche_id": niche_id,
            "run_id": run_id,
            "clustered": False,
            "reason": "insufficient_data",
            "n_keywords": 1,
            "n_clusters": 1,
            "algorithm": "singleton",
        }

    normalized_matrix = normalize_embeddings(matrix)
    algorithm = select_algorithm(config)

    if algorithm == "dbscan":
        eps, min_samples = _dbscan_config(config)
        labels, _ = run_dbscan(normalized_matrix, eps=eps, min_samples=min_samples)
    else:
        n_clusters = compute_n_clusters(len(keyword_ids), config)
        labels, _ = run_kmeans(normalized_matrix, n_clusters=n_clusters)

    labels = np.asarray(labels, dtype=int)
    label_list = labels.tolist()
    unique_clusters = sorted({label for label in label_list if label != -1})

    keyword_text_by_id = _keyword_text_map(keyword_ids, db)
    cluster_keywords: dict[int, list[str]] = defaultdict(list)
    for keyword_id, label in zip(keyword_ids, label_list, strict=False):
        if label == -1:
            continue
        keyword_text = keyword_text_by_id.get(keyword_id)
        if keyword_text:
            cluster_keywords[int(label)].append(keyword_text)

    label_payload: dict[int, dict[str, str | None]] = await _generate_cluster_labels(
        niche_id=niche_id,
        clusters=dict(cluster_keywords),
        llm_client=llm_client,
        cache=cache,
    )

    if _is_session(db):
        for keyword_id, label in zip(keyword_ids, label_list, strict=False):
            write_cluster_assignment(
                keyword_id=keyword_id,
                niche_id=niche_id,
                cluster_id=int(label),
                run_id=run_id,
                algorithm=algorithm,
                db=db,
                commit=False,
            )
            keyword_row = db.query(Keyword).filter(Keyword.id == keyword_id).one_or_none()
            if keyword_row is not None:
                keyword_row.cluster_id = int(label)

        for cluster_id in unique_clusters:
            generated = label_payload.get(cluster_id, {"label": None, "opportunity_narrative": None})
            write_cluster_label(
                niche_id=niche_id,
                cluster_id=cluster_id,
                run_id=run_id,
                label_text=generated.get("label"),
                opportunity_narrative=generated.get("opportunity_narrative"),
                keyword_count=sum(1 for label in label_list if label == cluster_id),
                db=db,
                commit=False,
            )
        db.commit()

    return {
        "niche_id": niche_id,
        "run_id": run_id,
        "n_keywords": len(keyword_ids),
        "n_clusters": len(unique_clusters),
        "algorithm": algorithm,
        "clustered": True,
    }


async def run_clustering_for_all_niches(
    run_id: str,
    db: Any,
    config: dict[str, Any],
    llm_client: Any = None,
    cache: Any = None,
) -> dict[str, Any]:
    """Run Stage 9 clustering across all active niches in config."""
    results: list[dict[str, Any]] = []
    for niche_id in _extract_niche_ids(config):
        result = await run_clustering_for_niche(
            niche_id=niche_id,
            run_id=run_id,
            db=db,
            config=config,
            llm_client=llm_client,
            cache=cache,
        )
        results.append(result)

    clustered_count = sum(1 for result in results if result.get("clustered") is True)
    return {
        "run_id": run_id,
        "niches_processed": len(results),
        "niches_clustered": clustered_count,
        "results": results,
    }

