"""Source summarizer — compiler step 2 (LLM).

Inputs:
  - source text (plain string, extracted from source note)
  - source_id (for citation anchoring in the summary)
  - InferenceRouter instance
  - optional model override

Outputs:
  - Summary dataclass: text, word_count, model, generation_time_ms

Failure modes:
  - router.generate() raises → propagated to caller; no partial write
  - Empty text raises ValueError before any LLM call
"""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass

from atlas_worker.inference.models import GenerateResult
from atlas_worker.inference.prompts import SUMMARY_PROMPT, SYSTEM_PROMPT
from atlas_worker.inference.router import InferenceRouter

logger = logging.getLogger(__name__)

# Temperature for synthesis: slightly creative but still grounded.
_SUMMARY_TEMPERATURE = 0.3
_SUMMARY_MAX_TOKENS = 2048


# ---------------------------------------------------------------------------
# Data contract
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class Summary:
    """Result of an LLM-generated source summary.

    Attributes:
        text:               Markdown-formatted summary (3–5 paragraphs).
        word_count:         Approximate word count of the summary text.
        model:              Model name used for generation (from GenerateResult).
        generation_time_ms: Wall-clock time of the router.generate() call in ms.
    """

    text: str
    word_count: int
    model: str
    generation_time_ms: int


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


async def summarize_source(
    text: str,
    source_id: str,
    router: InferenceRouter,
    *,
    model: str | None = None,
) -> Summary:
    """Generate a 3–5 paragraph Markdown summary of a source text.

    Args:
        text:      Source text to summarize. Must be non-empty.
        source_id: Identifier used in [source:…] citation anchors.
        router:    InferenceRouter to call for LLM generation.
        model:     Optional model override; uses router default if None.

    Returns:
        Summary with generated text, word count, model name, and latency.

    Raises:
        ValueError: If text is empty or blank.
    """
    if not text or not text.strip():
        raise ValueError("summarize_source: text must not be empty")

    prompt = SUMMARY_PROMPT.format(source_id=source_id, text=text)

    t0 = time.monotonic()
    result: GenerateResult = await router.generate(
        prompt,
        system=SYSTEM_PROMPT,
        model=model,
        temperature=_SUMMARY_TEMPERATURE,
        max_tokens=_SUMMARY_MAX_TOKENS,
    )
    elapsed_ms = int((time.monotonic() - t0) * 1000)

    summary_text = result.text.strip()
    word_count = len(summary_text.split())

    logger.info(
        "summarize_source: source_id=%s model=%s words=%d time=%dms",
        source_id,
        result.model,
        word_count,
        elapsed_ms,
    )

    return Summary(
        text=summary_text,
        word_count=word_count,
        model=result.model,
        generation_time_ms=elapsed_ms,
    )
