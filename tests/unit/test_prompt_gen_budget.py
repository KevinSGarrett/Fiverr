"""Calibration invariant: the hybrid PM generator's per-agent batch budget must be
large enough to actually REACH the task floor, or every cycle's prompt generation
fails the floor and burns fruitless retries (the cycle-84 live failure: 1800s budget
allowed only ~4 rounds / 29 tasks vs the 55-task floor).

Measured live (cycle-84): at today's required per-task richness (PQ-6 code fence +
src path + verify line, ~511 words/task) Claude authors ~7 task blocks per ~450s
batch call. The budget + round cap must allow reaching MIN_TASKS at that rate. This
guards against re-introducing the budget/floor mismatch — WITHOUT lowering the floor
or weakening the anti-degenerate gates.
"""
from __future__ import annotations

from automation.claude_prompt_creator import (
    GEN_BATCH_BUDGET_S,
    GEN_MAX_BATCH_ROUNDS,
    GEN_TARGET_TASKS,
)
from automation.prompt_validator import MIN_TASKS

# Conservative live measurements (cycle-84). If real yield improves these can rise.
MEASURED_TASKS_PER_ROUND = 7
MEASURED_SECONDS_PER_ROUND = 450


def test_round_cap_can_reach_task_floor():
    # The round cap alone must allow authoring at least MIN_TASKS at the measured rate.
    assert GEN_MAX_BATCH_ROUNDS * MEASURED_TASKS_PER_ROUND >= MIN_TASKS, (
        f"GEN_MAX_BATCH_ROUNDS={GEN_MAX_BATCH_ROUNDS} x ~{MEASURED_TASKS_PER_ROUND} tasks/round "
        f"cannot reach the {MIN_TASKS}-task floor"
    )


def test_budget_allows_enough_rounds_to_reach_floor():
    rounds_needed = MIN_TASKS / MEASURED_TASKS_PER_ROUND
    assert GEN_BATCH_BUDGET_S >= rounds_needed * MEASURED_SECONDS_PER_ROUND, (
        f"GEN_BATCH_BUDGET_S={GEN_BATCH_BUDGET_S}s is too small: reaching the "
        f"{MIN_TASKS}-task floor needs ~{rounds_needed:.1f} rounds x "
        f"{MEASURED_SECONDS_PER_ROUND}s = ~{rounds_needed * MEASURED_SECONDS_PER_ROUND:.0f}s"
    )


def test_target_at_or_above_floor():
    assert GEN_TARGET_TASKS >= MIN_TASKS
