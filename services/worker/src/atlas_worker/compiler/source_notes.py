"""Source note generator — compiler step 1.

Inputs:
  - SourceRecord dataclass (title, source_id, workspace_id, extracted_text,
    provenance fields)
  - vault_root: Path to the vault directory

Outputs:
  - Writes vault/{workspace_id}/sources/{slug}.md
  - Returns SourceNoteResult with path, slug, and write action

Failure modes:
  - Missing required fields raise ValueError before any file I/O
  - ConflictRecord returned inside SourceNoteResult when user edits detected
"""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import NamedTuple

from atlas_worker.compiler.vault_writer import ConflictRecord, WriteResult, write_note

logger = logging.getLogger(__name__)

COMPILER_VERSION = "worker/compiler-v1"
_SLUG_MAX_LEN = 80  # schema: max 80 chars


# ---------------------------------------------------------------------------
# Data contracts
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class SourceProvenance:
    ingest_job_id: str
    content_hash: str  # sha256:…
    mime_type: str
    char_count: int
    ingested_by: str = "worker/ingest-v1"
    url: str | None = None
    retrieved_at: str | None = None  # ISO 8601


@dataclass(frozen=True)
class SourceRecord:
    source_id: str  # src_…
    workspace_id: str  # ws_…
    title: str
    extracted_text: str
    provenance: SourceProvenance
    tags: list[str] = field(default_factory=list)
    author: str | None = None
    published_at: str | None = None  # YYYY-MM-DD
    language: str | None = None
    # Pre-resolved entity/concept slugs from a prior extraction pass.
    entity_slugs: list[str] = field(default_factory=list)
    concept_slugs: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class SourceNoteResult:
    source_id: str
    slug: str
    path: Path
    action: str  # "created" | "updated" | "skipped" | "conflict"
    conflict: ConflictRecord | None = None


# ---------------------------------------------------------------------------
# Slug helpers
# ---------------------------------------------------------------------------


def make_slug(title: str, max_len: int = _SLUG_MAX_LEN) -> str:
    """Derive a deterministic URL-safe slug from a title.

    Rules (from frontmatter-schema.md):
      - Lowercase ASCII + digits + hyphens only.
      - No leading or trailing hyphens.
      - Max `max_len` characters.
    """
    slug = title.lower()
    slug = re.sub(r"[^a-z0-9\s-]", "", slug)
    slug = re.sub(r"[\s]+", "-", slug.strip())
    slug = re.sub(r"-{2,}", "-", slug)
    slug = slug.strip("-")
    return slug[:max_len].rstrip("-")


# ---------------------------------------------------------------------------
# Frontmatter builder
# ---------------------------------------------------------------------------


def _build_frontmatter(record: SourceRecord, slug: str, now: str) -> dict:
    prov = record.provenance
    provenance_block: dict = {
        "ingested_by": prov.ingested_by,
        "ingest_job_id": prov.ingest_job_id,
        "content_hash": prov.content_hash,
        "mime_type": prov.mime_type,
        "char_count": prov.char_count,
    }
    if prov.url is not None:
        provenance_block["url"] = prov.url
    if prov.retrieved_at is not None:
        provenance_block["retrieved_at"] = prov.retrieved_at

    base_tags = [f"source/{_mime_to_tag(prov.mime_type)}"]
    extra_tags = [t for t in record.tags if t not in base_tags]

    fm: dict = {
        "title": record.title,
        "slug": slug,
        "type": "source",
        "created": now,
        "updated": now,
        "source_id": record.source_id,
        "workspace_id": record.workspace_id,
        "tags": base_tags + extra_tags,
        "aliases": [],
        "provenance": provenance_block,
    }

    if record.author is not None:
        fm["author"] = record.author
    if record.published_at is not None:
        fm["published_at"] = record.published_at
    if record.language is not None:
        fm["language"] = record.language

    fm["entities"] = [f"[[entities/{s}]]" for s in record.entity_slugs]
    fm["concepts"] = [f"[[concepts/{s}]]" for s in record.concept_slugs]
    fm["confidence"] = None
    fm["model"] = None
    fm["generation_notes"] = None

    return fm


def _mime_to_tag(mime_type: str) -> str:
    mapping = {
        "text/html": "article",
        "application/pdf": "pdf",
        "text/plain": "text",
        "text/markdown": "markdown",
        "application/json": "json",
    }
    return mapping.get(mime_type, "file")


# ---------------------------------------------------------------------------
# Body builder
# ---------------------------------------------------------------------------


def _build_body(record: SourceRecord) -> tuple[str, str]:
    """Return (static_body, generated_section).

    static_body: the user-editable intro and Related section.
    generated_section: compiler-owned excerpt block inside atlas:generated tags.
    """
    prov = record.provenance

    # Static intro — user may edit.
    parts: list[str] = [f"# {record.title}\n"]

    meta_lines: list[str] = []
    if record.author:
        meta_lines.append(f"- **Author:** {record.author}")
    if record.published_at:
        meta_lines.append(f"- **Published:** {record.published_at}")
    if prov.url:
        meta_lines.append(f"- **Source URL:** {prov.url}")
    meta_lines.append(f"- **MIME type:** {prov.mime_type}")
    meta_lines.append(f"- **Characters:** {prov.char_count:,}")
    if record.language:
        meta_lines.append(f"- **Language:** {record.language}")

    if meta_lines:
        parts.append("\n## Metadata\n")
        parts.extend(meta_lines)

    if record.entity_slugs:
        parts.append("\n## Related\n")
        for slug in record.entity_slugs:
            parts.append(f"- [[entities/{slug}]]")

    static_body = "\n".join(parts) + "\n"

    # Generated section — compiler replaces on re-run.
    excerpt = _excerpt(record.extracted_text)
    gen_lines: list[str] = ["## Raw Excerpt\n", f"> {excerpt}"]

    generated_section = "\n".join(gen_lines) + "\n"

    return static_body, generated_section


def _excerpt(text: str, max_chars: int = 2000) -> str:
    """Return a safe excerpt, truncated at a sentence boundary if possible."""
    text = text.strip()
    if len(text) <= max_chars:
        return text
    cutoff = text.rfind(".", 0, max_chars)
    if cutoff > max_chars // 2:
        return text[: cutoff + 1] + " …"
    return text[:max_chars] + " …"


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def generate_source_note(record: SourceRecord, vault_root: Path) -> SourceNoteResult:
    """Generate or update a source vault note.

    Args:
        record:     SourceRecord with all required fields populated.
        vault_root: Absolute path to the vault root directory.

    Returns:
        SourceNoteResult describing the write outcome.

    Raises:
        ValueError: If required fields are missing or empty.
    """
    _validate(record)

    slug = make_slug(record.title)
    if not slug:
        raise ValueError(f"Could not derive slug from title: {record.title!r}")

    now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    fm = _build_frontmatter(record, slug, now)
    static_body, generated_section = _build_body(record)

    note_path = vault_root / record.workspace_id / "sources" / f"{slug}.md"

    result: WriteResult = write_note(
        path=note_path,
        frontmatter=fm,
        body=static_body,
        generated_section=generated_section,
    )

    logger.info(
        "source note %s for source_id=%s action=%s",
        note_path.name,
        record.source_id,
        result.action,
    )

    return SourceNoteResult(
        source_id=record.source_id,
        slug=slug,
        path=note_path,
        action=result.action,
        conflict=result.conflict,
    )


def _validate(record: SourceRecord) -> None:
    if not record.source_id:
        raise ValueError("source_id is required")
    if not record.workspace_id:
        raise ValueError("workspace_id is required")
    if not record.title or not record.title.strip():
        raise ValueError("title is required and must not be blank")
    if not record.provenance.ingest_job_id:
        raise ValueError("provenance.ingest_job_id is required")
    if not record.provenance.content_hash:
        raise ValueError("provenance.content_hash is required")
    if not record.provenance.mime_type:
        raise ValueError("provenance.mime_type is required")
