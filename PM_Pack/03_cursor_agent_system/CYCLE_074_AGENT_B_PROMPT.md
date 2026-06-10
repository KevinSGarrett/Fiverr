# CYCLE 074 — AGENT B PROMPT (CORRECTED 2026-06-09)
# TierD-2 Hybrid: Sole src/ Implementation Author
# POLICY v4.3 CORRECTED | Floor: 1,200 lines
#
# STATE: C073 COMPLETE | Wave 10: DONE | TierD-2: APPROVED controlled pilot
# Internal Build: ~66% | E2E: ~45% (42-50%) | Cap ~50% until live collection validated
# C074 +5% E2E: collect-live(+2%) + live-validate(+2%) + logger(+1%) = +5% build credit
#
# CODEBASE FACTS:
#   collect-only: dry_run=True (NOT live)   recommendations-only: dry_run=True (NOT live)
#   run --mode full: score_keyword_batch() + run_pricing_stage() (WORKS with live data)
#   ScrapFlyConfig.cost_budget_credits: raises ScrapFlyRateLimitError (ALREADY BUILT)
#   scrapfly.enabled STAYS FALSE in committed config.yaml
#
# HARD GATES (B must pass ALL before committing):
#   G-001: coverage >= 90%
#   G-005: kw=110 62.7/1.0/CONDITIONAL_GO (golden parity unchanged)
#   G-010: zero new migration files
#   G-015: scrapfly.enabled = False in committed config.yaml
#   G-020: src/analysis/visual_analysis.py MUST NOT EXIST (S8.1 deferred to C075)
#   ZONE:  B commits only files listed in B ZONE section

```powershell
function Invoke-Exe { param([string]$File,[string]$ArgString)
  $psi = New-Object System.Diagnostics.ProcessStartInfo
  $psi.FileName=$File; $psi.WorkingDirectory='C:\\Fiverr\\Fiverr'
  $psi.Arguments=$ArgString; $psi.RedirectStandardOutput=$true
  $psi.RedirectStandardError=$true; $psi.UseShellExecute=$false
  $psi.CreateNoWindow=$true; $p=[System.Diagnostics.Process]::Start($psi)
  $o=$p.StandardOutput.ReadToEnd(); $e=$p.StandardError.ReadToEnd()
  $p.WaitForExit(); return [pscustomobject]@{Out=$o;Err=$e;Exit=$p.ExitCode} }
$git='C:\\Program Files\\Git\\cmd\\git.exe'
$python='C:\\Users\\kevin\\AppData\\Local\\Programs\\Python\\Python311\\python.exe'
```

---

## TASK 1 — PREFLIGHT: PULL BRANCH AND VERIFY A COMMITTED
```powershell
Invoke-Exe $git 'pull origin cycle/074/integration'
Invoke-Exe $git 'log --oneline -6'
# Confirm A's commit is visible (docs(cycle074): Agent A corrected)
Invoke-Exe $python 'run.py config-check'
```
A.md must be present in docs/cycle_reports/ before B begins.
B does NOT touch PM_Pack/ — that is A's zone.

---

## TASK 2 — VERIFY STARTING STATE
```python
import ast, os, subprocess, yaml
import sys; sys.path.insert(0,'C:/Fiverr/Fiverr')
# Suite at base
r = subprocess.run(['C:/Users/kevin/AppData/Local/Programs/Python/Python311/python.exe',
    '-m','pytest','--collect-only','-q','tests/unit/','--no-header'],
    cwd='C:/Fiverr/Fiverr', capture_output=True, text=True, timeout=30)
print('Suite at base:', (r.stdout+r.stderr).strip().splitlines()[-1])
# Config
cfg = yaml.safe_load(open('config.yaml', encoding='utf-8'))
scrapfly_enabled = cfg.get('collection',{}).get('scrapfly',{}).get('enabled')
assert not scrapfly_enabled, f'G-015 FAIL: scrapfly.enabled={scrapfly_enabled}'
print(f'scrapfly.enabled={scrapfly_enabled} (must be False) PASS')
# Baseline
mtime = os.path.getmtime('data/cycle037_live.db')
assert abs(mtime - 1780553758) < 10, f'BASELINE TAMPERED: {mtime}'
print(f'Baseline UNTOUCHED: {mtime:.0f}')
# Playbook before
playbook_dir = 'src/playbook'
files = [f for f in os.listdir(playbook_dir) if f.endswith('.py') and f != '__init__.py']
print(f'src/playbook/ before B: {files}')
```

---

## TASK 3 — IMPLEMENT src/collection/pilot_logger.py
Create this file at src/collection/pilot_logger.py:

```python
"""
Persistent request logger for TierD-2 live collection pilot.
Logs every ScrapFly request/response/cost/error to JSONL.
Produces structured evidence bundle at pilot completion.
TierD-2 condition D: log every ScrapFly request, response, cost, error, retry, blocked.
"""
from __future__ import annotations
import json
import logging
import os
from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

log = logging.getLogger(__name__)


@dataclass(slots=True)
class PilotRequestLog:
    timestamp: str
    url: str
    stage: str            # stage03_search | stage04_gig_detail | stage05_seller_profile
    status_code: int
    credits_used: int
    success: bool
    asp_triggered: bool
    error: str | None
    retry_count: int
    blocked: bool


class PilotLogger:
    """Logs every ScrapFly request and builds an evidence bundle."""

    def __init__(self, log_path: str = 'data/live_pilot_log.jsonl') -> None:
        self._path = Path(log_path)
        self._path.parent.mkdir(parents=True, exist_ok=True)
        self._entries: list[PilotRequestLog] = []

    def log_request(
        self, url: str, stage: str, status_code: int, credits_used: int,
        success: bool, asp_triggered: bool = False,
        error: str | None = None, retry_count: int = 0, blocked: bool = False,
    ) -> None:
        entry = PilotRequestLog(
            timestamp=datetime.now(UTC).isoformat(),
            url=url[:200],  # truncate for log safety
            stage=stage, status_code=status_code, credits_used=credits_used,
            success=success, asp_triggered=asp_triggered,
            error=error, retry_count=retry_count, blocked=blocked,
        )
        self._entries.append(entry)
        with open(self._path, 'a', encoding='utf-8') as f:
            f.write(json.dumps(asdict(entry)) + '\n')
        log.debug('PilotLogger: %s %s credits=%d', stage, url[:60], credits_used)

    def write_evidence_bundle(
        self, output_path: str, extra: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Writes evidence JSON and returns the bundle dict."""
        total = len(self._entries)
        total_credits = sum(e.credits_used for e in self._entries)
        total_errors = sum(1 for e in self._entries if e.error)
        total_blocked = sum(1 for e in self._entries if e.blocked)
        block_rate = round(total_blocked / max(1, total), 3)
        error_rate = round(total_errors / max(1, total), 3)
        bundle: dict[str, Any] = {
            'generated_at': datetime.now(UTC).isoformat(),
            'total_requests': total,
            'total_credits_used': total_credits,
            'total_errors': total_errors,
            'block_rate': block_rate,
            'error_rate': error_rate,
            'stop_conditions_triggered': block_rate > 0.5 or error_rate > 0.3,
            'requests_by_stage': {},
            'log_path': str(self._path),
        }
        for entry in self._entries:
            stage_data = bundle['requests_by_stage'].setdefault(
                entry.stage, {'count': 0, 'credits': 0, 'errors': 0, 'blocked': 0})
            stage_data['count'] += 1
            stage_data['credits'] += entry.credits_used
            if entry.error: stage_data['errors'] += 1
            if entry.blocked: stage_data['blocked'] += 1
        if extra:
            bundle.update(extra)
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(bundle, f, indent=2, default=str)
        return bundle
```
Acceptance criteria:
  - PilotLogger importable from src.collection.pilot_logger
  - log_request writes JSONL line to file for each call
  - write_evidence_bundle produces JSON with block_rate, error_rate, stop_conditions_triggered
  - stop_conditions_triggered=True when block_rate > 0.5 or error_rate > 0.3
  - credentials never written to log (URL truncated, no API keys)

---

## TASK 4 — IMPLEMENT src/collection/live_pilot.py
Create this file at src/collection/live_pilot.py:

```python
"""
TierD-2 Live Collection Pilot Orchestrator.
Runs controlled single-niche live collection with cost controls, persistent
logging, and DB persistence validation. All TierD-2 conditions enforced.
"""
from __future__ import annotations
import asyncio
import logging
import uuid
from typing import Any

log = logging.getLogger(__name__)

DEFAULT_BUDGET_CREDITS = 500
PILOT_EVIDENCE_PATH = 'data/live_validation_evidence.json'


async def run_live_collection_pilot(
    niche_id: str,
    budget_credits: int = DEFAULT_BUDGET_CREDITS,
    database_url: str | None = None,
    config_path: str = 'config.yaml',
    log_path: str = 'data/live_pilot_log.jsonl',
    evidence_path: str = PILOT_EVIDENCE_PATH,
) -> dict[str, Any]:
    """
    TierD-2 conditions enforced:
    A. One niche only (config_payload niches filtered to niche_id)
    B. Hard credit ceiling (cost_budget_credits=budget_credits in ScrapFlyConfig)
    C. Persistent logging (PilotLogger writes every request to JSONL)
    D. Stop on budget exceeded, session expired, or block_rate > 50%
    E. Pilot DB separate from production (data/live_pilot_{niche_id}.db)
    Returns structured result dict with all pilot metrics.
    """
    from src.collection.pilot_logger import PilotLogger
    from src.collection.orchestrator import run_collection_pipeline
    from src.collection.scrapfly_client import ScrapFlyRateLimitError
    from src.collection.session_manager import SessionManager
    from src.config import ConfigLoader
    from src.models.database import (
        create_session_factory, get_session,
        initialize_database, normalize_database_url,
    )

    db_url = database_url or f'sqlite:///data/live_pilot_{niche_id}.db'
    result: dict[str, Any] = {
        'run_id': None, 'niche_id': niche_id, 'db_url': db_url,
        'budget_credits': budget_credits, 'success': False,
        'credits_used': 0, 'gigs_collected': 0, 'search_results': 0,
        'keywords_found': 0, 'errors': [], 'stop_reason': None,
        'evidence_path': evidence_path,
    }

    try:
        normalized_url = normalize_database_url(db_url)
        engine = initialize_database(database_url=normalized_url)
        _seed_pilot_niche(niche_id, engine)
        session_factory = create_session_factory(engine)

        config = ConfigLoader(config_path).load()
        config_payload = config.model_dump() if hasattr(config, 'model_dump') else {}

        # TierD-2 runtime overrides (never committed to config.yaml)
        config_payload.setdefault('collection', {})
        config_payload['collection'].setdefault('scrapfly', {})
        config_payload['collection']['scrapfly']['enabled'] = True
        config_payload['collection']['scrapfly']['cost_budget_credits'] = budget_credits

        # Scope to ONE niche only
        all_niches = config_payload.get('niches', [])
        if isinstance(all_niches, list):
            config_payload['niches'] = [
                n for n in all_niches
                if isinstance(n, dict) and n.get('niche_id') == niche_id
            ]

        logger = PilotLogger(log_path=log_path)
        run_id = f'pilot-{niche_id}-{uuid.uuid4().hex[:8]}'
        result['run_id'] = run_id

        session_manager = SessionManager(config)
        try:
            await session_manager.ensure_session()
        except Exception as exc:
            result['errors'].append(f'Session error: {exc}')
            result['stop_reason'] = 'session_expired'
            return result
        finally:
            pass

        try:
            with get_session(session_factory) as db:
                pilot_summary = await run_collection_pipeline(
                    run_id=run_id,
                    db=db,
                    config=config_payload,
                    session_manager=session_manager,
                    dry_run=False,
                )
            result['success'] = True
            result['errors'] = pilot_summary.get('errors', [])
            result['gigs_collected'] = pilot_summary.get('gig_detail_jobs_run', 0)
            result['search_results'] = pilot_summary.get('search_jobs_run', 0)
        except ScrapFlyRateLimitError as exc:
            result['errors'].append(str(exc))
            result['stop_reason'] = 'budget_exceeded'
        except Exception as exc:
            result['errors'].append(str(exc))
            result['stop_reason'] = 'pipeline_error'
        finally:
            await session_manager.close()

    except Exception as exc:
        result['errors'].append(f'Setup error: {exc}')
        result['stop_reason'] = 'setup_error'

    # Write evidence bundle ALWAYS (even on failure)
    from src.collection.pilot_logger import PilotLogger
    try:
        logger_obj = PilotLogger(log_path=log_path) if 'logger' not in dir() else logger
        evidence = logger_obj.write_evidence_bundle(evidence_path, extra=result)
        result['credits_used'] = evidence.get('total_credits_used', 0)
    except Exception:
        pass

    return result


def _seed_pilot_niche(niche_id: str, engine: Any) -> None:
    """Seeds the target niche into pilot DB from config.yaml if not present."""
    from src.models.database import create_session_factory, get_session
    from src.models.niche import Niche
    from src.config import ConfigLoader
    session_factory = create_session_factory(engine)
    config = ConfigLoader('config.yaml').load()
    config_payload = config.model_dump() if hasattr(config, 'model_dump') else {}
    niche_cfg = next(
        (n for n in config_payload.get('niches', [])
         if isinstance(n, dict) and n.get('niche_id') == niche_id), {}
    )
    with get_session(session_factory) as db:
        existing = db.query(Niche).filter(Niche.slug == niche_id).first()
        if existing is None:
            db.add(Niche(
                slug=niche_id,
                name=niche_cfg.get('name', niche_id.replace('_', ' ').title()),
                category_path=niche_cfg.get('category_path', 'uncategorized'),
                is_active=True,
            ))
            db.commit()
            log.info('Seeded pilot niche: %s', niche_id)
```
Acceptance criteria:
  - run_live_collection_pilot importable from src.collection.live_pilot
  - Returns {success=False, stop_reason='session_expired'} when ensure_session raises
  - Returns {stop_reason='budget_exceeded'} when ScrapFlyRateLimitError raised
  - Evidence bundle written EVEN when pipeline fails
  - db_url never equals 'sqlite:///data/cycle037_live.db'

---

## TASK 5 — ADD collect-live COMMAND TO run.py
Find the existing collect-only command in run.py and add collect-live immediately after it:

```python
@cli.command('collect-live')
@click.option('--niche', 'niche_id', required=True,
              help='Niche ID for live collection. ONE niche only (TierD-2 condition A).')
@click.option('--budget', 'budget_credits', default=500, show_default=True, type=int,
              help='ScrapFly credit ceiling. Pilot stops automatically when reached.')
@click.option('--database-url', default=None,
              help='Pilot DB URL. Default: sqlite:///data/live_pilot_{niche}.db')
@click.option('--config-path', default='config.yaml', show_default=True)
@click.option('--log-path', default='data/live_pilot_log.jsonl', show_default=True,
              help='JSONL file for per-request ScrapFly logging (TierD-2 condition C).')
@click.option('--evidence-path', default='data/live_validation_evidence.json',
              show_default=True)
def collect_live_command(
    niche_id: str, budget_credits: int, database_url: str | None,
    config_path: str, log_path: str, evidence_path: str,
) -> None:
    """
    Run CONTROLLED live collection for ONE niche using ScrapFly.

    TierD-2 approval conditions enforced:
    - One niche only (--niche required, no default)
    - Hard credit ceiling (--budget, default 500 credits)
    - Every ScrapFly request logged to --log-path (JSONL)
    - Evidence bundle written to --evidence-path on completion or failure
    - Auto-stops: budget exceeded, block rate > 50%, error rate > 30%

    Prerequisites:
      SCRAPFLY_API_KEY environment variable set
      Valid Fiverr session: python run.py relogin

    Example (minimal test): python run.py collect-live --niche python_automation --budget 100
    """
    from src.collection.live_pilot import run_live_collection_pilot
    click.echo(f'Starting live collection pilot: niche={niche_id} budget={budget_credits} credits')
    click.echo('Prerequisites: SCRAPFLY_API_KEY set + valid session (run relogin if needed)')
    result = asyncio.run(
        run_live_collection_pilot(
            niche_id=niche_id, budget_credits=budget_credits,
            database_url=database_url,
            config_path=normalize_cli_config_path(config_path),
            log_path=log_path, evidence_path=evidence_path,
        )
    )
    if result.get('stop_reason'):
        click.echo(f'Pilot stopped: {result["stop_reason"]}', err=True)
    click.echo(
        f'success={result["success"]} '
        f'credits={result["credits_used"]}/{budget_credits} '
        f'gigs={result["gigs_collected"]} '
        f'searches={result["search_results"]}'
    )
    if result['errors']:
        for err in result['errors'][:3]:
            click.echo(f'  error: {err}', err=True)
    click.echo(f'Evidence: {result.get("evidence_path", evidence_path)}')
    raise SystemExit(0 if result['success'] else 1)
```
Acceptance criteria:
  - 'collect-live' in open('run.py').read()
  - collect-live fails without --niche
  - collect-live --budget defaults to 500
  - CLI exits 0 on success, 1 on failure

---

## TASK 6 — ADD live-validate COMMAND TO run.py
Add the live-validate command and its helper functions to run.py:

```python
@cli.command('live-validate')
@click.option('--niche', 'niche_id', default='python_automation', show_default=True)
@click.option('--budget', 'budget_credits', default=500, type=int)
@click.option('--database-url', default=None)
@click.option('--config-path', default='config.yaml', show_default=True)
@click.option('--skip-collection', is_flag=True, default=False,
              help='Skip collection if already run for this niche and DB exists.')
@click.option('--evidence-path', default='data/live_validation_evidence.json', show_default=True)
def live_validate_command(
    niche_id: str, budget_credits: int, database_url: str | None,
    config_path: str, skip_collection: bool, evidence_path: str,
) -> None:
    """
    Full end-to-end live validation pipeline (TierD-2 controlled pilot).

    Stages:
      1. Pre-flight: check SCRAPFLY_API_KEY and session
      2. Collection: run collect-live (unless --skip-collection)
      3. DB validation: count gigs/keywords/search_results persisted
      4. Scoring: score all keywords in pilot DB
      5. Recommendations: generate from live scores (uses --live flag)
      6. Export: export recommendations to data/exports/live_pilot/
      7. Playbook: generate from live recommendation
      8. Evidence: write complete evidence bundle

    After merge, run:
      python run.py live-validate --niche python_automation
    """
    import json
    from pathlib import Path
    resolved_db = database_url or f'sqlite:///data/live_pilot_{niche_id}.db'
    evidence: dict[str, Any] = {
        'niche_id': niche_id, 'db_url': resolved_db,
        'stages': {}, 'success': False,
    }

    # Stage 1: Pre-flight
    scrapfly_key = os.getenv('SCRAPFLY_API_KEY')
    evidence['stages']['preflight'] = {'scrapfly_key_present': bool(scrapfly_key)}
    if not scrapfly_key and not skip_collection:
        click.echo('ERROR: SCRAPFLY_API_KEY not set. Cannot collect live data.', err=True)
        raise SystemExit(1)

    # Stage 2: Collection
    if not skip_collection:
        click.echo(f'Stage 2: Live collection (niche={niche_id} budget={budget_credits})')
        from src.collection.live_pilot import run_live_collection_pilot
        collect_result = asyncio.run(run_live_collection_pilot(
            niche_id=niche_id, budget_credits=budget_credits,
            database_url=resolved_db,
            config_path=normalize_cli_config_path(config_path),
        ))
        evidence['stages']['collection'] = collect_result
        click.echo(f'  Collected: gigs={collect_result["gigs_collected"]} '
                   f'credits={collect_result["credits_used"]}')
        if not collect_result['success']:
            click.echo(f'  Collection failed: {collect_result.get("stop_reason")}', err=True)
    else:
        click.echo('Stage 2: Skipped (--skip-collection)')

    # Stage 3: DB persistence validation
    click.echo('Stage 3: DB persistence validation')
    db_validation = _validate_pilot_db_state(resolved_db)
    evidence['stages']['db_validation'] = db_validation
    click.echo(f'  gigs={db_validation["gigs"]} keywords={db_validation["keywords"]} '
               f'search_results={db_validation["search_results"]}')

    # Stage 4: Scoring
    click.echo('Stage 4: Scoring live keywords')
    try:
        run_pipeline(
            mode='full',
            config_path=normalize_cli_config_path(config_path),
            database_url=resolved_db,
        )
        evidence['stages']['scoring'] = {'success': True}
    except Exception as exc:
        evidence['stages']['scoring'] = {'success': False, 'error': str(exc)}
        click.echo(f'  Scoring error: {exc}', err=True)

    # Stage 5: Recommendations
    click.echo('Stage 5: Live recommendations')
    recs = _run_live_recommendations(
        normalize_cli_config_path(config_path), resolved_db)
    evidence['stages']['recommendations'] = recs
    click.echo(f'  count={recs.get("count", 0)} dry_run={recs.get("dry_run", True)}')

    # Stage 6: Export
    click.echo('Stage 6: Export recommendations')
    export_dir = 'data/exports/live_pilot'
    evidence['stages']['export'] = {'dir': export_dir}

    # Stage 7: Playbook
    click.echo('Stage 7: Playbook from live recommendation')
    playbook_result = _generate_playbook_from_live_data(niche_id, resolved_db)
    evidence['stages']['playbook'] = playbook_result
    click.echo(f'  has_full_data={playbook_result.get("has_full_data")} '
               f'sections={playbook_result.get("sections_count")}')

    # Stage 8: Write evidence bundle
    evidence['success'] = (
        evidence['stages'].get('db_validation', {}).get('gigs', 0) > 0
        and evidence['stages'].get('scoring', {}).get('success', False)
    )
    Path(evidence_path).parent.mkdir(parents=True, exist_ok=True)
    Path(evidence_path).write_text(
        json.dumps(evidence, indent=2, default=str), encoding='utf-8')
    click.echo(f'Evidence bundle: {evidence_path}')
    click.echo(f'Validation {"PASSED" if evidence["success"] else "PARTIAL"}: {evidence["success"]}')
    raise SystemExit(0)


def _validate_pilot_db_state(db_url: str) -> dict[str, Any]:
    """Counts records in pilot DB to validate persistence."""
    from src.models.database import (
        create_session_factory, get_session, initialize_database, normalize_database_url)
    from src.models.gig import Gig
    from src.models.keyword import Keyword
    from src.models.search_result import SearchResult
    try:
        engine = initialize_database(database_url=normalize_database_url(db_url))
        session_factory = create_session_factory(engine)
        with get_session(session_factory) as db:
            return {
                'gigs': int(db.query(Gig).count()),
                'keywords': int(db.query(Keyword).count()),
                'search_results': int(db.query(SearchResult).count()),
            }
    except Exception as exc:
        return {'gigs': 0, 'keywords': 0, 'search_results': 0, 'error': str(exc)}


def _run_live_recommendations(config_path: str, database_url: str) -> dict[str, Any]:
    """Runs recommendations with dry_run=False if OPENAI_API_KEY available."""
    from src.recommendations.pipeline import run_recommendations_pipeline
    from src.utils.datetime import timestamp_stamp
    config_payload = _load_recommendation_config(config_path)
    live_mode = bool(os.getenv('OPENAI_API_KEY'))
    try:
        llm_client = None
        if live_mode:
            try:
                from src.llm.client import build_llm_client
                llm_client = build_llm_client(config_payload)
            except (ImportError, Exception):
                live_mode = False
        with _recommendation_db_session(database_url) as db:
            result = asyncio.run(run_recommendations_pipeline(
                run_id=timestamp_stamp(), db=db, config=config_payload,
                llm_client=llm_client, cache=None, dry_run=(not live_mode)))
        return {'success': True, 'dry_run': not live_mode, 'result': str(result)}
    except Exception as exc:
        return {'success': False, 'error': str(exc), 'dry_run': True}


def _generate_playbook_from_live_data(niche_id: str, database_url: str) -> dict[str, Any]:
    """Generates a playbook using the best live recommendation for a niche."""
    try:
        from src.playbook.generator import generate_playbook, export_playbook_markdown
        from src.models.database import (
            create_session_factory, get_session, initialize_database, normalize_database_url)
        engine = initialize_database(database_url=normalize_database_url(database_url))
        session_factory = create_session_factory(engine)
        config_payload = _load_recommendation_config()
        with get_session(session_factory) as db:
            playbook = generate_playbook(niche_id, db, config_payload)
        md = export_playbook_markdown(playbook)
        return {
            'success': True, 'niche_id': niche_id,
            'has_full_data': playbook.get('has_full_data', False),
            'sections_count': len(playbook.get('sections', [])),
            'keyword_used': playbook.get('keyword_used'),
            'markdown_length': len(md),
        }
    except Exception as exc:
        return {'success': False, 'error': str(exc)}
```
Acceptance criteria:
  - 'live-validate' in open('run.py').read()
  - live-validate has --skip-collection flag
  - live-validate writes evidence bundle even if scoring fails
  - _validate_pilot_db_state returns {gigs, keywords, search_results}
  - _generate_playbook_from_live_data returns {success, has_full_data, sections_count}

---

## TASK 7 — UPDATE recommendations-only WITH --live FLAG
Find the recommendations-only command in run.py and add the --live flag:

```python
# ADD this option to the existing @click.option decorators:
@click.option('--live', 'live_mode', is_flag=True, default=False,
              help='Pass dry_run=False for real LLM recommendations. '
                   'Requires OPENAI_API_KEY. Falls back to dry_run=True if key missing.')
def recommendations_only_command(config_path: str, database_url: str | None, live_mode: bool) -> None:
    """Run recommendation pipeline. Use --live for real LLM recommendations."""
    from src.recommendations.pipeline import run_recommendations_pipeline
    from src.utils.datetime import timestamp_stamp
    config_payload = _load_recommendation_config(config_path)
    run_id = timestamp_stamp()
    llm_client = None
    actual_live = live_mode
    if live_mode:
        try:
            from src.llm.client import build_llm_client
            llm_client = build_llm_client(config_payload)
            if llm_client is None:
                actual_live = False
                click.echo('Note: OPENAI_API_KEY not set, running dry_run=True', err=True)
        except (ImportError, Exception) as exc:
            actual_live = False
            click.echo(f'Note: LLM client unavailable ({exc}), running dry_run=True', err=True)
    with _recommendation_db_session(database_url) as db:
        result = asyncio.run(
            run_recommendations_pipeline(
                run_id=run_id, db=db, config=config_payload,
                llm_client=llm_client, cache=None, dry_run=(not actual_live),
            )
        )
    mode_label = 'live' if actual_live else 'dry-run'
    click.echo(f'Recommendations ({mode_label}): {result}')
    raise SystemExit(0)
```
Acceptance criteria:
  - 'live_mode' in open('run.py').read()
  - recommendations-only without --live: dry_run=True (unchanged)
  - recommendations-only --live: dry_run=False when OPENAI_API_KEY available

---

## TASK 8 — ENSURE build_llm_client EXISTS IN src/llm/client.py
```python
import os, ast; import sys; sys.path.insert(0,'C:/Fiverr/Fiverr')
llm_path = 'src/llm/client.py'
if os.path.exists(llm_path):
    content = open(llm_path, encoding='utf-8').read()
    tree = ast.parse(content)
    fns = [n.name for n in ast.walk(tree) if isinstance(n, ast.FunctionDef)]
    print(f'src/llm/client.py functions: {fns}')
    if 'build_llm_client' in fns:
        print('build_llm_client: PRESENT')
    else:
        print('build_llm_client: MISSING -- B adds it')
else:
    print(f'{llm_path} not found')
```
If build_llm_client is missing, B adds to src/llm/client.py:

```python
def build_llm_client(config: dict) -> Any | None:
    """Builds an AsyncOpenAI client from OPENAI_API_KEY. Returns None if key missing."""
    import os
    api_key = os.getenv('OPENAI_API_KEY')
    if not api_key:
        return None
    try:
        from openai import AsyncOpenAI
        return AsyncOpenAI(api_key=api_key)
    except ImportError:
        return None
```

---

## TASK 9 — IMPLEMENT src/playbook/generator.py
Create src/playbook/generator.py (~280 lines).
This file is the Wave 11 S8.3 playbook generator scaffold.
It connects to the live pilot via _generate_playbook_from_live_data() in run.py.
When has_full_data=True (real recommendation in pilot DB): uses live data.
When has_full_data=False: returns helpful stub content (placeholder until live data exists).

Required functions and signatures:

def get_niche_name(niche_id: str) -> str:
  Returns human-readable name. Falls back to title-case niche_id.
  Must have all 9 niche IDs mapped.

def generate_playbook(niche_id: str, db: Any, config: Any) -> dict:
  Returns {niche_id, niche_name, generated_at, keyword_used, has_full_data, sections}
  sections: 5 items. Never raises.

def export_playbook_markdown(playbook: dict) -> str:
  Converts playbook to Markdown. Pure Python. No external dependencies.
  Handles steps, strategies, milestones.

def export_playbook_pdf(playbook: dict, output_path: str) -> None:
  WeasyPrint + Jinja2. Raises ImportError with install instructions if WeasyPrint missing.

def render_playbook_section(niche_id: str, db: Any) -> None:
  Streamlit dashboard widget. Must use get_db_session().

def build_account_setup_section(niche_id, profile_opt, profile_patterns) -> dict:
  7 steps. Step 1: CRITICAL profile photo. Graceful {} defaults.

def build_gig_creation_section(recommendation, pricing, visual) -> dict:
  8 steps. Step 8 has checklist. None recommendation -> placeholder options.

def build_first_5_orders_section(niche_id, pricing, buyer_persona) -> dict:
  4 strategies: Buyer Requests (PRIMARY), Search Optimization (SECONDARY),
  Outside Traffic (SUPPLEMENTARY), Pricing Leverage (PRIMARY).
  Plus delivery_excellence_tips list (4+ items).

def build_review_strategy_section(niche_id) -> dict:
  3 strategies: Delivery Message Template, Follow-Up (48hr), Over-Delivery.
  Delivery strategy has string template.

def build_ongoing_optimization_section(pricing) -> dict:
  4 milestones: 5 Reviews, 10 Reviews, 25 Reviews, 50 Reviews.
  Uses pricing['entry_prices'] and pricing['price_ladder'] gracefully.

All functions graceful: empty {} inputs produce valid output, never raise.

---

## TASK 10 — CREATE src/reports/templates/playbook.html (~120 lines)
Create a Jinja2 template for PDF export of the playbook.

Required structure:
  DOCTYPE html, head with CSS, body with:
  - Header section: niche_name, generated_at, keyword_used, has_full_data warning
  - Loop: for section in playbook.sections
    - h2 with section.section name and estimated_time
    - for step in section.steps: h3 with title/action/detail/checklist/guidance
    - for strategy in section.strategies: h3 with strategy/detail/template/tips/rules
    - for milestone in section.milestones: milestone div with actions list
    - for tip in delivery_excellence_tips: excellence list
  - CSS: page-break between sections, milestone div styling, template-box, etc.

Required CSS classes: page-break, milestone, template-box, critical, high, guidance, excellence
Required Jinja2 filters: default ([]), is string, is mapping

---

## TASK 11 — EXTEND RecommendationOutput WITH TWO NEW OPTIONAL FIELDS
Find the file containing class RecommendationOutput and add after pricing_strategy:

```python
# Wave 11 additions
# S8.2 (C076) populates profile_optimization
# S8.1 (C075) populates visual_recommendations
# Both default None until those cycles complete
# Playbook generator handles None gracefully with {} defaults
profile_optimization: Optional[dict] = None
visual_recommendations: Optional[dict] = None

def completeness_ratio(self) -> float:
    # Update denominator from 13 to 14 (or 12 to 14 if pricing_strategy was already added)
    fields = [self.gig_titles, self.tag_sets, self.package_structure,
              self.description_outline, self.faq_entries, self.differentiation_angle,
              self.buyer_persona, self.thumbnail_direction, self.upsell_structure,
              self.red_flags, self.niche_viability_assessment, self.pricing_strategy,
              self.profile_optimization, self.visual_recommendations]
    return sum(1 for f in fields if f is not None) / len(fields)
```
Acceptance criteria:
  - profile_optimization: Optional[dict] = None present in RecommendationOutput
  - visual_recommendations: Optional[dict] = None present
  - No migration required (application-layer fields only)

---

## TASK 12 — ADD playbook COMMAND TO run.py
```python
@cli.command('playbook')
@click.argument('niche_id')
@click.option('--format', 'fmt', type=click.Choice(['markdown', 'pdf']),
              default='markdown', show_default=True)
@click.option('--output', default=None, help='Output path (pdf only)')
@click.option('--database-url', default=None)
def playbook_command(niche_id: str, fmt: str, output: str | None, database_url: str | None) -> None:
    """Generate seller setup playbook for a niche. Example: python run.py playbook python_automation"""
    from src.playbook.generator import generate_playbook, export_playbook_markdown, export_playbook_pdf
    config_payload = _load_recommendation_config()
    with _recommendation_db_session(database_url) as db:
        playbook = generate_playbook(niche_id, db, config_payload)
    if fmt == 'pdf':
        out = output or f'data/exports/pdf/playbook_{niche_id}.pdf'
        export_playbook_pdf(playbook, out)
        click.echo(f'PDF: {out}')
    else:
        click.echo(export_playbook_markdown(playbook))
    raise SystemExit(0)
```

---

## TASK 13 — UPDATE requirements.txt AND .gitignore
```powershell
# Check if scrapfly-sdk in requirements.txt
$req = Get-Content 'requirements.txt' -ErrorAction SilentlyContinue
if ($req -match 'scrapfly') {
    Write-Host "scrapfly-sdk already in requirements.txt"
} else {
    Add-Content 'requirements.txt' 'scrapfly-sdk>=6.0'
    Write-Host "Added scrapfly-sdk>=6.0 to requirements.txt"
}
# Install it
Invoke-Exe $python '-m pip install scrapfly-sdk --quiet'

# Check .gitignore
$gi = Get-Content '.gitignore' -ErrorAction SilentlyContinue
if (-not ($gi -match 'live_pilot')) {
    Add-Content '.gitignore' "`ndata/live_pilot_*.db`ndata/live_pilot_log.jsonl`ndata/live_validation_evidence.json`ndata/exports/live_pilot/"
    Write-Host "Added live pilot patterns to .gitignore"
}
```

---

## TASK 14 — WRITE tests/unit/test_live_pilot.py (18+ tests)
Create tests/unit/test_live_pilot.py with these test classes:

TestPilotLogger (6 tests):
  test_log_request_creates_jsonl_file:
    tmp_path, logger = PilotLogger(str(tmp/log.jsonl))
    logger.log_request('http://test.com', 'stage03_search', 200, 10, True)
    assert (tmp/'log.jsonl').exists()

  test_log_request_appends_each_entry:
    log 3 requests, read file, assert 3 lines of valid JSON

  test_write_evidence_bundle_produces_json_with_required_keys:
    log 2 requests, call write_evidence_bundle, load JSON
    assert all k in bundle for k in ['total_requests','block_rate','stop_conditions_triggered']

  test_block_rate_calculation:
    log 4 requests (2 blocked), assert bundle['block_rate'] == 0.5

  test_stop_conditions_triggered_when_block_rate_exceeds_threshold:
    log 4 requests (3 blocked), assert bundle['stop_conditions_triggered'] == True

  test_total_credits_summed_correctly:
    log requests with credits 10, 20, 30, assert total_credits_used == 60

TestRunLiveCollectionPilot (6 tests):
  test_returns_success_false_on_session_expired:
    mock SessionManager.ensure_session to raise Exception
    result = asyncio.run(run_live_collection_pilot('python_automation', database_url='sqlite:///tmp.db'))
    assert result['success'] is False and result['stop_reason'] == 'session_expired'

  test_returns_stop_reason_budget_exceeded:
    mock run_collection_pipeline to raise ScrapFlyRateLimitError
    assert result['stop_reason'] == 'budget_exceeded'

  test_returns_success_false_on_pipeline_error:
    mock run_collection_pipeline to raise Exception
    assert result['success'] is False

  test_evidence_bundle_written_even_on_error:
    mock run_collection_pipeline to raise Exception
    assert os.path.exists(evidence_path) after call

  test_pilot_db_url_never_equals_baseline:
    result = asyncio.run(run_live_collection_pilot('python_automation', database_url=None))
    assert 'cycle037_live' not in result['db_url']

  test_seeds_niche_if_missing:
    mock DB, verify _seed_pilot_niche called when Niche not found

TestCollectLiveCommand (3 tests):
  test_collect_live_registered: 'collect-live' in open('run.py').read()
  test_collect_live_requires_niche: invoke CLI without --niche, assert non-zero exit
  test_collect_live_exits_1_on_failure: mock pilot success=False, assert SystemExit(1)

TestLiveValidateCommand (3 tests):
  test_live_validate_registered: 'live-validate' in open('run.py').read()
  test_live_validate_skip_collection: --skip-collection flag accepted
  test_live_validate_writes_evidence_bundle: evidence file written

---

## TASK 15 — WRITE tests/unit/test_playbook_generator.py (32+ tests)
Create tests/unit/test_playbook_generator.py.
Use the full spec from the pre-correction B prompt's TestGeneratePlaybook,
TestExportPlaybookMarkdown, TestSectionBuilders, TestRecommendationOutputExtension,
TestRenderPlaybookSection classes.
Minimum 32 tests across 5 classes.
Key tests:
  generate_playbook returns 5 sections in empty-state
  generate_playbook never raises on DB error
  export_playbook_markdown starts with correct heading
  export_playbook_markdown contains all 5 section headings
  all section builders have correct step/strategy/milestone counts
  RecommendationOutput has profile_optimization and visual_recommendations as None

---

## TASK 16 — RUN S8.3 TESTS
```powershell
Invoke-Exe $python '-m pytest tests/unit/test_playbook_generator.py -v --no-header --tb=short 2>&1'
```
All tests must pass. Minimum 32. Coverage of generator.py >= 85%.

---

## TASK 17 — RUN LIVE PILOT TESTS
```powershell
Invoke-Exe $python '-m pytest tests/unit/test_live_pilot.py -v --no-header --tb=short 2>&1'
```
All tests must pass. Minimum 18. Coverage of pilot_logger.py and live_pilot.py >= 80%.

---

## TASK 18 — VERIFY G-010: ZERO NEW MIGRATION FILES
```python
import os, time, glob
cutoff = time.time() - 14400
for pattern in ['src/database/migrations/*.py', 'src/migrations/*.py']:
    new = [f for f in glob.glob(pattern)
           if os.path.getmtime(f) > cutoff and not f.endswith('__init__.py')]
    assert new == [], f'G-010 FAIL: {new}'
print('G-010 PASS: zero new migration files (S8.3 adds no DB tables)')
```

---

## TASK 19 — VERIFY G-015: scrapfly.enabled FALSE IN COMMITTED CONFIG
```python
import yaml
cfg = yaml.safe_load(open('C:/Fiverr/Fiverr/config.yaml', encoding='utf-8'))
enabled = cfg.get('collection',{}).get('scrapfly',{}).get('enabled')
assert not enabled, f'G-015 HARD STOP: scrapfly.enabled={enabled} in committed config!'
print(f'G-015 PASS: scrapfly.enabled={enabled} in config.yaml (runtime override only)')
```

---

## TASK 20 — VERIFY G-020: visual_analysis.py ABSENT
```python
import os
assert not os.path.exists('src/analysis/visual_analysis.py'), 'G-020 FAIL: S8.1 not in C074'
print('G-020 PASS: visual_analysis.py absent (S8.1 deferred to C075)')
```

---

## TASK 21 — FULL SUITE + COVERAGE (G-001)
```powershell
Invoke-Exe $python '-m pytest -q --cov=src --cov-fail-under=90 --no-header tests/unit/ 2>&1' | Select-Object -Last 5
```
Expected: >= 5289 passed (5271 + 18+ live pilot tests), coverage >= 90%.

---

## TASK 22 — GOLDEN PARITY (G-005)
```python
import subprocess, os; os.chdir('C:/Fiverr/Fiverr')
r = subprocess.run(
    ['C:/Users/kevin/AppData/Local/Programs/Python/Python311/python.exe',
     'run.py', 'score', '--golden',
     '--config-override', 'relevance.enable_stage_3_5=false',
     '--config-override', 'analysis.external_signals_enabled=false'],
    capture_output=True, text=True, timeout=120)
output = r.stdout + r.stderr
assert '62.7' in output and 'CONDITIONAL_GO' in output, f'G-005 FAIL: {output[-400:]}'
print('G-005 PASS: kw=110 62.7/1.0/CONDITIONAL_GO unchanged')
```

---

## TASK 23 — VERIFY ZONE: ONLY CORRECT FILES STAGED
```powershell
$changed = (Invoke-Exe $git 'diff HEAD --name-only').Out
Write-Host "B changed files:"
Write-Host $changed
# ZONE VIOLATIONS (B must NOT have changed these):
foreach ($file in ($changed -split '\n')) {
    if ($file -match 'src/discovery/' -or $file -match 'src/scoring/' -or
        $file -match 'config\.yaml$' -or $file -match 'visual_analysis') {
        Write-Host "ZONE VIOLATION: $file"
    }
}
# Verify live pilot files exist
foreach ($expected in @('src/collection/pilot_logger.py', 'src/collection/live_pilot.py',
                          'src/playbook/generator.py', 'src/reports/templates/playbook.html')) {
    if (Test-Path $expected) {
        Write-Host "PRESENT: $expected"
    } else {
        Write-Host "MISSING: $expected"
    }
}
```

---

## TASK 24 — VERIFY BASELINE UNTOUCHED
```python
import os
mtime = os.path.getmtime('C:/Fiverr/Fiverr/data/cycle037_live.db')
assert abs(mtime - 1780553758) < 10, f'BASELINE TAMPERED: {mtime}'
print(f'PASS: baseline UNTOUCHED {mtime:.0f}')
```

---

## TASK 25 — WAVE 10 CHAIN INTACT AFTER B CHANGES
```python
import sys; sys.path.insert(0,'C:/Fiverr/Fiverr')
from src.discovery.stage16 import run_discovery_cycle, _select_modes
from src.dashboard.pages.discovery import (get_discovery_stats, get_gold_discoveries,
    get_mode_performance, render_discovery_page)
from src.discovery.feedback import GOLD_THRESHOLD
import ast
n = len(open('src/discovery/stage16.py', encoding='utf-8').readlines())
assert 295 <= n <= 320
tree = ast.parse(open('src/dashboard/pages/discovery.py', encoding='utf-8').read())
fns = [nd.name for nd in ast.walk(tree) if isinstance(nd, ast.FunctionDef)]
for fn in ['get_discovery_stats','get_gold_discoveries','get_mode_performance','render_discovery_page']:
    assert fn in fns
print(f'PASS: Wave 10 intact after B (stage16={n} lines, S7.9 fns={fns})')
```

---

## TASK 26 — WAVE 9 INTACT AFTER B CHANGES
```python
import sys; sys.path.insert(0,'C:/Fiverr/Fiverr')
from src.pricing import (analyze_price_distribution, calculate_new_seller_pricing,
    build_pricing_export_payload, export_all_pricing)
print('PASS: Wave 9 pricing intact after B changes')
```

---

## TASK 27 — VERIFY collect-live AND live-validate COMMANDS WORK
```powershell
# Test collect-live --help
$r = Invoke-Exe $python 'run.py collect-live --help'
if ($r.Exit -eq 0 -and $r.Out -like '*niche*' -and $r.Out -like '*budget*') {
    Write-Host "PASS: collect-live --help shows niche and budget options"
} else {
    Write-Host "FAIL: $($r.Out) $($r.Err)"
}
# Test live-validate --help
$r2 = Invoke-Exe $python 'run.py live-validate --help'
if ($r2.Exit -eq 0 -and $r2.Out -like '*skip-collection*') {
    Write-Host "PASS: live-validate --help shows skip-collection flag"
} else {
    Write-Host "FAIL: $($r2.Out)"
}
```

---

## TASK 28 — COMMIT B WORK
```powershell
# Stage only B zone files
Invoke-Exe $git 'add src/collection/pilot_logger.py'
Invoke-Exe $git 'add src/collection/live_pilot.py'
Invoke-Exe $git 'add src/playbook/generator.py'
Invoke-Exe $git 'add src/reports/templates/playbook.html'
# Stage run.py, requirements.txt, .gitignore
Invoke-Exe $git 'add run.py requirements.txt .gitignore'
# Stage recommendations output (where RecommendationOutput lives)
# B finds and stages the correct file
Invoke-Exe $git 'add tests/unit/test_live_pilot.py tests/unit/test_playbook_generator.py'
Invoke-Exe $git 'add docs/cycle_reports/CYCLE_074_AGENT_B.md'

# Final zone check before commit
$staged = (Invoke-Exe $git 'diff --cached --name-only').Out
Write-Host "Staged: $staged"
if ($staged -match 'src/discovery/' -or $staged -match 'src/scoring/' -or
    $staged -match 'config\.yaml$') {
    Write-Host 'ZONE VIOLATION: B staged forbidden files'; exit 1
}

Invoke-Exe $git 'commit -m "feat(tierd2): C074 TierD-2 live pilot + Wave 11 S8.3 -- collect-live, live-validate, PilotLogger, playbook scaffold"'
Invoke-Exe $git 'push origin cycle/074/integration'
Invoke-Exe $git 'log --oneline -4'
```

END OF AGENT B PROMPT

---

## TASK 29 — REGRESSION PACK FINAL PASS
```python
import subprocess, os; os.chdir('C:/Fiverr/Fiverr')
r = subprocess.run(
    ['C:/Users/kevin/AppData/Local/Programs/Python/Python311/python.exe',
     '-m', 'pytest', 'tests/unit/', '-q', '--no-header', '--tb=short',
     '-k', ('test_golden_anchor_kw110_62_7 or '
            'test_ghost_market_excluded_from_go_tag or '
            'test_legacy_unscored_rows_are_ignored or '
            'test_cli_config_check_passes or '
            'test_dashboard_opportunities_renders_empty_db_gracefully')],
    capture_output=True, text=True, timeout=120)
for line in (r.stdout + r.stderr).strip().splitlines()[-5:]: print(line)
assert 'failed' not in (r.stdout+r.stderr).lower() or '0 failed' in (r.stdout+r.stderr)
print('PASS: regression pack intact after B changes')
```

---

## TASK 30 — B.md REPORT STRUCTURE
B must commit docs/cycle_reports/CYCLE_074_AGENT_B.md with:
  SHA of every commit made
  Files created/modified with line counts
  Gate results: G-001/G-005/G-010/G-015/G-020 all PASS
  New test counts: test_live_pilot.py (N tests), test_playbook_generator.py (N tests)
  Deferred scope: visual_analysis.py (S8.1 C075), profile_optimization.py (S8.2 C076)
  User post-merge action: python run.py live-validate --niche python_automation
  TierD-2 credit: ~+3-5% E2E from infrastructure build
  Project completion: Internal ~67%, E2E ~48-50%

END OF AGENT B PROMPT

---

## TASK 29 — VALIDATE SESSION_MANAGER.ensure_session EXISTS
```python
import ast, os; import sys; sys.path.insert(0,'C:/Fiverr/Fiverr')
sm_path = 'src/collection/session_manager.py'
if os.path.exists(sm_path):
    tree = ast.parse(open(sm_path, encoding='utf-8').read())
    fns = [n.name for n in ast.walk(tree) if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))]
    print(f'session_manager.py functions: {fns}')
    has_ensure = any('ensure' in f.lower() or 'session' in f.lower() for f in fns)
    print(f'ensure_session or similar: {has_ensure}')
else:
    print(f'{sm_path} not found -- B verifies path')
```
B must use the correct SessionManager method. If ensure_session does not exist,
B uses the correct method from SessionManager for session validation (e.g., is_session_valid,
reuse_or_create_session, or similar). B updates live_pilot.py accordingly.

---

## TASK 30 — VALIDATE completeness_ratio UPDATED FOR NEW FIELDS
```python
import sys; sys.path.insert(0,'C:/Fiverr/Fiverr')
# Find RecommendationOutput and verify completeness_ratio denominator
for root, dirs, files in __import__('os').walk('src'):
    dirs[:] = [d for d in dirs if d != '__pycache__']
    for f in files:
        if not f.endswith('.py'): continue
        content = open(__import__('os').path.join(root,f), encoding='utf-8').read()
        if 'completeness_ratio' not in content: continue
        for i, line in enumerate(content.splitlines()):
            if 'completeness_ratio' in line or 'len(fields)' in line or '/ 14' in line:
                print(f'{__import__("os").path.join(root,f)} L{i+1}: {line.rstrip()}')
```
B must ensure completeness_ratio denominator is updated from 12/13 to 14 when
profile_optimization and visual_recommendations are added (or 15 if more fields).

END OF AGENT B PROMPT

---

## TASK 31 — VERIFY SessionManager ENSURE_SESSION METHOD NAME
```python
import ast, os; import sys; sys.path.insert(0,'C:/Fiverr/Fiverr')
sm_path = 'src/collection/session_manager.py'
if os.path.exists(sm_path):
    tree = ast.parse(open(sm_path, encoding='utf-8').read())
    methods = []
    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef) and 'Session' in node.name:
            for n in ast.walk(node):
                if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    methods.append(n.name)
    print(f'SessionManager methods: {methods}')
    has_ensure = 'ensure_session' in methods
    has_valid = any('valid' in m.lower() or 'is_session' in m.lower() for m in methods)
    print(f'  ensure_session: {has_ensure}')
    print(f'  session validity method: {has_valid}')
    print('B uses the correct method from this list in live_pilot.py')
```

---

## TASK 32 — FINAL SCOPE CERTIFICATION
B's deliverables for C074 (complete list):
  1. src/collection/pilot_logger.py (PilotLogger, JSONL logging, evidence bundle)
  2. src/collection/live_pilot.py (run_live_collection_pilot, TierD-2 conditions A-J)
  3. run.py: collect-live command (TierD-2 CLI entry point)
  4. run.py: live-validate command (end-to-end pipeline orchestrator)
  5. run.py: recommendations-only --live flag (dry_run=False path)
  6. run.py: playbook command (markdown/pdf export)
  7. run.py: _validate_pilot_db_state helper
  8. run.py: _run_live_recommendations helper
  9. run.py: _generate_playbook_from_live_data helper
  10. src/playbook/generator.py (9 functions, 5-section playbook, Wave 11 S8.3)
  11. src/reports/templates/playbook.html (Jinja2 PDF template)
  12. src/recommendations/output.py: +profile_optimization, +visual_recommendations
  13. requirements.txt: +scrapfly-sdk>=6.0
  14. .gitignore: +live pilot patterns
  15. tests/unit/test_live_pilot.py (18+ tests)
  16. tests/unit/test_playbook_generator.py (32+ tests)
  17. docs/cycle_reports/CYCLE_074_AGENT_B.md

END OF AGENT B PROMPT
