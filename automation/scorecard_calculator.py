"""
scorecard_calculator.py â€” Calculate two-score model after each cycle.
Score 1: Internal Engineering Build Progress
Score 2: E2E Production-Grade Readiness (always <= Score 1)
"""
from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path

REPO_ROOT = Path(__file__).parent.parent
PM_PACK = REPO_ROOT / "PM_Pack"


@dataclass
class ScoreCard:
    cycle: int
    score1_internal: float   # Engineering build progress %
    score2_e2e: float        # E2E production-grade readiness %
    tierd2_status: str       # PENDING / IN_PROGRESS / COMPLETE
    tierd2_stages: dict[str, str] = field(default_factory=dict)
    active_score2_caps: list[str] = field(default_factory=list)
    deltas: dict[str, float] = field(default_factory=dict)
    calculated_at: str = ""

    def __post_init__(self) -> None:
        if not self.calculated_at:
            self.calculated_at = datetime.now(UTC).isoformat()
        # Invariant: Score 2 must never exceed Score 1
        if self.score2_e2e > self.score1_internal:
            self.score2_e2e = self.score1_internal

    def to_dict(self) -> dict:
        return {
            "cycle": self.cycle,
            "score1_internal_pct": self.score1_internal,
            "score2_e2e_pct": self.score2_e2e,
            "tierd2_status": self.tierd2_status,
            "tierd2_stages": self.tierd2_stages,
            "active_score2_caps": self.active_score2_caps,
            "score2_lte_score1": self.score2_e2e <= self.score1_internal,
            "deltas": self.deltas,
            "calculated_at": self.calculated_at,
        }


def load_current_scores() -> tuple[float, float]:
    """Read current Score 1 and Score 2 from HYDRATION_HEADER.md."""
    header = PM_PACK / "07_hydration/HYDRATION_HEADER.md"
    if not header.exists():
        return 0.0, 0.0
    text = header.read_text(encoding="utf-8", errors="replace")

    m1 = re.search(r"^INTERNAL_BUILD_PROGRESS:\s*~?(\d+(?:\.\d+)?)%",
                   text, re.MULTILINE)
    # Handle range format: ~48-50% â€” take midpoint
    m2 = re.search(r"^END_TO_END_PRODUCTION_READINESS:\s*~?(\d+(?:\.\d+)?)(?:-(\d+(?:\.\d+)?))?%",
                   text, re.MULTILINE)
    s1 = float(m1.group(1)) if m1 else 0.0
    if m2:
        lo = float(m2.group(1))
        hi = float(m2.group(2)) if m2.group(2) else lo
        s2 = (lo + hi) / 2.0
    else:
        s2 = 0.0
    return s1, s2


def calculate_scorecard(cycle: int,
                         score1_delta: float = 0.0,
                         score2_delta: float = 0.0) -> ScoreCard:
    """
    Calculate updated scorecard based on current scores + cycle deltas.
    Reads current values from HYDRATION_HEADER.
    """
    s1_current, s2_current = load_current_scores()
    s1_new = min(100.0, s1_current + score1_delta)
    s2_new = min(s1_new, s2_current + score2_delta)  # Score 2 cap

    # Check TierD-2 status from hydration
    header = PM_PACK / "07_hydration/HYDRATION_HEADER.md"
    tierd2_status = "PENDING"
    if header.exists():
        text = header.read_text(encoding="utf-8", errors="replace")
        if "TIER_D2: APPROVED" in text:
            tierd2_status = "IN_PROGRESS"
        if "PILOT: COMPLETE" in text.upper():
            tierd2_status = "COMPLETE"

    # Active Score 2 caps (always document these)
    caps = []
    if tierd2_status != "COMPLETE":
        caps.append("~50% hard cap: TierD-2 live pilot not yet completed")
    if s2_new > 50.0 and tierd2_status != "COMPLETE":
        s2_new = 50.0
        caps.append("Score 2 capped at 50.0% (TierD-2 pending)")

    card = ScoreCard(
        cycle=cycle,
        score1_internal=round(s1_new, 1),
        score2_e2e=round(s2_new, 1),
        tierd2_status=tierd2_status,
        active_score2_caps=caps,
        deltas={"score1_delta": score1_delta, "score2_delta": score2_delta},
    )

    # Write scorecard artifact
    out_dir = REPO_ROOT / "PM_Pack/automation/post_cycle_reviews"
    out_dir.mkdir(parents=True, exist_ok=True)
    path = out_dir / f"CYCLE_{cycle:03d}_scorecard.json"
    path.write_text(json.dumps(card.to_dict(), indent=2))

    return card
