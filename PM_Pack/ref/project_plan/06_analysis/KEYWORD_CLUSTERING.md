# Keyword Clustering
# Fiverr Research System — Wave 5

**Document Status:** Complete
**Wave:** 5 — Analysis and Competitor Model
**Purpose:** Embedding pipeline, algorithm selection, cluster count heuristic, LLM labeling integration, opportunity narrative design, cross-niche clustering decision, and re-clustering logic.

---

## Design Goals

1. Group semantically related keywords into clusters so research is organized by theme, not as a flat list of hundreds of terms
2. Every cluster gets a human-readable label (LLM-generated) and a strategic opportunity narrative (LLM-generated)
3. Clustering runs per-niche — each niche has its own independent cluster set
4. Clusters are stable between runs unless significant new keywords are added
5. The clustering pipeline feeds directly into competitor synthesis (Stage 8) and scoring (Stage 10)

---

## Embedding Pipeline

Embeddings are generated in Stage 2 (Keyword Expansion) and stored in `keywords.embedding_vector` as a JSON array of 1536 floats. The clustering module reads these vectors at Stage 9.

```python
# src/analysis/keyword_clusterer.py — embedding loading step

import numpy as np
from sqlalchemy import select

def load_embeddings_for_niche(niche_id: str, db) -> tuple[list[int], np.ndarray]:
    """
    Loads keyword IDs and their embedding vectors for a given niche.
    Skips keywords with null embedding_vector (feasibility depth or embedding failure).

    Returns:
        keyword_ids: list of keyword primary keys
        matrix: numpy array of shape (n_keywords, 1536)
    """
    rows = db.execute(
        select(Keyword.id, Keyword.embedding_vector)
        .where(
            Keyword.niche_id == niche_id,
            Keyword.is_active == True,
            Keyword.embedding_vector.isnot(None),
        )
    ).fetchall()

    if not rows:
        return [], np.array([])

    keyword_ids = [row.id for row in rows]
    matrix = np.array([row.embedding_vector for row in rows], dtype=np.float32)
    return keyword_ids, matrix
```

### Embedding Vector Normalization

Before clustering, vectors are L2-normalized. This makes cosine similarity equivalent to Euclidean distance and improves KMeans performance on embedding vectors.

```python
from sklearn.preprocessing import normalize

def normalize_embeddings(matrix: np.ndarray) -> np.ndarray:
    """L2-normalize embedding vectors for cosine-distance clustering."""
    return normalize(matrix, norm="l2")
```

---

## Algorithm Selection

### Default: KMeans

KMeans is the default clustering algorithm because:
- Fast and deterministic (with fixed `random_state`)
- Works well with L2-normalized embeddings
- Produces compact, interpretable clusters
- Cluster count is controllable

```python
from sklearn.cluster import KMeans

def run_kmeans(matrix: np.ndarray, n_clusters: int) -> np.ndarray:
    """
    Runs KMeans clustering on the embedding matrix.
    Returns cluster label array (0-indexed, length = n_keywords).
    """
    kmeans = KMeans(
        n_clusters=n_clusters,
        init="k-means++",      # Smarter initialization — faster convergence
        n_init=10,             # 10 random initializations, pick best
        max_iter=300,
        random_state=42,       # Reproducible results
        algorithm="lloyd",     # Standard KMeans algorithm
    )
    labels = kmeans.fit_predict(matrix)
    return labels, kmeans.inertia_
```

### Alternative: DBSCAN

DBSCAN is available as a config option for niches where the keyword universe is large and density-based clustering would produce more natural groupings. It does not require specifying the number of clusters upfront.

```python
from sklearn.cluster import DBSCAN

def run_dbscan(matrix: np.ndarray, eps: float = 0.3, min_samples: int = 3) -> np.ndarray:
    """
    Runs DBSCAN clustering.
    eps: maximum distance between points to be considered neighbors
    min_samples: minimum cluster size
    Returns cluster labels (-1 = noise/unclustered)
    """
    dbscan = DBSCAN(
        eps=eps,
        min_samples=min_samples,
        metric="euclidean",    # Works with L2-normalized embeddings
        n_jobs=-1,
    )
    labels = dbscan.fit_predict(matrix)
    return labels, None  # No inertia for DBSCAN
```

**When to use DBSCAN:**
- Niche has > 300 keywords (large keyword universe)
- Many long-tail keywords that don't fit neatly into K groups
- Set in config.yaml: `clustering.algorithm: dbscan`

---

## Cluster Count Heuristic (KMeans Auto Mode)

When `config.clustering.n_clusters_per_niche = "auto"`, the system calculates the optimal cluster count:

```python
import math

def calculate_n_clusters(n_keywords: int) -> int:
    """
    Auto cluster count heuristic: ceil(sqrt(n_keywords / 2))
    
    Rationale: Square root heuristic is well-established for KMeans.
    Dividing by 2 gives slightly fewer, larger clusters — better for
    the small-to-medium keyword universes in these niches (50–300 keywords).
    
    Examples:
        50 keywords  → 5 clusters
        100 keywords → 7 clusters
        200 keywords → 10 clusters
        300 keywords → 12 clusters
    
    Floor and ceiling bounds prevent degenerate cases:
        < 20 keywords → 2 clusters minimum
        > 500 keywords → 20 clusters maximum
    """
    raw = math.ceil(math.sqrt(n_keywords / 2))
    return max(2, min(raw, 20))
```

---

## Cluster Quality Metrics

After clustering, quality metrics are logged to the run summary and stored in `cluster_analysis`:

```python
from sklearn.metrics import silhouette_score

def compute_cluster_quality(matrix: np.ndarray, labels: np.ndarray) -> dict:
    """
    Computes clustering quality metrics.
    Both metrics are logged per run in run_logs.
    """
    # Silhouette score: -1 (poor) to +1 (excellent). > 0.3 is acceptable.
    unique_labels = set(labels) - {-1}  # Exclude DBSCAN noise
    if len(unique_labels) < 2:
        return {"silhouette_score": None, "inertia": None, "n_clusters": len(unique_labels)}

    # Only compute silhouette on non-noise points
    mask = labels != -1
    score = silhouette_score(matrix[mask], labels[mask], sample_size=min(500, mask.sum()))

    return {
        "silhouette_score": round(float(score), 4),
        "n_clusters": len(unique_labels),
        "n_noise_points": int((labels == -1).sum()),  # DBSCAN only
    }
```

**Quality thresholds (logged in run summary):**
- Silhouette > 0.5: Excellent clustering — topics are well-separated
- Silhouette 0.3–0.5: Good clustering — acceptable for most niches
- Silhouette 0.1–0.3: Weak clustering — consider increasing n_clusters or switching to DBSCAN
- Silhouette < 0.1: Poor clustering — keyword universe may be too broad or too small

---

## Cluster Theme Labeling (LLM, gpt-4o-mini)

After clustering, the system identifies representative keywords per cluster and sends them to gpt-4o-mini for human-readable label generation.

### Representative Keyword Selection

```python
def get_representative_keywords(
    keyword_ids: list[int],
    labels: np.ndarray,
    matrix: np.ndarray,
    cluster_id: int,
    top_n: int = 7,
) -> list[str]:
    """
    Returns the top_n keywords closest to the cluster centroid.
    These are the most representative of the cluster's theme.
    """
    cluster_mask = labels == cluster_id
    cluster_indices = np.where(cluster_mask)[0]
    cluster_matrix = matrix[cluster_indices]

    centroid = cluster_matrix.mean(axis=0)
    distances = np.linalg.norm(cluster_matrix - centroid, axis=1)
    sorted_indices = cluster_indices[np.argsort(distances)][:top_n]

    return [get_keyword_text(keyword_ids[i]) for i in sorted_indices]
```

### LLM Label Generation

```
Prompt template: src/llm/prompts/stage09_clustering/cluster_labeling.j2

---
You are analyzing keyword clusters for a Fiverr gig research system.

Niche: {{ niche_name }}
Cluster keywords (most representative first):
{% for kw in representative_keywords %}
- {{ kw }}
{% endfor %}

Generate a concise, descriptive cluster label (4–8 words) that captures the common
theme of these keywords. The label should be useful for a Fiverr seller deciding
which gig topics to target.

Format: Return ONLY the label text. No explanation. No quotes.

Examples of good labels:
- "PRD — MVP Scoping and Feature Definition"
- "Python Automation — Web Scraping Scripts"
- "AI Agent — LangChain and CrewAI Development"
---

Expected output: "PRD — Technical Roadmap and Architecture"
Stored in: keyword_clusters.cluster_label + cluster_analysis.cluster_label
Model: gpt-4o-mini
Cache: Yes — keyed on representative keywords (stable between runs)
```

---

## Cluster Opportunity Narrative (LLM, gpt-4o)

A strategic paragraph summarizing the opportunity for each cluster. This is one of the most valuable outputs — it tells the user what this cluster means and whether it's worth pursuing.

```
Prompt template: src/llm/prompts/stage09_clustering/cluster_opportunity_narrative.j2

---
You are a Fiverr competitive research analyst. Analyze this keyword cluster and
write a strategic opportunity assessment.

Niche: {{ niche_name }}
Cluster label: {{ cluster_label }}
Representative keywords: {{ representative_keywords | join(", ") }}
Keyword count in cluster: {{ keyword_count }}

Demand signals:
- Average Fiverr search result count: {{ avg_result_count }}
- Google Trends average (12mo): {{ avg_trends_score }}/100
- Trend direction: {{ trend_slope }}
- Reddit demand intent score: {{ reddit_intent_score }}/10

Competition signals:
- Average top-10 gig review count: {{ avg_review_count }}
- Average seller level: {{ avg_seller_level }}
- Pro seller presence: {{ has_pro_sellers }}

Write a 2–3 sentence strategic opportunity narrative covering:
1. What this keyword cluster represents for buyers
2. Whether the competitive landscape suggests an entry opportunity
3. One specific angle a new seller could use

Be direct and specific. No generic advice.
---

Stored in: cluster_analysis.opportunity_narrative
Model: gpt-4o
Cache: Yes — keyed on demand signals + competition signals (re-runs when data refreshes)
```

---

## Cross-Niche Clustering Decision

**Decision: Cluster per-niche independently. Do NOT cluster across niches.**

Rationale:
1. Keywords from different niches (e.g., "Python automation script" and "AI SaaS PRD") should not be grouped — they serve different buyers and require different gig strategies
2. Cross-niche clustering would dilute the signal by mixing demand contexts
3. Per-niche clusters produce cleaner, more actionable theme labels
4. The dashboard can always show cross-niche keyword similarity if desired later — but clusters stay niche-scoped

Implementation: The `niche_id` field on `keyword_clusters` enforces this. The clustering pipeline iterates over niches independently.

---

## Re-Clustering Logic

Clustering is expensive (embeddings + LLM labels + LLM narratives). It should not re-run on every run unless the keyword universe has meaningfully changed.

```python
def should_recluster(niche_id: str, db) -> bool:
    """
    Returns True if clustering should re-run for this niche.

    Re-cluster when:
    1. No existing clusters for this niche
    2. New keywords added since last clustering > 15% of current total
    3. Config clustering.algorithm or n_clusters has changed
    4. User explicitly sets config.clustering.force_recluster: true
    """
    existing_clusters = db.query(KeywordCluster).filter(
        KeywordCluster.niche_id == niche_id
    ).count()

    if existing_clusters == 0:
        return True  # Never been clustered

    total_keywords = db.query(Keyword).filter(
        Keyword.niche_id == niche_id,
        Keyword.is_active == True,
        Keyword.embedding_vector.isnot(None),
    ).count()

    unclustered = db.query(Keyword).filter(
        Keyword.niche_id == niche_id,
        Keyword.is_active == True,
        Keyword.embedding_vector.isnot(None),
        Keyword.cluster_id.is_(None),
    ).count()

    new_keyword_ratio = unclustered / max(1, total_keywords)
    if new_keyword_ratio > 0.15:  # > 15% new keywords
        return True

    if config.clustering.force_recluster:
        return True

    return False
```

When clustering does NOT re-run, newly added keywords without a cluster_id are assigned to the nearest existing cluster centroid using a nearest-neighbor lookup — no full re-run needed.

---

## Full Clustering Orchestrator

```python
# src/analysis/keyword_clusterer.py

async def run_clustering_for_niche(niche_id: str, config, db, llm_client, cache):
    """
    Orchestrates the full clustering pipeline for one niche.
    Called at Stage 9 for all niches with depth != keyword_only.
    """
    if not should_recluster(niche_id, db):
        # Assign new keywords to nearest existing cluster
        assign_new_keywords_to_nearest_cluster(niche_id, db)
        return

    keyword_ids, matrix = load_embeddings_for_niche(niche_id, db)
    if len(keyword_ids) < 4:
        log.warning(f"Too few keywords to cluster for {niche_id}: {len(keyword_ids)}")
        return

    matrix_normalized = normalize_embeddings(matrix)
    n_clusters = (
        config.clustering.n_clusters_per_niche
        if config.clustering.n_clusters_per_niche != "auto"
        else calculate_n_clusters(len(keyword_ids))
    )

    if config.clustering.algorithm == "dbscan":
        labels, _ = run_dbscan(matrix_normalized, config.clustering.dbscan_eps,
                                config.clustering.min_cluster_size)
    else:
        labels, inertia = run_kmeans(matrix_normalized, n_clusters)

    quality = compute_cluster_quality(matrix_normalized, labels)
    log.info(f"Clustering {niche_id}: {quality['n_clusters']} clusters, "
             f"silhouette={quality['silhouette_score']}")

    # Write cluster assignments
    write_cluster_assignments(keyword_ids, labels, niche_id, db)

    # Generate labels and narratives for each cluster
    unique_clusters = [c for c in set(labels) if c != -1]
    for cluster_id in unique_clusters:
        rep_keywords = get_representative_keywords(keyword_ids, labels, matrix_normalized, cluster_id)

        # LLM label (gpt-4o-mini, cached)
        label = await generate_cluster_label(niche_id, cluster_id, rep_keywords, llm_client, cache)

        # LLM opportunity narrative (gpt-4o, cached)
        narrative = await generate_cluster_narrative(
            niche_id, cluster_id, label, rep_keywords, db, llm_client, cache
        )

        write_cluster_analysis(niche_id, cluster_id, label, narrative, rep_keywords, db)

    log.info(f"Clustering complete for {niche_id}: {len(unique_clusters)} clusters labeled.")
```
