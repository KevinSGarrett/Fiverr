"""Supplemental CLI surfaces for focused utility workflows."""

from __future__ import annotations

import argparse
from collections.abc import Sequence

from src.models.database import (
    create_session_factory,
    get_session,
    initialize_database,
    normalize_database_url,
)
from src.models.price_analysis import PriceAnalysis
from src.pricing.pricing_export import export_all_pricing


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Fiverr research utility CLI")
    subparsers = parser.add_subparsers(dest="command")

    pricing_export = subparsers.add_parser(
        "pricing-export",
        help="Export pricing snapshots in csv/json/excel/md formats.",
    )
    pricing_export.add_argument(
        "--keyword-id",
        action="append",
        type=int,
        default=[],
        help="Optional keyword id filter. Repeat for multiple ids.",
    )
    pricing_export.add_argument(
        "--format",
        action="append",
        choices=["csv", "json", "excel", "md"],
        default=[],
        help="Optional format filter; defaults to all formats.",
    )
    pricing_export.add_argument(
        "--output-dir",
        default="exports/pricing",
        help="Output directory for generated pricing exports.",
    )
    pricing_export.add_argument(
        "--database-url",
        default=None,
        help="Optional database URL override.",
    )
    return parser


def _run_pricing_export(args: argparse.Namespace) -> int:
    normalized_url = normalize_database_url(args.database_url)
    engine = initialize_database(database_url=normalized_url)
    session_factory = create_session_factory(engine)
    with get_session(session_factory) as db:
        keyword_ids = sorted({value for value in args.keyword_id if value > 0})
        if not keyword_ids:
            rows = db.query(PriceAnalysis.keyword_id).distinct().order_by(PriceAnalysis.keyword_id.asc()).all()
            keyword_ids = [int(row[0]) for row in rows if row and row[0] is not None]
        if not keyword_ids:
            print("No pricing rows found; nothing exported.")
            return 0
        results = export_all_pricing(
            keyword_ids=keyword_ids,
            db=db,
            output_dir=args.output_dir,
            formats=list(args.format) or None,
        )
    print(f"Exported {len(results)} pricing file(s) to {args.output_dir}")
    return 0


def main(argv: Sequence[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(list(argv) if argv is not None else None)
    if args.command == "pricing-export":
        return _run_pricing_export(args)
    parser.print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
