"""Evidence pack assembly — given search results, build grounded EvidenceExcerpt
and EvidencePack structures for consumption by answer generation.

Workflow:
  Input:  query string + list[SearchResult] (ranked by score)
  Output: EvidencePack (frozen Pydantic model matching models/evidence.py)

Citation format: [^{slug}] footnotes appended to a Markdown block.
"""

from __future__ import annotations

import logging
import re
import uuid
from datetime import datetime, timezone

from atlas_api.models.evidence import EvidenceExcerpt, EvidencePack
from atlas_api.search.models import SearchResult

logger = logging.getLogger(__name__)

_EXCERPT_WINDOW = 500  # chars; ~half-page of context
_WIKILINK_RE = re.compile(r"\[\[([^\]]+)\]\]")


def _extract_passage(body: str, snippet_hint: str, window: int = _EXCERPT_WINDOW) -> str:
    """Return a passage from body anchored on the snippet_hint position.

    Falls back to the first `window` chars when the hint is not found.
    """
    if not body:
        return ""

    anchor = body.find(snippet_hint.lstrip("...").rstrip("...").strip()[:40])
    if anchor == -1:
        return body[:window]

    start = max(0, anchor - window // 4)
    end = min(len(body), start + window)
    passage = body[start:end].strip()
    if start > 0:
        passage = "..." + passage
    if end < len(body):
        passage = passage + "..."
    return passage


def _source_id_from_result(result: SearchResult) -> str:
    """Derive a stable source_id string from the note slug.

    For source notes the frontmatter source_id should be used; since we only
    have SearchResult here (no frontmatter), we use the slug as a stable key.
    The caller can enrich this from the full NoteRecord when needed.
    """
    return result.slug


def _location_hint(result: SearchResult) -> str:
    """Human-readable location hint for the excerpt."""
    return f"{result.note_type}/{result.slug}"


def build_evidence_pack(
    workspace_id: str,
    query: str,
    results: list[SearchResult],
    note_bodies: dict[str, str],
    max_sources: int = 10,
) -> EvidencePack:
    """Assemble an EvidencePack from ranked search results.

    Args:
        workspace_id: owning workspace.
        query: original user query.
        results: ranked SearchResult list (highest score first).
        note_bodies: mapping of note slug -> full body text for passage extraction.
        max_sources: cap on number of excerpts.

    Returns:
        An immutable EvidencePack ready for the answer layer.
    """
    top = results[:max_sources]
    excerpts: list[EvidenceExcerpt] = []
    note_refs: list[str] = []

    for i, result in enumerate(top):
        body = note_bodies.get(result.slug, "")
        passage = _extract_passage(body, result.snippet, window=_EXCERPT_WINDOW)

        excerpt = EvidenceExcerpt(
            source_id=_source_id_from_result(result),
            chunk_index=i,
            text=passage,
            score=result.score,
            location_hint=_location_hint(result),
        )
        excerpts.append(excerpt)
        note_refs.append(result.note_path)

    return EvidencePack(
        id=str(uuid.uuid4()),
        workspace_id=workspace_id,
        query=query,
        excerpts=tuple(excerpts),
        note_refs=tuple(note_refs),
        model=None,
        generated_at=datetime.now(tz=timezone.utc).isoformat(),
    )


def format_markdown_citations(pack: EvidencePack) -> str:
    """Render Markdown footnote-style citations from an EvidencePack.

    Output format:
        [^slug-0]: Note title/location — passage excerpt

    Suitable for appending to a generated answer block.
    """
    lines: list[str] = []
    for excerpt in pack.excerpts:
        slug_key = re.sub(r"[^a-z0-9-]", "-", excerpt.source_id.lower())
        ref = f"[^{slug_key}]"
        trimmed = excerpt.text[:200].replace("\n", " ").strip()
        if len(excerpt.text) > 200:
            trimmed += "..."
        lines.append(f"{ref}: **{excerpt.location_hint}** — {trimmed}")
    return "\n".join(lines)
