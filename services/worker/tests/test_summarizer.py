"""Tests for atlas_worker.compiler.summarizer.

Coverage:
  - summarize_source: valid text returns correct Summary fields
  - summarize_source: word_count matches split count of returned text
  - summarize_source: model name preserved from GenerateResult
  - summarize_source: generation_time_ms is non-negative integer
  - summarize_source: empty text raises ValueError (no LLM call)
  - summarize_source: whitespace-only text raises ValueError
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest

from atlas_worker.compiler.summarizer import Summary, summarize_source
from atlas_worker.inference.models import GenerateResult


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_router(response_text: str, model: str = "test-model") -> MagicMock:
    """Return a mock InferenceRouter whose generate() returns the given text."""
    result = GenerateResult(
        text=response_text,
        model=model,
        backend="ollama",
        tokens_used=50,
        duration_ms=100,
    )
    router = MagicMock()
    router.generate = AsyncMock(return_value=result)
    return router


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_summarize_returns_summary_dataclass() -> None:
    router = _make_router("This is the summary.\n\nSecond paragraph here.")
    result = await summarize_source("Some long source text.", "src_001", router)
    assert isinstance(result, Summary)


@pytest.mark.asyncio
async def test_summarize_text_matches_response() -> None:
    expected = "This is the summary.\n\nSecond paragraph here."
    router = _make_router(expected)
    result = await summarize_source("Some long source text.", "src_001", router)
    assert result.text == expected.strip()


@pytest.mark.asyncio
async def test_summarize_word_count_is_correct() -> None:
    text = "Word one two three four five."
    router = _make_router(text)
    result = await summarize_source("Input text here.", "src_002", router)
    assert result.word_count == len(text.split())


@pytest.mark.asyncio
async def test_summarize_model_name_preserved() -> None:
    router = _make_router("Summary text.", model="gemma4:27b")
    result = await summarize_source("Input text here.", "src_003", router)
    assert result.model == "gemma4:27b"


@pytest.mark.asyncio
async def test_summarize_generation_time_non_negative() -> None:
    router = _make_router("Summary text.")
    result = await summarize_source("Input text here.", "src_004", router)
    assert result.generation_time_ms >= 0


@pytest.mark.asyncio
async def test_summarize_calls_router_generate_once() -> None:
    router = _make_router("Summary text.")
    await summarize_source("Some source text.", "src_005", router)
    router.generate.assert_called_once()


@pytest.mark.asyncio
async def test_summarize_passes_source_id_in_prompt() -> None:
    router = _make_router("Summary text.")
    await summarize_source("Some source text.", "src_custom_id", router)
    call_args = router.generate.call_args
    prompt = call_args.args[0]
    assert "src_custom_id" in prompt


@pytest.mark.asyncio
async def test_summarize_empty_text_raises_value_error() -> None:
    router = _make_router("Summary.")
    with pytest.raises(ValueError, match="text must not be empty"):
        await summarize_source("", "src_006", router)
    router.generate.assert_not_called()


@pytest.mark.asyncio
async def test_summarize_whitespace_only_raises_value_error() -> None:
    router = _make_router("Summary.")
    with pytest.raises(ValueError):
        await summarize_source("   \n\t  ", "src_007", router)
    router.generate.assert_not_called()


@pytest.mark.asyncio
async def test_summarize_strips_trailing_whitespace_from_response() -> None:
    router = _make_router("  Summary with spaces.  \n\n")
    result = await summarize_source("Source text.", "src_008", router)
    assert result.text == "Summary with spaces."
