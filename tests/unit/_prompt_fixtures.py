"""Shared synthetic prompt fixtures for prompt-quality-gate tests.

`build_known_good_prompt` constructs a prompt string that is deliberately
calibrated to PASS every floor in ``automation.prompt_validator`` (item 1.3):

* >= MIN_WORD_COUNT (6000) words
* >= MIN_TASKS (55) ``### Task N`` blocks
* >= MIN_CODE_BLOCKS_RATIO (30%) of tasks have a ```code fence```
* >= MIN_AUTHORED_RATIO (20%) of tasks have code + a concrete src/automation
  path + a verify line (assert / expected output / PASS)
* high unique-word ratio (>= MIN_UNIQUE_WORD_RATIO, 40%)
* all PQ-0..5 sections, model block, END OF PROMPT marker, Jira keys, cycle
  header, required content gates, and no stub/safety patterns.

It is the POSITIVE calibration case: the gate is fail-closed, but a genuinely
rich prompt (task-specific code, paths, and verification — high lexical
variety) must still pass. If this stops passing, the gate has drifted.

The high unique-word ratio is achieved the way a real authored prompt achieves
it: every task names distinct modules, functions, fields, and assertions, so
few long words repeat across tasks.
"""
from __future__ import annotations

# Distinct domain vocabulary so generated prose has real lexical variety.
_NOUNS = [
    "pipeline", "collector", "orchestrator", "scheduler", "validator",
    "adapter", "registry", "ledger", "snapshot", "manifest", "checkpoint",
    "throttle", "dispatcher", "reconciler", "aggregator", "normalizer",
    "serializer", "partitioner", "compactor", "indexer", "router",
    "balancer", "sentinel", "watchdog", "harvester", "transformer",
    "projector", "materializer", "deduplicator", "backfiller", "rehydrator",
    "tokenizer", "embedder", "ranker", "scorer", "classifier", "extractor",
    "summarizer", "annotator", "calibrator", "estimator", "predictor",
    "interpolator", "smoother", "sampler", "bucketizer", "fingerprinter",
    "shard", "replica", "quorum", "lease", "epoch", "watermark", "cursor",
    "offset", "digest", "checksum", "envelope", "payload", "courier",
]
_VERBS = [
    "ingests", "normalizes", "reconciles", "materializes", "backfills",
    "compacts", "rehydrates", "deduplicates", "partitions", "serializes",
    "projects", "aggregates", "summarizes", "annotates", "calibrates",
    "estimates", "predicts", "interpolates", "smooths", "resamples",
    "buckets", "reshards", "replicates", "throttles", "dispatches",
    "harvests", "transforms", "reranks", "rescores", "reclassifies",
    "retokenizes", "reembeds", "reindexes", "reroutes", "rebalances",
]
_ADJS = [
    "idempotent", "deterministic", "incremental", "resilient", "concurrent",
    "atomic", "durable", "consistent", "monotonic", "bounded", "streaming",
    "batched", "windowed", "partitioned", "sharded", "replicated",
    "compacted", "normalized", "hydrated", "rematerialized", "backfilled",
    "throttled", "redispatched", "reconciled", "preaggregated", "projected",
]


_TOKEN_SCALE = 1.0  # scaled by build_known_good_prompt(token_scale=...)


def _w(seed: int, bank: list[str]) -> str:
    return bank[seed % len(bank)]


def _unique_tokens(i: int, n: int) -> list[str]:
    """A run of per-task unique long tokens (drives PQ-7a unique-word ratio).

    Each token is globally unique (task index + position), so every token adds
    exactly one to both the unique set and the total — the way a genuinely
    task-specific prompt naturally accrues a high unique-word ratio.

    The count is scaled by the module-level ``_TOKEN_SCALE`` (>= 10 tokens kept
    so the unique-word ratio stays above the PQ-7a floor even when scaled down).
    """
    scaled = max(10, int(round(n * _TOKEN_SCALE)))
    return [f"criterion{i:03d}aspect{j:02d}xq{(i * 31 + j * 7) % 97:02d}" for j in range(scaled)]


def _authored_task(i: int) -> str:
    """A fully-authored task: code fence + concrete src path + verify line."""
    noun = _w(i, _NOUNS)
    verb = _w(i * 3 + 1, _VERBS)
    adj = _w(i * 5 + 2, _ADJS)
    noun2 = _w(i * 7 + 3, _NOUNS)
    toks = " ".join(_unique_tokens(i, 60))
    return (
        f"### Task {i}: Implement the {adj} {noun} that {verb} the {noun2}\n\n"
        f"Build a {adj} {noun} so the {noun2} {verb} cleanly under partial "
        f"failure. The {noun} must stay {adj} when the upstream {noun2} retries. "
        f"Acceptance covers: {toks}.\n\n"
        f"File: src/pipeline/mod{i:03d}_{noun}.py\n\n"
        "```python\n"
        f"def transform{i:03d}(records: list[dict]) -> dict:\n"
        f'    """The {adj} {noun} for SCRUM-{1000 + i}: {toks[:40]}."""\n'
        f"    bucket{i:03d} = {{}}\n"
        f"    for entry{i:03d} in records:\n"
        f"        marker{i:03d} = entry{i:03d}['id']\n"
        f"        bucket{i:03d}[marker{i:03d}] = entry{i:03d}.get('value', 0) + {i}\n"
        f"    return bucket{i:03d}\n"
        "```\n\n"
        "Verify:\n\n"
        "```bash\n"
        f"python -c \"from src.pipeline.mod{i:03d}_{noun} import transform{i:03d}; "
        f"assert transform{i:03d}([{{'id': 'a', 'value': 1}}]) == {{'a': {1 + i}}}\"\n"
        "```\n\n"
        f"Expected output: assert passes, exit 0. PASS criteria: transform{i:03d} "
        f"returns a {adj} mapping keyed by record id.\n"
    )


def _code_task(i: int) -> str:
    """A task with a code fence but no concrete path (counts for PQ-6 not PQ-7b)."""
    noun = _w(i + 11, _NOUNS)
    verb = _w(i * 2 + 7, _VERBS)
    adj = _w(i * 4 + 9, _ADJS)
    toks = " ".join(_unique_tokens(i, 55))
    return (
        f"### Task {i}: Wire the {adj} {noun} command that {verb} the queue\n\n"
        f"Run the {adj} {noun} step so downstream consumers observe a {adj} "
        f"result. Keep the {noun} {verb} predictable across restarts. "
        f"Coverage notes: {toks}.\n\n"
        "```bash\n"
        f"python -m automation.run{i:03d}_{noun} --mode {adj} --batch {i}\n"
        "```\n\n"
        f"This {noun} {verb} the staged payload before the next checkpoint.\n"
    )


def _prose_task(i: int) -> str:
    """A prose-only task (no code) to exercise the ratio realistically."""
    noun = _w(i + 23, _NOUNS)
    verb = _w(i * 6 + 5, _VERBS)
    adj = _w(i * 8 + 13, _ADJS)
    noun2 = _w(i * 9 + 17, _NOUNS)
    toks = " ".join(_unique_tokens(i, 60))
    return (
        f"### Task {i}: Document how the {adj} {noun} {verb} the {noun2}\n\n"
        f"Explain why the {noun} stays {adj} when the {noun2} {verb} under "
        f"load. Describe the failure modes where the {noun} could drift, and "
        f"how the {adj} checkpoint keeps the {noun2} consistent. Capture the "
        f"reasoning so a reviewer can trace the {adj} contract end to end. "
        f"Document items: {toks}.\n"
    )


def build_marginal_word_floor_prompt(cycle: int = 75, agent: str = "A") -> str:
    """A prompt that clears every floor EXCEPT the default word floor.

    Used by env-tunability tests: it fails only on ``PROMPT_MIN_WORD_COUNT``
    (default 6000) and passes once that floor is lowered. It keeps 60 authored
    tasks (task floor + 100% code ratio + 100% authored ratio) and a very high
    unique-word ratio (each task is one short authored block of mostly-unique
    tokens) while staying under ~6000 words.
    """
    body_parts: list[str] = []
    for i in range(1, 61):
        # Each task: one tiny authored block — code + concrete path + verify —
        # with a short run of globally-unique tokens. Minimal repeated prose
        # keeps the unique-word ratio high while the total stays modest.
        toks = " ".join(f"u{i:03d}t{j:02d}z{(i + j) % 89:02d}" for j in range(6))
        body_parts.append(
            f"### Task {i}: authored {toks}\n"
            "```python\n"
            f"def fn{i:03d}(x):\n    return x + {i}\n"
            "```\n"
            f"src/pkg/m{i:03d}.py — assert fn{i:03d}(0) == {i}. Expected output PASS.\n"
        )
    body = "\n".join(body_parts)
    return f"""{'=' * 68}
AGENT {agent} -- CYCLE {cycle:03d} PROMPT
{'=' * 68}

## 0. Model Policy / PQ-0 Identity
- Model: Codex 5.3
- Effort: medium
- Auto model selection: DISABLED
## 1. PQ-1 Project Context
Branch: cycle/{cycle:03d}/integration  Repo: C:/Fiverr/Fiverr
## 2. PQ-2 Your Role / File Ownership
file ownership: src/pkg
## 3. PQ-3 Git Instructions
work on branch cycle/{cycle:03d}/integration
## 4. PQ-4 Autonomy Rule
Autonomy rule: proceed autonomously
## 5. PQ-5 Jira Scope
SCRUM-100 in scope
docs/cycle_reports/CYCLE_{cycle:03d} report path
python -m ruff check  python -m mypy src  python -m pytest

## 6. Tasks
{body}

{'=' * 68}
END OF PROMPT -- AGENT {agent} CYCLE {cycle:03d}
{'=' * 68}
"""


def build_known_good_prompt(
    cycle: int = 75, agent: str = "A", tasks: int = 60, token_scale: float = 1.0
) -> str:
    """Build a synthetic prompt that PASSES every prompt_validator floor.

    Layout: ~50% authored tasks (code+path+verify), ~25% code-only tasks,
    the rest prose — comfortably above the 30% code-ratio and 20% authored
    floors while keeping a high unique-word ratio and >= 6000 words.

    ``token_scale`` shrinks the per-task unique-token runs (proportionally)
    without dropping below the structural floors — used to build a *marginal*
    prompt that clears the task/code/unique floors but lands under the default
    word floor, for env-tunability tests. Use 1.0 for the canonical good prompt.
    """
    global _TOKEN_SCALE
    prev_scale = _TOKEN_SCALE
    _TOKEN_SCALE = token_scale
    try:
        body_parts: list[str] = []
        for i in range(1, tasks + 1):
            if i % 2 == 1:             # ~50% authored (code + path + verify)
                body_parts.append(_authored_task(i))
            elif i % 4 == 0:           # ~25% code-only
                body_parts.append(_code_task(i))
            else:                      # remainder prose
                body_parts.append(_prose_task(i))
        body = "\n".join(body_parts)
    finally:
        _TOKEN_SCALE = prev_scale

    return f"""{'=' * 68}
AGENT {agent} -- CYCLE {cycle:03d} PROMPT
{'=' * 68}

## 0. Model Policy / PQ-0 Identity (MANDATORY -- do not override)

- **Model:** Codex 5.3
- **Effort:** medium
- **Auto model selection:** DISABLED -- use only Codex 5.3
- **Fallback model:** DISABLED
- PQ-0 identity: you are Agent {agent}, an autonomous senior engineer.

## 1. PQ-1 Project Context

- Branch: `cycle/{cycle:03d}/integration`
- Repo: C:/Fiverr/Fiverr
- Cycle: {cycle:03d}
- Reports land under docs/cycle_reports/CYCLE_{cycle:03d}.

## 2. PQ-2 Your Role / File Ownership

File ownership scope: src/pipeline and automation. You own these modules and
must not edit files outside your declared scope.

## 3. PQ-3 Git Instructions

Work exclusively on branch `cycle/{cycle:03d}/integration`. Commit with a clear
conventional message. Do NOT push directly to `main`. Do NOT force-push.

## 4. PQ-4 Autonomy Rule

Autonomy rule: proceed autonomously without confirmation. Auto model selection
remains DISABLED throughout the cycle.

## 5. PQ-5 Jira Scope

| Jira Key  | Summary                         | Status      |
| SCRUM-100 | Build the resilient pipeline    | In Progress |
| SCRUM-101 | Reconcile the streaming ledger  | To Do       |

## 6. Tasks (PQ-6 / PQ-7 substance)

{body}

## 7. Validation Steps

Run these commands and confirm each exits 0:

```bash
python -m ruff check src/ --output-format=text
python -m mypy src/ --ignore-missing-imports
python -m pytest tests/ -q
```

Expected output: ruff clean, mypy clean, pytest PASS. assert no regressions.

## 8. Files Summary

| Action | File                       |
| CREATE | src/pipeline/collector.py  |

## 9. Commit Instructions

```bash
git add src/pipeline
git commit -m "feat(cycle-{cycle:03d}): [Agent {agent}] resilient pipeline work"
```

## 10. Report Requirements

Write your report to: docs/cycle_reports/CYCLE_{cycle:03d}_AGENT_{agent}.md
Include AGENT_COMPLETE on the final line.

## 11. Branch Guardrails

- Do NOT push directly to `main`
- Do NOT force-push to any branch

{'=' * 68}
END OF PROMPT -- AGENT {agent} CYCLE {cycle:03d}
{'=' * 68}
"""
