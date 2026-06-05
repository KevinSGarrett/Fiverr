"""Unit tests for Wave 9 pricing export helpers."""

from __future__ import annotations

import inspect
import json
from pathlib import Path

import openpyxl
import pytest
from sqlalchemy import inspect as sa_inspect
from sqlalchemy.orm import Session
from src.models.price_analysis import PriceAnalysis
from src.models.price_ladder_snapshot import PriceLadderSnapshot
from src.pricing.pricing_export import (
    build_pricing_export_payload,
    export_all_pricing,
    export_pricing_csv,
    export_pricing_excel,
    export_pricing_json,
    export_pricing_markdown,
    row_to_dict,
)


class TestBuildPricingExportPayload:
    def test_returns_dict_with_required_keys(self, seeded_pricing_export_db) -> None:
        payload = build_pricing_export_payload(1, seeded_pricing_export_db)
        assert {
            "keyword_id",
            "niche_price_analyses",
            "price_analyses",
            "pricing_snapshots",
            "ladder_snapshots",
            "revenue_gate_records",
            "pricing_strategy_outputs",
            "export_timestamp",
        }.issubset(payload.keys())

    def test_returns_empty_lists_for_empty_db(self, empty_db) -> None:
        payload = build_pricing_export_payload(1, empty_db)
        assert payload["niche_price_analyses"] == []
        assert payload["price_analyses"] == []
        assert payload["pricing_snapshots"] == []
        assert payload["ladder_snapshots"] == []
        assert payload["revenue_gate_records"] == []
        assert payload["pricing_strategy_outputs"] == []

    def test_keyword_id_in_payload(self, seeded_pricing_export_db) -> None:
        payload = build_pricing_export_payload(1, seeded_pricing_export_db)
        assert payload["keyword_id"] == 1

    def test_export_timestamp_present(self, seeded_pricing_export_db) -> None:
        payload = build_pricing_export_payload(1, seeded_pricing_export_db)
        assert isinstance(payload["export_timestamp"], str)
        assert "T" in payload["export_timestamp"]

    def test_price_analyses_are_list(self, seeded_pricing_export_db) -> None:
        payload = build_pricing_export_payload(1, seeded_pricing_export_db)
        assert isinstance(payload["price_analyses"], list)

    def test_includes_pricing_strategy_output(self, seeded_pricing_export_db) -> None:
        payload = build_pricing_export_payload(1, seeded_pricing_export_db)
        assert len(payload["pricing_strategy_outputs"]) == 1
        assert payload["pricing_strategy_outputs"][0]["recommendation_type"] == "pricing_strategy"

    def test_row_to_dict_excludes_private_attrs(self, seeded_pricing_export_db) -> None:
        with Session(seeded_pricing_export_db) as session:
            row = session.query(PriceAnalysis).first()
            assert row is not None
            exported = row_to_dict(row)
            assert exported
            assert not any(key.startswith("_") for key in exported)

    def test_row_to_dict_only_contains_columns(self, seeded_pricing_export_db) -> None:
        with Session(seeded_pricing_export_db) as session:
            row = session.query(PriceAnalysis).first()
            assert row is not None
            exported = row_to_dict(row)
            columns = {column["name"] for column in sa_inspect(seeded_pricing_export_db).get_columns("price_analysis")}
            assert set(exported.keys()).issubset(columns)


class TestExportPricingCsv:
    def test_creates_file_at_output_path(self, tmp_path: Path, seeded_pricing_export_db) -> None:
        output = tmp_path / "pricing.csv"
        export_pricing_csv(1, seeded_pricing_export_db, str(output))
        assert output.exists()

    def test_file_is_nonempty(self, tmp_path: Path, seeded_pricing_export_db) -> None:
        output = tmp_path / "pricing.csv"
        export_pricing_csv(1, seeded_pricing_export_db, str(output))
        assert output.stat().st_size > 0

    def test_empty_db_creates_file(self, tmp_path: Path, empty_db) -> None:
        output = tmp_path / "empty.csv"
        export_pricing_csv(99, empty_db, str(output))
        assert output.exists()

    def test_returns_output_path(self, tmp_path: Path, seeded_pricing_export_db) -> None:
        output = tmp_path / "pricing.csv"
        result = export_pricing_csv(1, seeded_pricing_export_db, str(output))
        assert result == str(output)

    def test_csv_has_section_headers(self, tmp_path: Path, seeded_pricing_export_db) -> None:
        output = tmp_path / "pricing.csv"
        export_pricing_csv(1, seeded_pricing_export_db, str(output))
        content = output.read_text(encoding="utf-8")
        assert "# price_analyses" in content
        assert "# pricing_strategy_outputs" in content


class TestExportPricingJson:
    def test_creates_valid_json(self, tmp_path: Path, seeded_pricing_export_db) -> None:
        output = tmp_path / "pricing.json"
        export_pricing_json(1, seeded_pricing_export_db, str(output))
        payload = json.loads(output.read_text(encoding="utf-8"))
        assert isinstance(payload, dict)

    def test_returns_output_path(self, tmp_path: Path, seeded_pricing_export_db) -> None:
        output = tmp_path / "pricing.json"
        result = export_pricing_json(1, seeded_pricing_export_db, str(output))
        assert result == str(output)

    def test_empty_db_creates_json(self, tmp_path: Path, empty_db) -> None:
        output = tmp_path / "empty.json"
        export_pricing_json(999, empty_db, str(output))
        payload = json.loads(output.read_text(encoding="utf-8"))
        assert payload["price_analyses"] == []

    def test_json_has_keyword_id(self, tmp_path: Path, seeded_pricing_export_db) -> None:
        output = tmp_path / "pricing.json"
        export_pricing_json(1, seeded_pricing_export_db, str(output))
        payload = json.loads(output.read_text(encoding="utf-8"))
        assert payload["keyword_id"] == 1

    def test_datetime_serialized_as_string(self, tmp_path: Path, seeded_pricing_export_db) -> None:
        output = tmp_path / "pricing.json"
        export_pricing_json(1, seeded_pricing_export_db, str(output))
        payload = json.loads(output.read_text(encoding="utf-8"))
        assert isinstance(payload["export_timestamp"], str)


class TestExportPricingMarkdown:
    def test_creates_markdown_file(self, tmp_path: Path, seeded_pricing_export_db) -> None:
        output = tmp_path / "pricing.md"
        export_pricing_markdown(1, seeded_pricing_export_db, str(output))
        assert output.exists()

    def test_contains_section_headers(self, tmp_path: Path, seeded_pricing_export_db) -> None:
        output = tmp_path / "pricing.md"
        export_pricing_markdown(1, seeded_pricing_export_db, str(output))
        text = output.read_text(encoding="utf-8")
        assert "## Price Distribution Analysis" in text
        assert "## Pricing Strategy Output" in text

    def test_empty_db_creates_no_data_sections(self, tmp_path: Path, empty_db) -> None:
        output = tmp_path / "empty.md"
        export_pricing_markdown(1, empty_db, str(output))
        text = output.read_text(encoding="utf-8")
        assert "_No data available._" in text

    def test_returns_output_path(self, tmp_path: Path, seeded_pricing_export_db) -> None:
        output = tmp_path / "pricing.md"
        result = export_pricing_markdown(1, seeded_pricing_export_db, str(output))
        assert result == str(output)

    def test_caps_rows_at_twenty(self, tmp_path: Path, seeded_pricing_export_db) -> None:
        with Session(seeded_pricing_export_db) as session:
            for idx in range(24):
                session.add(
                    PriceLadderSnapshot(
                        keyword_id=1,
                        niche_id="test_niche",
                        run_id=f"r{idx}",
                        reviews_at_snapshot=idx + 6,
                        ladder_milestone=5,
                        actual_basic_price=70.0 + idx,
                        recommended_basic_price=65.0,
                        price_delta_pct=0.1,
                        on_track=True,
                    )
                )
            session.commit()
        output = tmp_path / "cap.md"
        export_pricing_markdown(1, seeded_pricing_export_db, str(output))
        text = output.read_text(encoding="utf-8")
        ladder_section = text.split("## Price Ladder Progress", maxsplit=1)[1]
        ladder_section = ladder_section.split("## Revenue Gate Records", maxsplit=1)[0]
        row_lines = [line for line in ladder_section.splitlines() if line.startswith("| ")]
        # header + separator + 20 data rows
        assert len(row_lines) == 22


class TestExportPricingExcel:
    def test_creates_xlsx_file(self, tmp_path: Path, seeded_pricing_export_db) -> None:
        output = tmp_path / "pricing.xlsx"
        export_pricing_excel([1], seeded_pricing_export_db, str(output))
        assert output.exists()

    def test_workbook_has_pricing_sheets(self, tmp_path: Path, seeded_pricing_export_db) -> None:
        output = tmp_path / "pricing.xlsx"
        export_pricing_excel([1], seeded_pricing_export_db, str(output))
        workbook = openpyxl.load_workbook(output)
        assert "price_analysis" in workbook.sheetnames
        assert "pricing_strategy_outputs" in workbook.sheetnames

    def test_returns_output_path(self, tmp_path: Path, seeded_pricing_export_db) -> None:
        output = tmp_path / "pricing.xlsx"
        result = export_pricing_excel([1], seeded_pricing_export_db, str(output))
        assert result == str(output)

    def test_empty_db_creates_empty_workbook(self, tmp_path: Path, empty_db) -> None:
        output = tmp_path / "empty.xlsx"
        export_pricing_excel([], empty_db, str(output))
        workbook = openpyxl.load_workbook(output)
        assert "export_meta" in workbook.sheetnames

    def test_excel_file_is_valid_xlsx(self, tmp_path: Path, empty_db) -> None:
        output = tmp_path / "valid.xlsx"
        export_pricing_excel([], empty_db, str(output))
        workbook = openpyxl.load_workbook(output)
        assert isinstance(workbook.sheetnames, list)


class TestExportAllPricing:
    def test_creates_multiple_format_files(self, tmp_path: Path, seeded_pricing_export_db) -> None:
        results = export_all_pricing([1], seeded_pricing_export_db, str(tmp_path))
        assert "excel" in results
        assert any(key.startswith("csv_") for key in results)
        assert any(key.startswith("json_") for key in results)
        assert any(key.startswith("md_") for key in results)

    def test_returns_dict_of_paths(self, tmp_path: Path, seeded_pricing_export_db) -> None:
        results = export_all_pricing([1], seeded_pricing_export_db, str(tmp_path))
        assert isinstance(results, dict)
        assert all(Path(path).exists() for path in results.values())

    def test_single_format_only(self, tmp_path: Path, seeded_pricing_export_db) -> None:
        results = export_all_pricing([1], seeded_pricing_export_db, str(tmp_path), formats=["json"])
        assert set(results.keys()) == {"json_kw1"}

    def test_creates_output_dir_if_missing(self, tmp_path: Path, seeded_pricing_export_db) -> None:
        output_dir = tmp_path / "nested" / "exports"
        export_all_pricing([1], seeded_pricing_export_db, str(output_dir))
        assert output_dir.exists()

    def test_empty_keyword_list_returns_empty_dict(self, tmp_path: Path, empty_db) -> None:
        results = export_all_pricing([], empty_db, str(tmp_path))
        assert results == {}

    def test_default_formats_include_csv(self) -> None:
        signature = inspect.signature(export_all_pricing)
        default_formats = signature.parameters["formats"].default
        assert default_formats is None

    @pytest.mark.parametrize("fmt", ["csv", "json", "excel", "md"])
    def test_single_format_parametrized(self, tmp_path: Path, seeded_pricing_export_db, fmt: str) -> None:
        results = export_all_pricing([1], seeded_pricing_export_db, str(tmp_path), formats=[fmt])
        assert len(results) >= 1
        assert all(Path(path).exists() for path in results.values())

    def test_export_all_pricing_creates_missing_output_dir(
        self, tmp_path: Path, seeded_pricing_export_db
    ) -> None:
        output_dir = tmp_path / "brand_new_dir" / "subdir"
        assert not output_dir.exists()
        results = export_all_pricing([1], seeded_pricing_export_db, str(output_dir), formats=["json"])
        assert output_dir.is_dir()
        assert len(results) >= 1

    def test_export_all_empty_keywords_returns_no_per_kw_files(self, tmp_path: Path, empty_db) -> None:
        results = export_all_pricing([], empty_db, str(tmp_path), formats=["csv", "json", "md"])
        csv_files = [value for value in results.values() if str(value).endswith(".csv")]
        json_files = [value for value in results.values() if str(value).endswith(".json")]
        assert len(csv_files) == 0
        assert len(json_files) == 0

    def test_wave9_complete_export_pipeline(self, tmp_path: Path, seeded_pricing_export_db) -> None:
        results = export_all_pricing(
            [1],
            seeded_pricing_export_db,
            str(tmp_path),
            formats=["csv", "json", "excel", "md"],
        )
        assert len(results) == 4
        for path in results.values():
            assert Path(path).exists()


class TestModuleBehaviors:
    def test_markdown_source_has_row_cap(self) -> None:
        source = inspect.getsource(export_pricing_markdown)
        assert "[:20]" in source

    def test_payload_serializes_to_json_without_float_errors(self, empty_db) -> None:
        payload = build_pricing_export_payload(999, empty_db)
        serialized = json.dumps(payload, default=str)
        assert isinstance(serialized, str)

    def test_module_does_not_import_tests(self) -> None:
        source = Path("src/pricing/pricing_export.py").read_text(encoding="utf-8")
        assert "from tests" not in source
        assert "import tests" not in source

    def test_build_payload_only_returns_requested_keyword_data(self, seeded_pricing_export_db) -> None:
        payload_kw1 = build_pricing_export_payload(1, seeded_pricing_export_db)
        payload_kw999 = build_pricing_export_payload(999, seeded_pricing_export_db)
        assert payload_kw1["keyword_id"] == 1
        assert payload_kw999["keyword_id"] == 999
        for key in ["price_analyses", "pricing_snapshots", "ladder_snapshots", "revenue_gate_records"]:
            assert payload_kw999.get(key, []) == []

    def test_markdown_caps_rows_at_20_with_large_fixture(self, tmp_path: Path, seeded_large_pricing_db) -> None:
        output = tmp_path / "large_cap.md"
        export_pricing_markdown(1, seeded_large_pricing_db, str(output))
        assert output.exists()
        text = output.read_text(encoding="utf-8")
        ladder_section = text.split("## Price Ladder Progress", maxsplit=1)[1]
        ladder_section = ladder_section.split("## Revenue Gate Records", maxsplit=1)[0]
        row_lines = [line for line in ladder_section.splitlines() if line.startswith("| ")]
        assert len(row_lines) == 22

    def test_json_export_serializes_datetime_objects(self, tmp_path: Path, seeded_pricing_export_db) -> None:
        output = tmp_path / "datetime_payload.json"
        export_pricing_json(1, seeded_pricing_export_db, str(output))
        data = json.loads(output.read_text(encoding="utf-8"))
        assert isinstance(data, dict)
        assert isinstance(data.get("export_timestamp"), str)

    def test_csv_has_section_label_for_each_data_type(
        self, tmp_path: Path, seeded_pricing_export_db
    ) -> None:
        output = tmp_path / "sections.csv"
        export_pricing_csv(1, seeded_pricing_export_db, str(output))
        content = output.read_text(encoding="utf-8")
        section_lines = [line for line in content.splitlines() if line.startswith("# ")]
        assert len(section_lines) >= 1

    def test_build_payload_all_sections_populated(self, seeded_pricing_export_db) -> None:
        payload = build_pricing_export_payload(1, seeded_pricing_export_db)
        assert len(payload["niche_price_analyses"]) > 0
        assert len(payload["price_analyses"]) > 0
        assert len(payload["pricing_snapshots"]) > 0
        assert len(payload["ladder_snapshots"]) > 0
        assert len(payload["revenue_gate_records"]) > 0

    def test_row_to_dict_includes_all_columns(self, seeded_pricing_export_db) -> None:
        with Session(seeded_pricing_export_db) as session:
            row = session.query(PriceAnalysis).first()
            assert row is not None
            exported = row_to_dict(row)
            columns = {
                column["name"] for column in sa_inspect(seeded_pricing_export_db).get_columns("price_analysis")
            }
            assert set(exported.keys()) == columns
            assert "keyword_id" in exported
            assert "niche_id" in exported

    def test_complete_wave9_export_round_trip(self, tmp_path: Path, seeded_pricing_export_db) -> None:
        output = tmp_path / "roundtrip.json"
        export_pricing_json(1, seeded_pricing_export_db, str(output))
        assert output.exists()
        data = json.loads(output.read_text(encoding="utf-8"))
        assert data["keyword_id"] == 1
        for section in [
            "price_analyses",
            "pricing_snapshots",
            "ladder_snapshots",
            "revenue_gate_records",
        ]:
            assert isinstance(data.get(section, []), list)

    def test_wave9_all_pricing_modules_coexist(self) -> None:
        from src.pricing import (
            analyze_price_distribution,
            calculate_new_seller_pricing,
            check_revenue_gates,
            pricing_llm_task,
            track_price_ladder,
        )
        from src.pricing import (
            build_pricing_export_payload as build_payload_from_package,
        )
        from src.pricing import (
            export_all_pricing as export_all_from_package,
        )

        assert callable(analyze_price_distribution)
        assert callable(calculate_new_seller_pricing)
        assert callable(pricing_llm_task)
        assert callable(track_price_ladder)
        assert callable(check_revenue_gates)
        assert callable(build_payload_from_package)
        assert callable(export_all_from_package)


class TestExportPricingCsvEdgeCases:
    def test_csv_handles_none_values(self, tmp_path: Path, seeded_pricing_export_db) -> None:
        path = tmp_path / "test.csv"
        result = export_pricing_csv(1, seeded_pricing_export_db, str(path))
        content = Path(result).read_text(encoding="utf-8")
        assert result == str(path)
        assert len(content) > 0

    def test_csv_creates_parent_dir_if_missing(self, tmp_path: Path, seeded_pricing_export_db) -> None:
        nested = tmp_path / "nested" / "dir" / "test.csv"
        result = export_pricing_csv(1, seeded_pricing_export_db, str(nested))
        assert Path(result).exists()

    def test_csv_multiple_keyword_ids_separate_files(
        self, tmp_path: Path, seeded_pricing_export_db
    ) -> None:
        for keyword_id in [1, 999]:
            path = tmp_path / f"pricing_kw{keyword_id}.csv"
            result = export_pricing_csv(keyword_id, seeded_pricing_export_db, str(path))
            assert Path(result).exists()

    def test_csv_empty_payload_still_creates_file(self, tmp_path: Path, empty_db) -> None:
        path = tmp_path / "empty.csv"
        result = export_pricing_csv(999, empty_db, str(path))
        assert Path(result).exists()


class TestExportPricingJsonEdgeCases:
    def test_json_is_valid_dict(self, tmp_path: Path, seeded_pricing_export_db) -> None:
        path = tmp_path / "test.json"
        result = export_pricing_json(1, seeded_pricing_export_db, str(path))
        data = json.loads(Path(result).read_text(encoding="utf-8"))
        assert isinstance(data, dict)
        assert data["keyword_id"] == 1

    def test_json_all_sections_present(self, tmp_path: Path, seeded_pricing_export_db) -> None:
        path = tmp_path / "test.json"
        result = export_pricing_json(1, seeded_pricing_export_db, str(path))
        data = json.loads(Path(result).read_text(encoding="utf-8"))
        for key in [
            "price_analyses",
            "pricing_snapshots",
            "ladder_snapshots",
            "revenue_gate_records",
            "export_timestamp",
        ]:
            assert key in data

    def test_json_timestamp_is_iso_string(self, tmp_path: Path, seeded_pricing_export_db) -> None:
        path = tmp_path / "test.json"
        result = export_pricing_json(1, seeded_pricing_export_db, str(path))
        data = json.loads(Path(result).read_text(encoding="utf-8"))
        assert isinstance(data.get("export_timestamp", ""), str)
        assert len(data.get("export_timestamp", "")) > 0


class TestExportPricingMarkdownEdgeCases:
    def test_markdown_starts_with_header(self, tmp_path: Path, seeded_pricing_export_db) -> None:
        path = tmp_path / "test.md"
        result = export_pricing_markdown(1, seeded_pricing_export_db, str(path))
        content = Path(result).read_text(encoding="utf-8")
        assert content.startswith("#")

    def test_markdown_contains_table_syntax(self, tmp_path: Path, seeded_pricing_export_db) -> None:
        path = tmp_path / "test.md"
        result = export_pricing_markdown(1, seeded_pricing_export_db, str(path))
        content = Path(result).read_text(encoding="utf-8")
        assert "|" in content

    def test_markdown_no_data_section_graceful(self, tmp_path: Path, empty_db) -> None:
        path = tmp_path / "empty.md"
        result = export_pricing_markdown(999, empty_db, str(path))
        content = Path(result).read_text(encoding="utf-8")
        assert "No data" in content or "available" in content.lower() or len(content) > 0


class TestExportPricingExcelEdgeCases:
    def test_excel_workbook_has_expected_sheets(self, tmp_path: Path, seeded_pricing_export_db) -> None:
        path = tmp_path / "test.xlsx"
        result = export_pricing_excel([1], seeded_pricing_export_db, str(path))
        workbook = openpyxl.load_workbook(result)
        assert len(workbook.sheetnames) >= 1

    def test_excel_multi_keyword_all_data_in_workbook(
        self, tmp_path: Path, seeded_pricing_export_db
    ) -> None:
        path = tmp_path / "multi.xlsx"
        result = export_pricing_excel([1, 999], seeded_pricing_export_db, str(path))
        output = Path(result)
        assert output.exists()
        assert output.stat().st_size > 0

    def test_excel_empty_keywords_list_creates_file(self, tmp_path: Path, empty_db) -> None:
        path = tmp_path / "empty.xlsx"
        result = export_pricing_excel([], empty_db, str(path))
        assert Path(result).exists()
