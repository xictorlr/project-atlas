"""Reference / bibliography extractor — compiler step 5 (LLM).

Inputs:
  - source text (plain string)
  - InferenceRouter instance

Outputs:
  - list[ExtractedReference] — bibliographic entries found in the text

Failure modes:
  - router.generate() raises → propagated to caller
  - Malformed JSON from LLM → logs warning, returns empty list (no crash)
  - Empty text raises ValueError before any LLM call
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field

from atlas_worker.inference.models import GenerateResult
from atlas_worker.inference.prompts import REFERENCE_EXTRACTION_PROMPT, SYSTEM_PROMPT
from atlas_worker.inference.router import InferenceRouter

logger = logging.getLogger(__name__)

# Temperature 0.0 — extraction must be deterministic.
_REF_TEMPERATURE = 0.0
_REF_MAX_TOKENS = 2048

_VALID_REF_TYPES = frozenset({"book", "article", "website", "report", "paper", "other"})


# ---------------------------------------------------------------------------
# Data contract
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class ExtractedReference:
    """A bibliographic reference found in source text.

    Attributes:
        title:    Full title of the referenced work.
        authors:  List of author names (may be empty).
        year:     Publication year as integer (nullable).
        ref_type: Classification: book | article | website | report | paper | other.
        context:  One sentence describing how the reference is used in the text.
    """

    title: str
    authors: list[str]
    year: int | None
    ref_type: str
    context: str


# ---------------------------------------------------------------------------
# JSON parsing helpers
# ---------------------------------------------------------------------------


def _parse_reference(raw: dict) -> ExtractedReference | None:
    """Parse a single reference dict from the LLM JSON array.

    Returns None if the entry is missing the mandatory `title` field.
    """
    title = str(raw.get("title", "")).strip()
    if not title:
        logger.warning("reference_extractor: skipping entry with missing title")
        return None

    authors_raw = raw.get("authors") or []
    authors = [str(a) for a in authors_raw if a]

    year_raw = raw.get("year")
    year: int | None = None
    if year_raw is not None:
        try:
            year = int(year_raw)
        except (TypeError, ValueError):
            logger.warning("reference_extractor: invalid year value %r — treating as null", year_raw)

    ref_type = str(raw.get("ref_type", "other")).lower()
    if ref_type not in _VALID_REF_TYPES:
        ref_type = "other"

    context = str(raw.get("context", "")).strip()

    return ExtractedReference(
        title=title,
        authors=authors,
        year=year,
        ref_type=ref_type,
        context=context,
    )


def _parse_references_json(raw_json: str) -> list[ExtractedReference]:
    """Parse LLM JSON array into a list of ExtractedReference.

    Returns empty list on malformed JSON rather than crashing.
    """
    try:
        data = json.loads(raw_json)
    except json.JSONDecodeError as exc:
        logger.warning("reference_extractor: malformed JSON from LLM — %s", exc)
        return []

    if not isinstance(data, list):
        logger.warning(
            "reference_extractor: expected JSON array, got %s — returning empty",
            type(data).__name__,
        )
        return []

    references: list[ExtractedReference] = []
    for item in data:
        if not isinstance(item, dict):
            continue
        ref = _parse_reference(item)
        if ref is not None:
            references.append(ref)

    return references


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


async def extract_references(
    text: str,
    router: InferenceRouter,
    *,
    model: str | None = None,
) -> list[ExtractedReference]:
    """Extract bibliographic references from source text.

    Args:
        text:   Source text to analyse. Must be non-empty.
        router: InferenceRouter for LLM generation.
        model:  Optional model override; uses router default if None.

    Returns:
        List of ExtractedReference objects found in the text.
        Returns empty list on malformed LLM output.

    Raises:
        ValueError: If text is empty or blank.
    """
    if not text or not text.strip():
        raise ValueError("extract_references: text must not be empty")

    prompt = REFERENCE_EXTRACTION_PROMPT.format(text=text)

    result: GenerateResult = await router.generate(
        prompt,
        system=SYSTEM_PROMPT,
        model=model,
        temperature=_REF_TEMPERATURE,
        max_tokens=_REF_MAX_TOKENS,
        format_json=True,
    )

    references = _parse_references_json(result.text.strip())

    logger.info(
        "extract_references: model=%s references_found=%d",
        result.model,
        len(references),
    )

    return references
