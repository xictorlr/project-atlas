"""Cross-source concept synthesizer — compiler step 6 (LLM).

Inputs:
  - sources: list of dicts with keys: source_id, title, text (extracted content)
  - entities: list of entity names/slugs discovered across all sources
  - InferenceRouter instance

Outputs:
  - list[SynthesizedConcept] — one concept article per discovered topic cluster

Clustering strategy (lightweight, no external dependencies):
  - Co-occurrence counting: terms that appear in multiple sources form a cluster.
  - A cluster needs >= 2 sources to qualify for synthesis.
  - Concepts are named by their most frequent shared term.

Failure modes:
  - router.generate() raises → error logged, that concept skipped, others continue
  - Empty source list returns empty list without LLM call
"""

from __future__ import annotations

import logging
import re
from collections import Counter, defaultdict
from dataclasses import dataclass, field

from atlas_worker.compiler.source_notes import make_slug
from atlas_worker.inference.models import GenerateResult
from atlas_worker.inference.prompts import CONCEPT_SYNTHESIS_PROMPT, SYSTEM_PROMPT
from atlas_worker.inference.router import InferenceRouter

logger = logging.getLogger(__name__)

# Temperature 0.3 — synthesis requires some creative structuring.
_SYNTHESIS_TEMPERATURE = 0.3
_SYNTHESIS_MAX_TOKENS = 4096

# Minimum number of sources a concept must appear in to warrant synthesis.
_MIN_SOURCES_PER_CONCEPT = 2

# Maximum concepts synthesized per compilation run (cost/time guard).
_MAX_CONCEPTS = 20


# ---------------------------------------------------------------------------
# Data contract
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class SynthesizedConcept:
    """A concept article synthesized from multiple sources.

    Attributes:
        title:       Human-readable concept name.
        slug:        URL-safe slug for the vault note filename.
        body:        Markdown body of the concept article (includes citations).
        source_ids:  IDs of all sources used for synthesis.
        entity_refs: Slugs of related entities (for wikilinks).
        model:       LLM model used for generation.
        confidence:  Heuristic confidence score 0.0–1.0 based on source coverage.
    """

    title: str
    slug: str
    body: str
    source_ids: list[str]
    entity_refs: list[str]
    model: str
    confidence: float


# ---------------------------------------------------------------------------
# Clustering helpers
# ---------------------------------------------------------------------------

# Common English words to exclude from concept detection.
_STOP_WORDS: frozenset[str] = frozenset(
    {
        "the", "a", "an", "and", "or", "but", "in", "on", "at", "to",
        "of", "as", "is", "are", "was", "were", "be", "been", "being",
        "have", "has", "had", "do", "does", "did", "will", "would",
        "could", "should", "may", "might", "must", "shall", "can",
        "not", "no", "yes", "from", "with", "about", "into", "through",
        "for", "by", "this", "that", "these", "those", "it", "its",
        "he", "she", "they", "we", "you", "new", "old", "first",
        "last", "next", "same", "also", "then", "than", "when", "where",
        "which", "who", "what", "how", "if", "so", "after", "before",
        "between", "during", "above", "below", "use", "used", "using",
    }
)

_TERM_RE = re.compile(r"\b[a-z][a-z0-9_-]{2,}\b")


def _extract_terms(text: str) -> list[str]:
    """Extract lowercase multi-character terms from text, excluding stop words."""
    return [
        m.group()
        for m in _TERM_RE.finditer(text.lower())
        if m.group() not in _STOP_WORDS
    ]


def _build_clusters(
    sources: list[dict],
) -> list[tuple[str, list[str]]]:
    """Return (concept_name, [source_id, …]) pairs for cross-source concepts.

    A concept is a term that appears in >= _MIN_SOURCES_PER_CONCEPT sources.
    Returns at most _MAX_CONCEPTS clusters, sorted by source coverage descending.
    """
    # term → set of source_ids that contain it
    term_sources: dict[str, set[str]] = defaultdict(set)

    for source in sources:
        source_id = source.get("source_id", "")
        text = source.get("text", "") + " " + source.get("title", "")
        terms = _extract_terms(text)
        # Count only unique terms per source to avoid noise from repetition.
        for term in set(terms):
            term_sources[term].add(source_id)

    # Keep only terms appearing in enough sources.
    candidates = [
        (term, sorted(sids))
        for term, sids in term_sources.items()
        if len(sids) >= _MIN_SOURCES_PER_CONCEPT
    ]

    # Sort by breadth (number of sources) descending, then alphabetically.
    candidates.sort(key=lambda x: (-len(x[1]), x[0]))

    # Deduplicate: if a term is a substring of a higher-ranked term already
    # selected, skip it to avoid near-duplicate concepts.
    selected: list[tuple[str, list[str]]] = []
    selected_terms: set[str] = set()

    for term, sids in candidates:
        if len(selected) >= _MAX_CONCEPTS:
            break
        if any(term in existing or existing in term for existing in selected_terms):
            continue
        selected.append((term, sids))
        selected_terms.add(term)

    return selected


# ---------------------------------------------------------------------------
# Synthesis helpers
# ---------------------------------------------------------------------------


def _build_sources_block(sources: list[dict], source_ids: list[str]) -> str:
    """Build the {sources_block} string for the synthesis prompt."""
    parts: list[str] = []
    for source in sources:
        if source.get("source_id") not in source_ids:
            continue
        sid = source.get("source_id", "unknown")
        title = source.get("title", sid)
        text = source.get("text", "")[:3000]  # cap per-source context
        parts.append(f"### [{sid}] {title}\n\n{text}")
    return "\n\n---\n\n".join(parts)


def _build_entity_list(entity_slugs: list[str]) -> str:
    if not entity_slugs:
        return "(none)"
    return "\n".join(f"- {slug}" for slug in entity_slugs)


def _compute_confidence(source_ids: list[str], total_sources: int) -> float:
    """Coverage-based confidence: ratio of contributing sources."""
    if total_sources == 0:
        return 0.0
    return round(min(len(source_ids) / total_sources, 1.0), 2)


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


async def synthesize_concepts(
    sources: list[dict],
    entities: list[str],
    router: InferenceRouter,
    *,
    model: str | None = None,
) -> list[SynthesizedConcept]:
    """Cluster topics across sources and synthesize one concept article per cluster.

    Args:
        sources:  List of source dicts, each with keys:
                    source_id (str), title (str), text (str).
        entities: List of entity slug strings for wikilink injection.
        router:   InferenceRouter for LLM generation.
        model:    Optional model override; uses router default if None.

    Returns:
        List of SynthesizedConcept objects. Empty if no cross-source concepts found.
        Individual synthesis failures are logged and skipped — others still complete.
    """
    if not sources:
        logger.info("synthesize_concepts: no sources provided, returning empty")
        return []

    clusters = _build_clusters(sources)
    if not clusters:
        logger.info("synthesize_concepts: no cross-source concept clusters found")
        return []

    total_sources = len(sources)
    results: list[SynthesizedConcept] = []

    for concept_name, source_ids in clusters:
        slug = make_slug(concept_name)
        if not slug:
            continue

        sources_block = _build_sources_block(sources, source_ids)
        entity_list = _build_entity_list(entities)

        prompt = CONCEPT_SYNTHESIS_PROMPT.format(
            concept_name=concept_name,
            entity_list=entity_list,
            sources_block=sources_block,
        )

        try:
            result: GenerateResult = await router.generate(
                prompt,
                system=SYSTEM_PROMPT,
                model=model,
                temperature=_SYNTHESIS_TEMPERATURE,
                max_tokens=_SYNTHESIS_MAX_TOKENS,
            )
        except Exception as exc:
            logger.error(
                "synthesize_concepts: failed for concept=%r — %s", concept_name, exc
            )
            continue

        confidence = _compute_confidence(source_ids, total_sources)

        concept = SynthesizedConcept(
            title=concept_name,
            slug=slug,
            body=result.text.strip(),
            source_ids=source_ids,
            entity_refs=entities,
            model=result.model,
            confidence=confidence,
        )
        results.append(concept)

        logger.info(
            "synthesize_concepts: concept=%r sources=%d confidence=%.2f model=%s",
            concept_name,
            len(source_ids),
            confidence,
            result.model,
        )

    return results
