"""Unit tests for the XLSX/CSV extractor."""

from __future__ import annotations

import io

import pytest

from atlas_worker.extractors.xlsx import XlsxResult, extract_xlsx


# ---------------------------------------------------------------------------
# In-memory fixture builders
# ---------------------------------------------------------------------------

def _build_xlsx(sheets: dict[str, list[list[object]]] | None = None) -> bytes:
    """Build a minimal .xlsx in memory.

    Args:
        sheets: mapping of sheet_name → list of rows (each row a list of values).
    """
    import openpyxl

    wb = openpyxl.Workbook()
    # openpyxl creates a default "Sheet" — remove it if we supply our own.
    default_sheet = wb.active

    if sheets:
        first = True
        for name, rows in sheets.items():
            if first:
                ws = default_sheet
                ws.title = name
                first = False
            else:
                ws = wb.create_sheet(title=name)
            for row in rows:
                ws.append(row)
    else:
        # Leave default sheet empty but present.
        pass

    buf = io.BytesIO()
    wb.save(buf)
    return buf.getvalue()


def _build_csv(rows: list[list[str]]) -> bytes:
    import csv
    buf = io.StringIO()
    writer = csv.writer(buf)
    for row in rows:
        writer.writerow(row)
    return buf.getvalue().encode("utf-8")


# ---------------------------------------------------------------------------
# XLSX tests
# ---------------------------------------------------------------------------

class TestExtractXlsx:
    def test_returns_xlsx_result(self):
        raw = _build_xlsx({"Data": [["A", "B"], [1, 2]]})
        result = extract_xlsx(raw)
        assert isinstance(result, XlsxResult)

    def test_sheet_names_captured(self):
        raw = _build_xlsx({"Revenue": [["Q", "Amount"]], "Costs": [["Q", "Amount"]]})
        result = extract_xlsx(raw)
        assert "Revenue" in result.sheet_names
        assert "Costs" in result.sheet_names

    def test_row_count_matches(self):
        raw = _build_xlsx({"Sheet1": [["H1", "H2"], ["v1", "v2"], ["v3", "v4"]]})
        result = extract_xlsx(raw)
        assert result.row_count == 3  # header + 2 data rows

    def test_markdown_table_has_header_and_separator(self):
        raw = _build_xlsx({"Products": [["Name", "Price"], ["Widget", 9.99]]})
        result = extract_xlsx(raw)
        assert "|" in result.tables_as_markdown
        assert "---" in result.tables_as_markdown
        assert "Name" in result.tables_as_markdown
        assert "Price" in result.tables_as_markdown

    def test_full_text_equals_tables_as_markdown(self):
        raw = _build_xlsx({"S": [["X", "Y"], [1, 2]]})
        result = extract_xlsx(raw)
        assert result.full_text == result.tables_as_markdown

    def test_language_detected_for_english_headers(self):
        raw = _build_xlsx(
            {"Report": [
                ["the", "and", "of", "to", "in"],
                ["is", "it", "that", "the", "and"],
            ]}
        )
        result = extract_xlsx(raw)
        # May detect English from repeated stop words.
        assert result.language in (None, "en", "es", "fr", "de")

    def test_empty_workbook_returns_result(self):
        raw = _build_xlsx()
        result = extract_xlsx(raw)
        assert isinstance(result, XlsxResult)

    def test_result_is_frozen(self):
        raw = _build_xlsx({"S": [["A", "B"]]})
        result = extract_xlsx(raw)
        with pytest.raises((AttributeError, TypeError)):
            result.full_text = "mutated"  # type: ignore[misc]

    def test_invalid_bytes_raises(self):
        with pytest.raises(Exception):
            extract_xlsx(b"not an xlsx or csv")


# ---------------------------------------------------------------------------
# CSV tests
# ---------------------------------------------------------------------------

class TestExtractCsv:
    def test_csv_filename_hint_triggers_csv_path(self):
        raw = _build_csv([["Name", "Age"], ["Alice", "30"], ["Bob", "25"]])
        result = extract_xlsx(raw, filename="data.csv")
        assert isinstance(result, XlsxResult)
        assert result.sheet_names == ("Sheet1",)

    def test_csv_row_count(self):
        raw = _build_csv([["Col1", "Col2"], ["a", "b"], ["c", "d"], ["e", "f"]])
        result = extract_xlsx(raw, filename="test.csv")
        assert result.row_count == 4  # header + 3 rows

    def test_csv_markdown_contains_header(self):
        raw = _build_csv([["Product", "Revenue"], ["Widget", "1000"]])
        result = extract_xlsx(raw, filename="sales.csv")
        assert "Product" in result.tables_as_markdown
        assert "Revenue" in result.tables_as_markdown
        assert "---" in result.tables_as_markdown

    def test_csv_empty_returns_empty_result(self):
        result = extract_xlsx(b"", filename="empty.csv")
        assert result.row_count == 0
        assert result.tables_as_markdown == ""

    def test_csv_pipe_characters_escaped_in_cells(self):
        raw = _build_csv([["Desc", "Value"], ["a|b", "1"]])
        result = extract_xlsx(raw, filename="data.csv")
        # The pipe in "a|b" must be escaped so it doesn't break Markdown table.
        assert "a\\|b" in result.tables_as_markdown

    def test_csv_unicode_content(self):
        raw = "Nombre,Valor\nÁlvaro,42\nLuís,99\n".encode("utf-8")
        result = extract_xlsx(raw, filename="unicode.csv")
        assert "Nombre" in result.tables_as_markdown
