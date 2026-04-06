"""Vault content translator — compiler step 8 (LLM, optional).

Inputs:
  - text to translate (plain string — may include Markdown formatting)
  - target_language (e.g. "Spanish", "French")
  - source_language (default "English" — Whisper produces EN by default)
  - InferenceRouter instance

Outputs:
  - TranslationResult dataclass

Failure modes:
  - router.generate() raises → propagated to caller
  - Empty text raises ValueError before any LLM call

EN→ES use case (primary):
  - Whisper transcribes EN audio → EN text (maximum accuracy)
  - translator sends EN text through router.generate() with TRANSLATION_PROMPT
  - Both versions stored in vault note:
      ## Transcript (Original — English)
      [00:00:00] …
      ## Transcripción (Traducido — Español)
      [00:00:00] …
  - If source is already ES, translation is skipped at the job level.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass

from atlas_worker.inference.models import GenerateResult
from atlas_worker.inference.prompts import SYSTEM_PROMPT, TRANSLATION_PROMPT
from atlas_worker.inference.router import InferenceRouter

logger = logging.getLogger(__name__)

# Temperature 0.0 for translation — deterministic, structure-preserving output.
_TRANSLATION_TEMPERATURE = 0.0
_TRANSLATION_MAX_TOKENS = 8192


# ---------------------------------------------------------------------------
# Data contract
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class TranslationResult:
    """Result of an LLM-powered translation.

    Attributes:
        original_text:   The source text passed to the translator.
        translated_text: The translated output from the LLM.
        source_language: Language of the original text (e.g. "English").
        target_language: Language of the translated text (e.g. "Spanish").
        model:           LLM model name used for the translation.
    """

    original_text: str
    translated_text: str
    source_language: str
    target_language: str
    model: str


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


async def translate_text(
    text: str,
    target_language: str,
    router: InferenceRouter,
    *,
    source_language: str = "English",
    model: str | None = None,
) -> TranslationResult:
    """Translate text from source_language to target_language.

    Markdown formatting, wikilinks, frontmatter keys, and timestamps are
    preserved by the prompt instructions.

    Args:
        text:            Source text to translate. Must be non-empty.
        target_language: Name of the target language (e.g. "Spanish").
        router:          InferenceRouter for LLM generation.
        source_language: Name of the source language (default "English").
        model:           Optional model override; uses router default if None.

    Returns:
        TranslationResult with original and translated text, language names,
        and the model used.

    Raises:
        ValueError: If text is empty or blank.
    """
    if not text or not text.strip():
        raise ValueError("translate_text: text must not be empty")

    prompt = TRANSLATION_PROMPT.format(
        source_language=source_language,
        target_language=target_language,
        text=text,
    )

    result: GenerateResult = await router.generate(
        prompt,
        system=SYSTEM_PROMPT,
        model=model,
        temperature=_TRANSLATION_TEMPERATURE,
        max_tokens=_TRANSLATION_MAX_TOKENS,
    )

    translated = result.text.strip()

    logger.info(
        "translate_text: %s → %s model=%s chars_in=%d chars_out=%d",
        source_language,
        target_language,
        result.model,
        len(text),
        len(translated),
    )

    return TranslationResult(
        original_text=text,
        translated_text=translated,
        source_language=source_language,
        target_language=target_language,
        model=result.model,
    )
