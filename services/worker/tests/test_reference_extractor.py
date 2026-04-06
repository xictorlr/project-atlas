"""Tests for atlas_worker.compiler.reference_extractor.

Coverage:
  - extract_references: valid JSON array → correct ExtractedReference list
  - extract_references: title field required — entries without title skipped
  - extract_references: authors list parsed correctly
  - extract_references: year parsed as int, null on missing/invalid
  - extract_references: ref_type normalised — invalid value → "other"
  - extract_references: malformed JSON → empty list (no crash)
  - extract_references: JSON object (not array) → empty list
  - extract_references: empty text raises ValueError (no LLM call)
  - extract_references: model call happens exactly once per invocation
  - ExtractedReference is a frozen dataclass
"""

from __future__ import annotations

import json
from unittest.mock import AsyncMock, MagicMock

import pytest

from atlas_worker.compiler.reference_extractor import (
    ExtractedReference,
    _parse_references_json,
    extract_references,
)
from atlas_worker.inference.models import GenerateResult


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_router(response_payload: list | str, model: str = "test-model") -> MagicMock:
    if isinstance(response_payload, list):
        text = json.dumps(response_payload)
    else:
        text = response_payload
    result = GenerateResult(
        text=text,
        model=model,
        backend="ollama",
        tokens_used=40,
        duration_ms=100,
    )
    router = MagicMock()
    router.generate = AsyncMock(return_value=result)
    return router


_VALID_REFS = [
    {
        "title": "Designing Data-Intensive Applications",
        "authors": ["Martin Kleppmann"],
        "year": 2017,
        "ref_type": "book",
        "context": "Referenced when discussing distributed systems design.",
    },
    {
        "title": "Attention Is All You Need",
        "authors": ["Vaswani et al."],
        "year": 2017,
        "ref_type": "paper",
        "context": "Foundation of the transformer architecture used in the project.",
    },
]


# ---------------------------------------------------------------------------
# Tests — extract_references (integration with mock router)
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_extract_returns_list() -> None:
    router = _make_router(_VALID_REFS)
    result = await extract_references("Some text with references.", router)
    assert isinstance(result, list)


@pytest.mark.asyncio
async def test_extract_correct_number_of_references() -> None:
    router = _make_router(_VALID_REFS)
    result = await extract_references("Some text with references.", router)
    assert len(result) == 2


@pytest.mark.asyncio
async def test_extract_title_parsed() -> None:
    router = _make_router(_VALID_REFS)
    result = await extract_references("Some text.", router)
    assert result[0].title == "Designing Data-Intensive Applications"


@pytest.mark.asyncio
async def test_extract_authors_parsed() -> None:
    router = _make_router(_VALID_REFS)
    result = await extract_references("Some text.", router)
    assert result[0].authors == ["Martin Kleppmann"]


@pytest.mark.asyncio
async def test_extract_year_parsed_as_int() -> None:
    router = _make_router(_VALID_REFS)
    result = await extract_references("Some text.", router)
    assert result[0].year == 2017
    assert isinstance(result[0].year, int)


@pytest.mark.asyncio
async def test_extract_ref_type_parsed() -> None:
    router = _make_router(_VALID_REFS)
    result = await extract_references("Some text.", router)
    assert result[0].ref_type == "book"
    assert result[1].ref_type == "paper"


@pytest.mark.asyncio
async def test_extract_context_parsed() -> None:
    router = _make_router(_VALID_REFS)
    result = await extract_references("Some text.", router)
    assert "distributed systems" in result[0].context


@pytest.mark.asyncio
async def test_extract_empty_text_raises_value_error() -> None:
    router = _make_router(_VALID_REFS)
    with pytest.raises(ValueError, match="text must not be empty"):
        await extract_references("", router)
    router.generate.assert_not_called()


@pytest.mark.asyncio
async def test_extract_calls_router_once() -> None:
    router = _make_router(_VALID_REFS)
    await extract_references("Some source text.", router)
    router.generate.assert_called_once()


# ---------------------------------------------------------------------------
# Tests — _parse_references_json (unit)
# ---------------------------------------------------------------------------


def test_parse_valid_array() -> None:
    refs = _parse_references_json(json.dumps(_VALID_REFS))
    assert len(refs) == 2


def test_parse_malformed_json_returns_empty() -> None:
    refs = _parse_references_json("NOT JSON {{{ broken")
    assert refs == []


def test_parse_json_object_not_array_returns_empty() -> None:
    refs = _parse_references_json(json.dumps({"title": "Oops"}))
    assert refs == []


def test_parse_skips_entry_without_title() -> None:
    data = [
        {"authors": ["A. Author"], "year": 2020, "ref_type": "book", "context": "ctx"},
        {"title": "Valid Title", "authors": [], "year": None, "ref_type": "article", "context": ""},
    ]
    refs = _parse_references_json(json.dumps(data))
    # First entry has no title — should be skipped.
    assert len(refs) == 1
    assert refs[0].title == "Valid Title"


def test_parse_invalid_ref_type_falls_back_to_other() -> None:
    data = [
        {
            "title": "Some Work",
            "authors": [],
            "year": 2021,
            "ref_type": "UNKNOWN_TYPE",
            "context": "ctx",
        }
    ]
    refs = _parse_references_json(json.dumps(data))
    assert refs[0].ref_type == "other"


def test_parse_null_year_stays_none() -> None:
    data = [
        {
            "title": "Undated Work",
            "authors": [],
            "year": None,
            "ref_type": "article",
            "context": "",
        }
    ]
    refs = _parse_references_json(json.dumps(data))
    assert refs[0].year is None


def test_parse_string_year_casts_to_int() -> None:
    data = [
        {
            "title": "Dated Work",
            "authors": [],
            "year": "2019",
            "ref_type": "article",
            "context": "",
        }
    ]
    refs = _parse_references_json(json.dumps(data))
    assert refs[0].year == 2019
    assert isinstance(refs[0].year, int)


def test_parse_invalid_year_string_becomes_none() -> None:
    data = [
        {
            "title": "Bad Year",
            "authors": [],
            "year": "not-a-year",
            "ref_type": "article",
            "context": "",
        }
    ]
    refs = _parse_references_json(json.dumps(data))
    assert refs[0].year is None


# ---------------------------------------------------------------------------
# Tests — frozen dataclass
# ---------------------------------------------------------------------------


def test_extracted_reference_is_frozen() -> None:
    ref = ExtractedReference(
        title="Test Book",
        authors=["Author"],
        year=2020,
        ref_type="book",
        context="Used in analysis.",
    )
    with pytest.raises(Exception):
        ref.title = "Changed"  # type: ignore[misc]
