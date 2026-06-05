"""Wave 9 Phase 4 pricing export helpers (S6.8)."""

from __future__ import annotations

import csv
import json
from contextlib import contextmanager
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from src.models.market import Keyword
from src.models.niche import Niche
from src.models.price_analysis import NichePriceAnalysis, PriceAnalysis, PricingSnapshot
from src.models.price_ladder_snapshot import PriceLadderSnapshot
from src.models.revenue_gate_record import RevenueGateRecord
from src.models.scoring import Recommendation


def row_to_dict(row: Any) -> dict[str, Any]:
    """Convert ORM row to a column-only dictionary."""
    return {column.name: getattr(row, column.name) for column in row.__table__.columns}


@contextmanager
def _session_scope(db: Any):
    if isinstance(db, Session):
        yield db
        return

    bind = db.get_bind() if hasattr(db, "get_bind") else db
    with Session(bind) as session:
        yield session


def _to_jsonable(value: Any) -> Any:
    if isinstance(value, datetime):
        return value.isoformat()
    if isinstance(value, dict):
        return {str(key): _to_jsonable(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_to_jsonable(item) for item in value]
    return value


def _resolve_niche_slug(session: Session, keyword_id: int) -> str | None:
    try:
        keyword = session.query(Keyword).filter(Keyword.id == keyword_id).first()
    except SQLAlchemyError:
        return None
    if keyword is None:
        return None
    try:
        niche = session.query(Niche).filter(Niche.id == keyword.niche_id).first()
    except SQLAlchemyError:
        return None
    if niche is None:
        return None
    return niche.slug


def _load_pricing_strategy_outputs(session: Session, keyword_id: int) -> list[dict[str, Any]]:
    try:
        rows = (
            session.query(Recommendation)
            .filter(
                Recommendation.keyword_id == keyword_id,
                Recommendation.recommendation_type == "pricing_strategy",
            )
            .order_by(Recommendation.created_at.desc())
            .all()
        )
    except SQLAlchemyError:
        return []
    return [_to_jsonable(row_to_dict(row)) for row in rows]


def _safe_rows(query: Any) -> list[Any]:
    try:
        return query.all()
    except SQLAlchemyError:
        return []


def build_pricing_export_payload(keyword_id: int, db: Any) -> dict[str, Any]:
    """Assemble all pricing export data for one keyword."""
    with _session_scope(db) as session:
        niche_slug = _resolve_niche_slug(session=session, keyword_id=keyword_id)
        niche_rows = (
            _safe_rows(session.query(NichePriceAnalysis).filter(NichePriceAnalysis.niche_id == niche_slug))
            if niche_slug is not None
            else []
        )
        analyses = _safe_rows(session.query(PriceAnalysis).filter(PriceAnalysis.keyword_id == keyword_id))
        snapshots = _safe_rows(session.query(PricingSnapshot).filter(PricingSnapshot.keyword_id == keyword_id))
        ladder_snapshots = _safe_rows(
            session.query(PriceLadderSnapshot).filter(PriceLadderSnapshot.keyword_id == keyword_id)
        )
        revenue_records = _safe_rows(
            session.query(RevenueGateRecord).filter(RevenueGateRecord.keyword_id == keyword_id)
        )
        strategy_outputs = _load_pricing_strategy_outputs(session=session, keyword_id=keyword_id)

    return {
        "keyword_id": keyword_id,
        "niche_price_analyses": [_to_jsonable(row_to_dict(row)) for row in niche_rows],
        "price_analyses": [_to_jsonable(row_to_dict(row)) for row in analyses],
        "pricing_snapshots": [_to_jsonable(row_to_dict(row)) for row in snapshots],
        "ladder_snapshots": [_to_jsonable(row_to_dict(row)) for row in ladder_snapshots],
        "revenue_gate_records": [_to_jsonable(row_to_dict(row)) for row in revenue_records],
        "pricing_strategy_outputs": strategy_outputs,
        "export_timestamp": datetime.now(tz=UTC).isoformat(),
    }


def export_pricing_csv(keyword_id: int, db: Any, output_path: str) -> str:
    """Export pricing payload as CSV and return file path."""
    payload = build_pricing_export_payload(keyword_id=keyword_id, db=db)
    destination = Path(output_path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    with destination.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        for section, rows in payload.items():
            if not isinstance(rows, list):
                continue
            writer.writerow([f"# {section}"])
            if rows:
                headers = list(rows[0].keys())
                writer.writerow(headers)
                for row in rows:
                    writer.writerow([_to_jsonable(row.get(header)) for header in headers])
            writer.writerow([])
    return str(destination)


def export_pricing_json(keyword_id: int, db: Any, output_path: str) -> str:
    """Export pricing payload as JSON and return file path."""
    payload = build_pricing_export_payload(keyword_id=keyword_id, db=db)
    destination = Path(output_path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    with destination.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2, default=_to_jsonable)
    return str(destination)


def export_pricing_excel(keyword_ids: list[int], db: Any, output_path: str) -> str:
    """Export pricing payloads as workbook sheets and return file path."""
    import pandas as pd

    destination = Path(output_path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    sheets: dict[str, list[dict[str, Any]]] = {
        "niche_price_analysis": [],
        "price_analysis": [],
        "pricing_snapshots": [],
        "price_ladder_snapshots": [],
        "revenue_gate_records": [],
        "pricing_strategy_outputs": [],
    }
    for keyword_id in keyword_ids:
        payload = build_pricing_export_payload(keyword_id=keyword_id, db=db)
        sheets["niche_price_analysis"].extend(payload.get("niche_price_analyses", []))
        sheets["price_analysis"].extend(payload.get("price_analyses", []))
        sheets["pricing_snapshots"].extend(payload.get("pricing_snapshots", []))
        sheets["price_ladder_snapshots"].extend(payload.get("ladder_snapshots", []))
        sheets["revenue_gate_records"].extend(payload.get("revenue_gate_records", []))
        sheets["pricing_strategy_outputs"].extend(payload.get("pricing_strategy_outputs", []))

    with pd.ExcelWriter(destination, engine="openpyxl") as writer:
        for sheet_name, rows in sheets.items():
            frame = pd.DataFrame(rows)
            frame.to_excel(writer, sheet_name=sheet_name[:31], index=False)
        pd.DataFrame({"keyword_ids": keyword_ids}).to_excel(writer, sheet_name="export_meta", index=False)
    return str(destination)


def _escape_markdown_cell(value: Any) -> str:
    text = "" if value is None else str(value)
    return text.replace("\n", "<br>").replace("|", "\\|")


def export_pricing_markdown(keyword_id: int, db: Any, output_path: str) -> str:
    """Export pricing payload as a Markdown report and return file path."""
    payload = build_pricing_export_payload(keyword_id=keyword_id, db=db)
    lines = [
        f"# Pricing Export - keyword_id={keyword_id}",
        f"Generated: {payload['export_timestamp']}",
        "",
    ]
    section_titles = {
        "niche_price_analyses": "## Niche Price Analysis",
        "price_analyses": "## Price Distribution Analysis",
        "pricing_snapshots": "## New Seller Pricing Recommendations",
        "ladder_snapshots": "## Price Ladder Progress",
        "revenue_gate_records": "## Revenue Gate Records",
        "pricing_strategy_outputs": "## Pricing Strategy Output",
    }

    for section_key, title in section_titles.items():
        rows = payload.get(section_key, [])
        lines.append(title)
        if not rows:
            lines.append("_No data available._")
            lines.append("")
            continue

        headers = list(rows[0].keys())
        lines.append("| " + " | ".join(headers) + " |")
        lines.append("| " + " | ".join(["---"] * len(headers)) + " |")
        for row in rows[:20]:
            values = [_escape_markdown_cell(row.get(column)) for column in headers]
            lines.append("| " + " | ".join(values) + " |")
        lines.append("")

    destination = Path(output_path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text("\n".join(lines), encoding="utf-8")
    return str(destination)


def export_all_pricing(
    keyword_ids: list[int],
    db: Any,
    output_dir: str,
    formats: list[str] | None = None,
) -> dict[str, str]:
    """Export pricing data in requested formats and return format/path map."""
    if not keyword_ids:
        return {}

    selected_formats = [name.strip().lower() for name in (formats or ["csv", "json", "excel", "md"])]
    output_root = Path(output_dir)
    output_root.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now(tz=UTC).strftime("%Y%m%d_%H%M%S")
    results: dict[str, str] = {}

    if "csv" in selected_formats:
        for keyword_id in keyword_ids:
            path = output_root / f"pricing_kw{keyword_id}_{timestamp}.csv"
            results[f"csv_kw{keyword_id}"] = export_pricing_csv(keyword_id=keyword_id, db=db, output_path=str(path))
    if "json" in selected_formats:
        for keyword_id in keyword_ids:
            path = output_root / f"pricing_kw{keyword_id}_{timestamp}.json"
            results[f"json_kw{keyword_id}"] = export_pricing_json(keyword_id=keyword_id, db=db, output_path=str(path))
    if "excel" in selected_formats:
        path = output_root / f"pricing_all_{timestamp}.xlsx"
        results["excel"] = export_pricing_excel(keyword_ids=keyword_ids, db=db, output_path=str(path))
    if "md" in selected_formats:
        for keyword_id in keyword_ids:
            path = output_root / f"pricing_kw{keyword_id}_{timestamp}.md"
            results[f"md_kw{keyword_id}"] = export_pricing_markdown(keyword_id=keyword_id, db=db, output_path=str(path))

    return results


__all__ = [
    "row_to_dict",
    "build_pricing_export_payload",
    "export_pricing_csv",
    "export_pricing_json",
    "export_pricing_excel",
    "export_pricing_markdown",
    "export_all_pricing",
]
