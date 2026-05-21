"""Unit tests for demand-score cluster boost integration."""

from __future__ import annotations

import asyncio
import json
from pathlib import Path
from typing import Any

import yaml
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from src.config import ConfigLoader
from src.models import Base, ClusterAssignment, ClusterLabel, Keyword, Niche
from src.scoring.demand import DemandScoreCalculator, get_cluster_demand_boost
from src.scoring.pipeline import score_keyword

KEYWORD_ID = 101


def _base_demand_inputs() -> dict[str, Any]:
    return {
        "total_result_count": 1250,
        "autocomplete_position": 3,
        "trends_12mo_score": 58,
        "reddit_demand_intent_score": 7.2,
    }


def _high_demand_inputs() -> dict[str, Any]:
    return {
        "total_result_count": 100000,
        "autocomplete_position": 1,
        "trends_12mo_score": 100,
        "reddit_demand_intent_score": 10,
    }


def _cluster_config(
    *,
    use_cluster_boost: bool = True,
    cluster_boost: float = 5.0,
    min_cluster_size: int = 3,
) -> dict[str, Any]:
    return {
        "scoring": {
            "demand": {
                "use_cluster_boost": use_cluster_boost,
                "cluster_boost": cluster_boost,
                "min_cluster_size": min_cluster_size,
            }
        }
    }


class FakeDemandDB:
    """In-memory demand + cluster context provider."""

    def __init__(
        self,
        *,
        demand_inputs: dict[int, dict[str, Any]] | None = None,
        cluster_assignments: dict[int, dict[str, Any]] | None = None,
        depth: str = "keyword_only",
    ) -> None:
        self._demand_inputs = demand_inputs or {}
        self._cluster_assignments = cluster_assignments or {}
        self._depth = depth

    def get_demand_inputs(self, keyword_id: int) -> dict[str, Any]:
        return dict(self._demand_inputs.get(keyword_id, {}))

    def get_cluster_assignment(self, keyword_id: int) -> dict[str, Any] | None:
        payload = self._cluster_assignments.get(keyword_id)
        return dict(payload) if isinstance(payload, dict) else None

    def get_keyword_depth(self, keyword_id: int) -> str:
        del keyword_id
        return self._depth

    def get_competition_inputs(self, keyword_id: int) -> dict[str, Any]:
        del keyword_id
        return {"total_result_count": 1000, "llm_competitor_strength_rating": 5.0}


def _build_demand_session() -> tuple[Session, Keyword]:
    engine = create_engine("sqlite+pysqlite:///:memory:", future=True)
    Base.metadata.create_all(engine)
    session = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)()
    niche = Niche(slug="demand-niche", name="Demand Niche", category_path="programming-tech/testing")
    session.add(niche)
    session.flush()
    keyword = Keyword(
        niche_id=niche.id,
        keyword="demand cluster keyword",
        normalized_keyword="demand cluster keyword",
    )
    session.add(keyword)
    session.commit()
    session.refresh(keyword)
    return session, keyword


def _cluster_payload(keyword_count: int = 5) -> dict[str, Any]:
    return {
        "cluster_id": 12,
        "keyword_count": keyword_count,
        "label_text": "Automation Demand",
        "opportunity_narrative": "High-intent automation requests cluster together.",
    }


def test_cluster_boost_returns_zero_when_no_cluster() -> None:
    db = FakeDemandDB(demand_inputs={KEYWORD_ID: _base_demand_inputs()})
    boost = get_cluster_demand_boost(KEYWORD_ID, db, _cluster_config())
    assert boost == 0.0


def test_cluster_boost_reads_session_assignment_and_label() -> None:
    session, keyword = _build_demand_session()
    try:
        session.add(
            ClusterAssignment(
                keyword_id=keyword.id,
                niche_id="demand-niche",
                cluster_id=4,
                run_id="run-demand",
                algorithm="kmeans",
            )
        )
        session.add(
            ClusterLabel(
                niche_id="demand-niche",
                cluster_id=4,
                run_id="run-demand",
                label_text="Demand Cluster",
                opportunity_narrative="High intent cluster.",
                keyword_count=6,
            )
        )
        session.commit()
        boost = get_cluster_demand_boost(
            keyword.id,
            session,
            _cluster_config(cluster_boost=6.5, min_cluster_size=3),
        )
        assert boost == 6.5
    finally:
        session.close()


def test_cluster_boost_session_falls_back_to_label_without_run_match() -> None:
    session, keyword = _build_demand_session()
    try:
        session.add(
            ClusterAssignment(
                keyword_id=keyword.id,
                niche_id="demand-niche",
                cluster_id=5,
                run_id="run-current",
                algorithm="kmeans",
            )
        )
        session.add(
            ClusterLabel(
                niche_id="demand-niche",
                cluster_id=5,
                run_id="run-older",
                label_text="Fallback Label",
                opportunity_narrative="Fallback narrative.",
                keyword_count=7,
            )
        )
        session.commit()
        boost = get_cluster_demand_boost(
            keyword.id,
            session,
            _cluster_config(cluster_boost=5.0, min_cluster_size=3),
        )
        assert boost == 5.0
    finally:
        session.close()


def test_cluster_boost_uses_cluster_context_embedded_in_demand_inputs() -> None:
    class _InlineClusterDB:
        def get_demand_inputs(self, _keyword_id: int) -> dict[str, Any]:
            return {
                **_base_demand_inputs(),
                "cluster_id": 42,
                "cluster_keyword_count": 9,
                "cluster_label_text": "Inline Cluster",
            }

    boost = get_cluster_demand_boost(
        KEYWORD_ID,
        _InlineClusterDB(),
        _cluster_config(cluster_boost=7.0, min_cluster_size=3),
    )
    assert boost == 7.0


def test_cluster_boost_returns_zero_for_small_cluster() -> None:
    db = FakeDemandDB(
        demand_inputs={KEYWORD_ID: _base_demand_inputs()},
        cluster_assignments={KEYWORD_ID: _cluster_payload(keyword_count=2)},
    )
    boost = get_cluster_demand_boost(KEYWORD_ID, db, _cluster_config(min_cluster_size=3))
    assert boost == 0.0


def test_cluster_boost_returns_configured_value() -> None:
    db = FakeDemandDB(
        demand_inputs={KEYWORD_ID: _base_demand_inputs()},
        cluster_assignments={KEYWORD_ID: _cluster_payload(keyword_count=5)},
    )
    boost = get_cluster_demand_boost(KEYWORD_ID, db, _cluster_config(cluster_boost=5.0))
    assert boost == 5.0


def test_cluster_boost_disabled_by_config() -> None:
    db = FakeDemandDB(
        demand_inputs={KEYWORD_ID: _base_demand_inputs()},
        cluster_assignments={KEYWORD_ID: _cluster_payload(keyword_count=8)},
    )
    boost = get_cluster_demand_boost(
        KEYWORD_ID,
        db,
        _cluster_config(use_cluster_boost=False, cluster_boost=9.0),
    )
    assert boost == 0.0


def test_demand_score_includes_cluster_boost() -> None:
    calculator = DemandScoreCalculator()
    clustered_db = FakeDemandDB(
        demand_inputs={KEYWORD_ID: _base_demand_inputs()},
        cluster_assignments={KEYWORD_ID: _cluster_payload(keyword_count=5)},
    )
    unclustered_db = FakeDemandDB(demand_inputs={KEYWORD_ID: _base_demand_inputs()})

    clustered = calculator.calculate(KEYWORD_ID, clustered_db, _cluster_config())
    unclustered = calculator.calculate(KEYWORD_ID, unclustered_db, _cluster_config())

    assert clustered.score_value is not None
    assert unclustered.score_value is not None
    assert clustered.score_value > unclustered.score_value
    assert clustered.score_components["cluster_boost"].value == 5.0


def test_demand_score_clamped_to_100() -> None:
    calculator = DemandScoreCalculator()
    db = FakeDemandDB(
        demand_inputs={KEYWORD_ID: _high_demand_inputs()},
        cluster_assignments={KEYWORD_ID: _cluster_payload(keyword_count=10)},
    )
    result = calculator.calculate(KEYWORD_ID, db, _cluster_config(cluster_boost=8.0))
    assert result.score_value is not None
    assert result.score_value <= 100.0
    assert result.score_value == 100.0


def test_demand_score_explanation_includes_cluster_label() -> None:
    calculator = DemandScoreCalculator()
    db = FakeDemandDB(
        demand_inputs={KEYWORD_ID: _base_demand_inputs()},
        cluster_assignments={KEYWORD_ID: _cluster_payload(keyword_count=6)},
    )
    result = calculator.calculate(KEYWORD_ID, db, _cluster_config(cluster_boost=5.0))
    assert "Keyword belongs to cluster 'Automation Demand'" in result.explanation_text
    assert "Cluster opportunity narrative: High-intent automation requests cluster together." in result.explanation_text


def test_demand_score_explanation_empty_when_no_cluster() -> None:
    calculator = DemandScoreCalculator()
    db = FakeDemandDB(demand_inputs={KEYWORD_ID: _base_demand_inputs()})
    result = calculator.calculate(KEYWORD_ID, db, _cluster_config())
    assert "Keyword belongs to cluster" not in result.explanation_text


def test_demand_score_uses_default_cluster_label_when_missing() -> None:
    calculator = DemandScoreCalculator()
    db = FakeDemandDB(
        demand_inputs={KEYWORD_ID: _base_demand_inputs()},
        cluster_assignments={
            KEYWORD_ID: {
                "cluster_id": 18,
                "keyword_count": 6,
                "label_text": "",
                "opportunity_narrative": "",
            }
        },
    )
    result = calculator.calculate(KEYWORD_ID, db, _cluster_config(cluster_boost=4.0))
    assert "cluster-18" in result.explanation_text


def test_demand_boost_zero_for_unclustered_keyword() -> None:
    calculator = DemandScoreCalculator()
    db = FakeDemandDB(demand_inputs={KEYWORD_ID: _base_demand_inputs()})
    result = calculator.calculate(KEYWORD_ID, db, _cluster_config())
    baseline = calculator.calculate(KEYWORD_ID, db, _cluster_config(use_cluster_boost=False))
    assert result.score_components.get("cluster_boost") is None
    assert get_cluster_demand_boost(KEYWORD_ID, db, _cluster_config()) == 0.0
    assert result.score_value == baseline.score_value


def test_demand_boost_applied_for_well_clustered_keyword() -> None:
    calculator = DemandScoreCalculator()
    db = FakeDemandDB(
        demand_inputs={KEYWORD_ID: _base_demand_inputs()},
        cluster_assignments={KEYWORD_ID: _cluster_payload(keyword_count=10)},
    )
    result = calculator.calculate(KEYWORD_ID, db, _cluster_config(cluster_boost=6.0))
    assert result.score_components["cluster_boost"].value == 6.0


def test_pipeline_persists_cluster_boost_explanation_in_score_components(
    tmp_path: Path,
    monkeypatch: Any,
) -> None:
    from src.scoring import pipeline

    monkeypatch.setattr(pipeline, "_SIDE_CAR_DIR", tmp_path)
    db = FakeDemandDB(
        demand_inputs={KEYWORD_ID: _base_demand_inputs()},
        cluster_assignments={KEYWORD_ID: _cluster_payload(keyword_count=7)},
    )
    result = asyncio.run(
        score_keyword(
            KEYWORD_ID,
            "default",
            db,
            llm_client=None,
            cache=None,
            config=_cluster_config(cluster_boost=5.0),
        )
    )

    details = result["score_components"].get("_demand_score_details")
    assert isinstance(details, dict)
    assert "Keyword belongs to cluster 'Automation Demand'" in str(details.get("note"))

    payload = json.loads((tmp_path / f"{KEYWORD_ID}.json").read_text(encoding="utf-8"))
    persisted_details = payload["score_components"].get("_demand_score_details")
    assert isinstance(persisted_details, dict)
    assert "Keyword belongs to cluster 'Automation Demand'" in str(persisted_details.get("note"))


def test_config_cluster_boost_keys_valid(tmp_path: Path) -> None:
    source = yaml.safe_load(Path("config.yaml").read_text(encoding="utf-8"))
    source.setdefault("scoring", {})
    source["scoring"]["demand"] = {
        "use_cluster_boost": True,
        "cluster_boost": 6.0,
        "min_cluster_size": 4,
    }
    config_path = tmp_path / "config_cluster_boost.yaml"
    config_path.write_text(yaml.safe_dump(source), encoding="utf-8")

    config = ConfigLoader(config_path).load()
    assert config.scoring.demand.use_cluster_boost is True
    assert config.scoring.demand.cluster_boost == 6.0
    assert config.scoring.demand.min_cluster_size == 4
