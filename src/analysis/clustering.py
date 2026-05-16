"""Deterministic local keyword clustering for Cycle 003 dry-runs."""

from __future__ import annotations

from itertools import combinations

from src.analysis.contracts import (
    AnalysisEvidence,
    AnalysisReadinessStatus,
    AnalysisWarning,
    ClusterEntry,
    KeywordClusterInput,
    KeywordClusterResult,
)
from src.analysis.keyword_features import normalize_keyword


def _token_set(keyword: str) -> set[str]:
    return set(normalize_keyword(keyword).split())


def _jaccard_similarity(left: set[str], right: set[str]) -> float:
    if not left or not right:
        return 0.0
    shared = left.intersection(right)
    union = left.union(right)
    if not union:
        return 0.0
    return len(shared) / len(union)


def _build_adjacency(token_sets: list[set[str]]) -> list[set[int]]:
    adjacency: list[set[int]] = [set() for _ in token_sets]
    for i, j in combinations(range(len(token_sets)), 2):
        similarity = _jaccard_similarity(token_sets[i], token_sets[j])
        if similarity >= 0.34 or token_sets[i].intersection(token_sets[j]):
            adjacency[i].add(j)
            adjacency[j].add(i)
    return adjacency


def _connected_components(adjacency: list[set[int]]) -> list[list[int]]:
    seen: set[int] = set()
    components: list[list[int]] = []
    for start in range(len(adjacency)):
        if start in seen:
            continue
        stack = [start]
        seen.add(start)
        component: list[int] = []
        while stack:
            node = stack.pop()
            component.append(node)
            for neighbor in sorted(adjacency[node]):
                if neighbor not in seen:
                    seen.add(neighbor)
                    stack.append(neighbor)
        components.append(sorted(component))
    return components


def _cluster_label(component_keywords: list[str]) -> str:
    token_counts: dict[str, int] = {}
    for keyword in component_keywords:
        for token in normalize_keyword(keyword).split():
            token_counts[token] = token_counts.get(token, 0) + 1
    if not token_counts:
        return "misc"
    sorted_tokens = sorted(token_counts.items(), key=lambda item: (-item[1], item[0]))
    return " ".join(token for token, _ in sorted_tokens[:2])


def _cohesion_score(component_indices: list[int], token_sets: list[set[str]]) -> float:
    if len(component_indices) <= 1:
        return 0.5
    scores: list[float] = []
    for i, j in combinations(component_indices, 2):
        scores.append(_jaccard_similarity(token_sets[i], token_sets[j]))
    if not scores:
        return 0.5
    return round(sum(scores) / len(scores), 4)


def cluster_keywords(payload: KeywordClusterInput) -> KeywordClusterResult:
    """Cluster keywords with deterministic token-overlap grouping."""
    warnings: list[AnalysisWarning] = []
    keywords = [keyword for keyword in payload.keywords if normalize_keyword(keyword)]

    if not keywords:
        warnings.append(
            AnalysisWarning(
                code="insufficient_keywords",
                message="No non-empty keywords were provided for clustering.",
                source_id=payload.source_id,
                missing_data_fields=["keywords"],
            )
        )
        return KeywordClusterResult(
            source_id=payload.source_id,
            clusters=[],
            unclustered_keywords=[],
            cluster_metrics={"keyword_count": 0.0, "cluster_count": 0.0, "unclustered_count": 0.0},
            confidence=0.0,
            explanation="Clustering skipped because there were no usable keywords.",
            missing_data_fields=["keywords"],
            warnings=warnings,
            metadata=payload.metadata,
            status=AnalysisReadinessStatus.SKIPPED,
            source_context={"keyword_count": 0, "min_cluster_size": payload.min_cluster_size},
            evidence=[
                AnalysisEvidence(
                    code="keyword_count",
                    message="No usable keywords were available for clustering.",
                    metric=0.0,
                    source_ref="keywords",
                )
            ],
            downstream_readiness={"status": "blocked", "reasons": ["keywords_missing"]},
        )

    token_sets = [_token_set(keyword) for keyword in keywords]

    if len(keywords) < 3:
        warnings.append(
            AnalysisWarning(
                code="too_few_keywords",
                message="Low keyword count reduced clustering quality.",
                source_id=payload.source_id,
                missing_data_fields=["keywords"],
                metadata={"keyword_count": len(keywords)},
            )
        )
        entry = ClusterEntry(
            cluster_id="cluster_01",
            label=_cluster_label(keywords),
            keywords=sorted(keywords),
            size=len(keywords),
            cohesion_score=0.35,
            explanation="Fallback single-cluster output for small keyword set.",
        )
        return KeywordClusterResult(
            source_id=payload.source_id,
            clusters=[entry],
            unclustered_keywords=[],
            cluster_metrics={
                "keyword_count": float(len(keywords)),
                "cluster_count": 1.0,
                "unclustered_count": 0.0,
            },
            confidence=0.35,
            explanation="Generated a fallback cluster because keyword count was too low.",
            missing_data_fields=[],
            warnings=warnings,
            metadata=payload.metadata,
            status=AnalysisReadinessStatus.PARTIAL,
            source_context={"keyword_count": len(keywords), "min_cluster_size": payload.min_cluster_size},
            evidence=[
                AnalysisEvidence(
                    code="fallback_single_cluster",
                    message="Single fallback cluster created from sparse keyword set.",
                    metric=float(len(keywords)),
                    source_ref="keywords",
                )
            ],
            downstream_readiness={"status": "partial", "reasons": ["too_few_keywords"]},
        )

    adjacency = _build_adjacency(token_sets)
    components = _connected_components(adjacency)
    components = sorted(
        components,
        key=lambda component: (-len(component), _cluster_label([keywords[i] for i in component])),
    )
    clusters: list[ClusterEntry] = []
    unclustered_keywords: list[str] = []
    for index, component in enumerate(components, start=1):
        cluster_keywords_list = sorted(keywords[i] for i in component)
        label = _cluster_label(cluster_keywords_list)
        cohesion = _cohesion_score(component, token_sets)
        if len(component) < payload.min_cluster_size:
            unclustered_keywords.extend(cluster_keywords_list)
            continue
        clusters.append(
            ClusterEntry(
                cluster_id=f"cluster_{index:02d}",
                label=label,
                keywords=cluster_keywords_list,
                size=len(component),
                cohesion_score=cohesion,
                explanation=f"Grouped by token overlap around '{label}'.",
            )
        )

    if not clusters:
        warnings.append(
            AnalysisWarning(
                code="min_cluster_size_filter",
                message="No clusters met min_cluster_size threshold.",
                source_id=payload.source_id,
                metadata={"min_cluster_size": payload.min_cluster_size},
            )
        )
    elif unclustered_keywords:
        warnings.append(
            AnalysisWarning(
                code="partial_clustering",
                message="Some keywords did not meet clustering threshold and remain unclustered.",
                source_id=payload.source_id,
                missing_data_fields=["unclustered_keywords"],
                metadata={"unclustered_count": len(unclustered_keywords)},
            )
        )

    confidence = round(sum(cluster.cohesion_score for cluster in clusters) / len(clusters), 4) if clusters else 0.2
    return KeywordClusterResult(
        source_id=payload.source_id,
        clusters=clusters,
        unclustered_keywords=sorted(unclustered_keywords),
        cluster_metrics={
            "keyword_count": float(len(keywords)),
            "cluster_count": float(len(clusters)),
            "unclustered_count": float(len(unclustered_keywords)),
        },
        confidence=confidence,
        explanation="Deterministic clustering completed using lexical token overlap.",
        missing_data_fields=[],
        warnings=warnings,
        metadata=payload.metadata,
        status=AnalysisReadinessStatus.READY if clusters else AnalysisReadinessStatus.BLOCKED,
        source_context={"keyword_count": len(keywords), "min_cluster_size": payload.min_cluster_size},
        evidence=[
            AnalysisEvidence(
                code="cluster_count",
                message="Deterministic lexical clustering completed.",
                metric=float(len(clusters)),
                source_ref="keywords",
                metadata={"keyword_count": len(keywords)},
            )
        ],
        downstream_readiness={
            "status": "ready" if clusters else "blocked",
            "reasons": [] if clusters else ["min_cluster_size_filter"],
        },
    )
