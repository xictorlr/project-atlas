"""Tests for atlas_worker.compiler.translator.

Coverage:
  - translate_text: returns TranslationResult dataclass
  - translate_text: original_text preserved unchanged
  - translate_text: translated_text matches router response
  - translate_text: source_language and target_language recorded correctly
  - translate_text: model name preserved from GenerateResult
  - translate_text: custom source_language kwarg respected
  - translate_text: prompt includes source and target language names
  - translate_text: empty text raises ValueError (no LLM call)
  - translate_text: whitespace-only text raises ValueError
  - TranslationResult is a frozen dataclass
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest

from atlas_worker.compiler.translator import TranslationResult, translate_text
from atlas_worker.inference.models import GenerateResult


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_router(response_text: str, model: str = "test-model") -> MagicMock:
    result = GenerateResult(
        text=response_text,
        model=model,
        backend="ollama",
        tokens_used=60,
        duration_ms=150,
    )
    router = MagicMock()
    router.generate = AsyncMock(return_value=result)
    return router


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_translate_returns_translation_result() -> None:
    router = _make_router("El texto traducido aquí.")
    result = await translate_text("The text here.", "Spanish", router)
    assert isinstance(result, TranslationResult)


@pytest.mark.asyncio
async def test_translate_original_text_preserved() -> None:
    original = "The API migration is complete."
    router = _make_router("La migración de la API está completa.")
    result = await translate_text(original, "Spanish", router)
    assert result.original_text == original


@pytest.mark.asyncio
async def test_translate_translated_text_from_response() -> None:
    translated = "La migración de la API está completa."
    router = _make_router(translated)
    result = await translate_text("The API migration is complete.", "Spanish", router)
    assert result.translated_text == translated


@pytest.mark.asyncio
async def test_translate_default_source_language_is_english() -> None:
    router = _make_router("Hola mundo.")
    result = await translate_text("Hello world.", "Spanish", router)
    assert result.source_language == "English"


@pytest.mark.asyncio
async def test_translate_target_language_recorded() -> None:
    router = _make_router("Hola mundo.")
    result = await translate_text("Hello world.", "Spanish", router)
    assert result.target_language == "Spanish"


@pytest.mark.asyncio
async def test_translate_custom_source_language() -> None:
    router = _make_router("Hello world.")
    result = await translate_text(
        "Hola mundo.", "English", router, source_language="Spanish"
    )
    assert result.source_language == "Spanish"
    assert result.target_language == "English"


@pytest.mark.asyncio
async def test_translate_model_name_preserved() -> None:
    router = _make_router("Hola.", model="gemma4:27b")
    result = await translate_text("Hello.", "Spanish", router)
    assert result.model == "gemma4:27b"


@pytest.mark.asyncio
async def test_translate_prompt_contains_languages() -> None:
    router = _make_router("Traducido.")
    await translate_text("Original text.", "French", router, source_language="English")
    call_args = router.generate.call_args
    prompt = call_args.args[0]
    assert "English" in prompt
    assert "French" in prompt


@pytest.mark.asyncio
async def test_translate_prompt_contains_source_text() -> None:
    router = _make_router("Traducido.")
    await translate_text("My special source text.", "Spanish", router)
    call_args = router.generate.call_args
    prompt = call_args.args[0]
    assert "My special source text." in prompt


@pytest.mark.asyncio
async def test_translate_empty_text_raises_value_error() -> None:
    router = _make_router("Hola.")
    with pytest.raises(ValueError, match="text must not be empty"):
        await translate_text("", "Spanish", router)
    router.generate.assert_not_called()


@pytest.mark.asyncio
async def test_translate_whitespace_only_raises_value_error() -> None:
    router = _make_router("Hola.")
    with pytest.raises(ValueError):
        await translate_text("   \n  ", "Spanish", router)
    router.generate.assert_not_called()


@pytest.mark.asyncio
async def test_translate_strips_trailing_whitespace() -> None:
    router = _make_router("  Texto traducido.  \n")
    result = await translate_text("Translated text.", "Spanish", router)
    assert result.translated_text == "Texto traducido."


def test_translation_result_is_frozen() -> None:
    tr = TranslationResult(
        original_text="Hello.",
        translated_text="Hola.",
        source_language="English",
        target_language="Spanish",
        model="test",
    )
    with pytest.raises(Exception):
        tr.translated_text = "changed"  # type: ignore[misc]
