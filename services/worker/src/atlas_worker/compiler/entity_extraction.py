"""Entity extraction and entity note generator — compiler step 2.

Inputs:
  - source note text (plain Markdown body, not the frontmatter)
  - SourceRecord (for provenance)
  - vault_root: Path to vault directory

Outputs:
  - Writes vault/{workspace_id}/entities/{slug}.md for each discovered entity
  - Patches the source note's `entities` frontmatter list with new slugs
  - Returns EntityExtractionResult

MVP extraction heuristics (no LLM dependency):
  - Capitalized multi-word phrases (2-4 words, Title Case) not at sentence starts
  - @mention patterns
  - Bare URLs (schema://…)
  - Email addresses
  Entity kinds are inferred from pattern type and name structure.

Idempotency:
  - Existing entity notes have their source_ids list extended, not replaced.
  - Re-running on the same source_id is a no-op for that entry.
"""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path

from atlas_worker.compiler.source_notes import SourceRecord, make_slug
from atlas_worker.compiler.vault_writer import (
    ConflictRecord,
    WriteResult,
    parse_frontmatter,
    render_frontmatter,
    write_note,
)

logger = logging.getLogger(__name__)

COMPILER_VERSION = "worker/compiler-v1"
# Model used for MVP heuristic pass (no LLM call, but schema requires the field).
HEURISTIC_MODEL = "heuristic-v1"
HEURISTIC_CONFIDENCE = 0.5


# ---------------------------------------------------------------------------
# Data contracts
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class ExtractedEntity:
    name: str
    slug: str
    kind: str  # person | company | project | url | email | unknown


@dataclass(frozen=True)
class EntityNoteResult:
    slug: str
    path: Path
    action: str  # "created" | "updated" | "skipped" | "conflict"
    conflict: ConflictRecord | None = None


@dataclass(frozen=True)
class EntityExtractionResult:
    source_id: str
    entities: list[ExtractedEntity]
    note_results: list[EntityNoteResult]
    source_note_patched: bool


# ---------------------------------------------------------------------------
# Heuristic extractors
# ---------------------------------------------------------------------------


# Titles of words to skip — very common English words that appear capitalized
# mid-sentence in certain contexts but are not entities.
_STOP_WORDS: frozenset[str] = frozenset(
    {
        "The", "A", "An", "This", "That", "These", "Those",
        "It", "Its", "He", "She", "They", "We", "You",
        "And", "Or", "But", "So", "Yet", "For", "Nor",
        "In", "On", "At", "By", "To", "Of", "As", "Is",
        "Are", "Was", "Were", "Be", "Been", "Being",
        "Have", "Has", "Had", "Do", "Does", "Did",
        "Will", "Would", "Could", "Should", "May", "Might",
        "Must", "Shall", "Can", "Not", "No", "Yes",
        "From", "With", "About", "Into", "Through", "During",
        "Before", "After", "Above", "Below", "Between",
        "New", "Old", "First", "Last", "Next", "Same",
    }
)

# Matches "Title Case Multi Word" phrases (2-4 words), not at line/sentence starts.
# We require at least 2 capitalised words not in the stop list.
_TITLE_PHRASE_RE = re.compile(
    r"(?<![.!?\n])(?<!\A)\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+){1,3})\b"
)
_MENTION_RE = re.compile(r"@([A-Za-z][A-Za-z0-9_.-]{1,39})")
_URL_RE = re.compile(r"https?://[^\s\"'<>)\]]+")
_EMAIL_RE = re.compile(r"\b[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}\b")


def extract_entities(text: str) -> list[ExtractedEntity]:
    """Run all heuristic extractors and return deduplicated entities."""
    seen: dict[str, ExtractedEntity] = {}

    for match in _EMAIL_RE.finditer(text):
        name = match.group()
        slug = make_slug(name)
        if slug and slug not in seen:
            seen[slug] = ExtractedEntity(name=name, slug=slug, kind="email")

    for match in _URL_RE.finditer(text):
        name = match.group().rstrip(".,;")
        slug = make_slug(name, max_len=60)
        if slug and slug not in seen:
            seen[slug] = ExtractedEntity(name=name, slug=slug, kind="url")

    for match in _MENTION_RE.finditer(text):
        name = match.group(1)
        slug = make_slug(name)
        if slug and slug not in seen:
            seen[slug] = ExtractedEntity(name=name, slug=slug, kind="person")

    for match in _TITLE_PHRASE_RE.finditer(text):
        phrase = match.group(1)
        words = phrase.split()
        # Filter out phrases composed entirely of stop words.
        content_words = [w for w in words if w not in _STOP_WORDS]
        if len(content_words) < 2:
            continue
        slug = make_slug(phrase)
        if slug and slug not in seen:
            seen[slug] = ExtractedEntity(
                name=phrase, slug=slug, kind=_infer_kind(phrase)
            )

    return list(seen.values())


def _infer_kind(name: str) -> str:
    name_lower = name.lower()
    org_suffixes = (
        " inc", " llc", " ltd", " corp", " co", " group",
        " foundation", " institute", " labs", " lab",
    )
    project_terms = (
        " project", " platform", " framework", " protocol",
        " api", " sdk", " os", " db", " app",
    )
    if any(name_lower.endswith(s) for s in org_suffixes):
        return "company"
    if any(t in name_lower for t in project_terms):
        return "project"
    # Default: if two words and likely a person's name.
    parts = name.split()
    if len(parts) == 2 and all(p[0].isupper() for p in parts):
        return "person"
    return "unknown"


# ---------------------------------------------------------------------------
# Entity note builder
# ---------------------------------------------------------------------------


def _build_entity_frontmatter(
    entity: ExtractedEntity,
    source_record: SourceRecord,
    compile_job_id: str,
    now: str,
    existing_source_ids: list[str],
) -> dict:
    all_source_ids = list(
        dict.fromkeys(existing_source_ids + [source_record.source_id])
    )
    return {
        "title": entity.name,
        "slug": entity.slug,
        "type": "entity",
        "entity_kind": entity.kind,
        "created": now,
        "updated": now,
        "workspace_id": source_record.workspace_id,
        "tags": [f"entity/{entity.kind}", "status/draft"],
        "aliases": [],
        "provenance": {
            "source_ids": all_source_ids,
            "compiled_by": COMPILER_VERSION,
            "compile_job_id": compile_job_id,
            "model": HEURISTIC_MODEL,
            "generated_at": now,
            "confidence": HEURISTIC_CONFIDENCE,
        },
        "sources": [
            f"[[sources/{make_slug(source_record.title)}]]"
            for _ in [None]
        ],
        "concepts": [],
    }


def _build_entity_body(entity: ExtractedEntity, source_record: SourceRecord) -> tuple[str, str]:
    source_slug = make_slug(source_record.title)
    static = (
        f"# {entity.name}\n\n"
        f"*Automatically extracted entity. Review and enrich as needed.*\n\n"
        f"## Overview\n\n"
        f"Entity kind: `{entity.kind}`\n"
    )
    generated = (
        f"## Sources\n\n"
        f"- [[sources/{source_slug}]]\n"
    )
    return static, generated


# ---------------------------------------------------------------------------
# Source note patcher — adds [[entities/…]] wikilinks to source frontmatter
# ---------------------------------------------------------------------------


def patch_source_note_entities(
    source_note_path: Path,
    entity_slugs: list[str],
) -> bool:
    """Add entity wikilinks to the `entities` list in a source note's frontmatter.

    Idempotent — existing entries are preserved.

    Returns:
        True if the note was modified, False if already up to date.
    """
    if not source_note_path.exists():
        logger.warning("source note not found for patching: %s", source_note_path)
        return False

    raw = source_note_path.read_text(encoding="utf-8")
    fm, body = parse_frontmatter(raw)

    existing: list[str] = fm.get("entities", []) or []
    existing_set = set(existing)
    new_entries = [f"[[entities/{s}]]" for s in entity_slugs if f"[[entities/{s}]]" not in existing_set]

    if not new_entries:
        return False

    fm["entities"] = existing + new_entries
    updated = render_frontmatter(fm) + body
    source_note_path.write_text(updated, encoding="utf-8")
    logger.info("patched source note entities: %s (+%d)", source_note_path.name, len(new_entries))
    return True


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def extract_and_generate(
    record: SourceRecord,
    note_text: str,
    vault_root: Path,
    compile_job_id: str,
    source_note_path: Path | None = None,
) -> EntityExtractionResult:
    """Extract entities from source note text and generate/update entity notes.

    Args:
        record:           SourceRecord for the source being compiled.
        note_text:        Plain text of the source note (body without frontmatter).
        vault_root:       Absolute path to the vault root.
        compile_job_id:   Job identifier for provenance.
        source_note_path: If provided, the source note's frontmatter `entities`
                          field will be patched with discovered entity slugs.

    Returns:
        EntityExtractionResult with all entities and their write outcomes.
    """
    entities = extract_entities(note_text)
    now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    note_results: list[EntityNoteResult] = []

    for entity in entities:
        entity_path = vault_root / record.workspace_id / "entities" / f"{entity.slug}.md"

        # Read existing source_ids if the note already exists.
        existing_source_ids: list[str] = []
        if entity_path.exists():
            existing_fm, _ = parse_frontmatter(entity_path.read_text(encoding="utf-8"))
            existing_source_ids = (
                (existing_fm.get("provenance") or {}).get("source_ids") or []
            )

        fm = _build_entity_frontmatter(
            entity=entity,
            source_record=record,
            compile_job_id=compile_job_id,
            now=now,
            existing_source_ids=existing_source_ids,
        )
        static_body, generated_section = _build_entity_body(entity, record)

        result: WriteResult = write_note(
            path=entity_path,
            frontmatter=fm,
            body=static_body,
            generated_section=generated_section,
        )

        note_results.append(
            EntityNoteResult(
                slug=entity.slug,
                path=entity_path,
                action=result.action,
                conflict=result.conflict,
            )
        )

    # Patch source note if a path was given.
    patched = False
    if source_note_path is not None and entities:
        patched = patch_source_note_entities(
            source_note_path=source_note_path,
            entity_slugs=[e.slug for e in entities],
        )

    return EntityExtractionResult(
        source_id=record.source_id,
        entities=entities,
        note_results=note_results,
        source_note_patched=patched,
    )
