"""Customer-facing PDF report generation (Wave 8 reporting).

Renders the four report types (opportunity, recommendation, run_summary) --
see PM_Pack/ref/project_plan/07_reporting/REPORT_TEMPLATES.md -- as Jinja2
HTML, then writes a PDF via WeasyPrint. The competitor report is not yet
implemented: no per-cluster top-seller/authority data is persisted anywhere
in the schema (only niche-wide CompetitorProfile aggregates exist), so the
plan's template would have to fabricate data that doesn't exist (SCRUM-1148
follow-up).
"""

from __future__ import annotations

import logging
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

TEMPLATE_DIR = Path(__file__).resolve().parent / "templates"

# WeasyPrint's internal progress logger has a known bug where its "Creating
# layout - Page %d" message is occasionally emitted with a non-numeric page
# identifier, which crashes any log handler that formats the record (e.g.
# pytest's log capture) with "TypeError: %d format: a real number is
# required, not str". This logger is routine internal progress noise with no
# value to report consumers, so it's silenced entirely rather than relying on
# every caller's log configuration to tolerate a third-party formatting bug.
logging.getLogger("weasyprint.progress").setLevel(logging.CRITICAL)

REPORT_TITLES: dict[str, str] = {
    "opportunity": "Opportunity Report",
    "recommendation": "Recommendation Report",
    "run_summary": "Run Summary Report",
}


def generate_report(
    report_type: str,
    data: dict[str, Any],
    output_path: str,
    *,
    run_id: str | None = None,
    niche_name: str | None = None,
) -> str:
    """Renders `report_type` with `data` and writes a PDF to `output_path`.

    Returns `output_path`. Raises ValueError for an unknown report_type, and
    ImportError with an install hint when WeasyPrint's native libraries
    (Pango/Cairo/GObject) are unavailable -- the same tolerant pattern used
    by src/playbook/generator.py::export_playbook_pdf.
    """
    if report_type not in REPORT_TITLES:
        raise ValueError(
            f"Unknown report_type '{report_type}'. Expected one of {sorted(REPORT_TITLES)}."
        )

    try:
        from jinja2 import Environment, FileSystemLoader
        from weasyprint import HTML  # type: ignore[import-untyped]
    except (ImportError, OSError) as exc:  # pragma: no cover - environment dependent
        raise ImportError(
            "PDF report generation requires WeasyPrint + Jinja2. Install with: pip install weasyprint jinja2"
        ) from exc

    env = Environment(loader=FileSystemLoader(str(TEMPLATE_DIR)))
    template = env.get_template(f"{report_type}.html")
    html_content = template.render(
        report_title=REPORT_TITLES[report_type],
        generated_at=datetime.now(UTC).strftime("%Y-%m-%d %H:%M UTC"),
        run_id=run_id,
        niche_name=niche_name,
        **data,
    )

    out = Path(output_path)
    out.parent.mkdir(parents=True, exist_ok=True)
    HTML(string=html_content).write_pdf(str(out))
    return str(out)
