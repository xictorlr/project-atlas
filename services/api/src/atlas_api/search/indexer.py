"""Vault indexer — scans Markdown files, parses frontmatter, builds an in-memory
TF-IDF inverted index keyed by workspace.

Index lifecycle:
  - Built lazily on first search request for a workspace.
  - Invalidated and rebuilt when explicitly requested (e.g. after ingest).
  - Stored in a module-level dict so it survives across requests in the same
    worker process; not shared across processes.

Failure states:
  - Vault directory missing: returns empty index (no error; caller sees 0 results).
  - Malformed frontmatter: file is skipped; error is logged.
  - Binary or unreadable file: skipped; error is logged.
"""

from __future__ import annotations

import logging
import math
import re
from collections import defaultdict
from dataclasses import dataclass, field
from pathlib import Path
from typing import TypeAlias

import yaml

logger = logging.getLogger(__name__)

# ── Types ──────────────────────────────────────────────────────────────────────

Slug: TypeAlias = str
Term: TypeAlias = str


@dataclass(frozen=True)
class NoteRecord:
    """Parsed representation of a single vault note."""

    slug: str
    title: str
    note_type: str
    tags: tuple[str, ...]
    vault_path: str
    body: str
    frontmatter: dict


@dataclass
class PostingEntry:
    """One entry in the inverted index posting list."""

    note_path: str
    slug: str
    tf: float  # term frequency within the document
    positions: list[int] = field(default_factory=list)  # char offsets for snippet extraction


@dataclass
class WorkspaceIndex:
    """In-memory index for a single workspace."""

    workspace_id: str
    notes: dict[Slug, NoteRecord] = field(default_factory=dict)
    # term -> list[PostingEntry]
    postings: dict[Term, list[PostingEntry]] = field(default_factory=lambda: defaultdict(list))
    # note_path -> set of terms (for IDF computation)
    note_terms: dict[str, set[Term]] = field(default_factory=dict)
    doc_count: int = 0


# module-level cache: workspace_id -> WorkspaceIndex
_INDEX_CACHE: dict[str, WorkspaceIndex] = {}

# ── Tokenization ───────────────────────────────────────────────────────────────

_STOP_WORDS: frozenset[str] = frozenset(
    {
        "a", "an", "and", "are", "as", "at", "be", "been", "but", "by",
        "for", "from", "has", "have", "he", "her", "his", "i", "if", "in",
        "is", "it", "its", "me", "my", "no", "not", "of", "on", "or", "our",
        "so", "than", "that", "the", "their", "them", "then", "there", "they",
        "this", "to", "up", "us", "was", "we", "were", "will", "with", "you",
    }
)


def tokenize(text: str) -> list[str]:
    """Lowercase, strip punctuation, split on whitespace, remove stop words."""
    text = text.lower()
    tokens = re.findall(r"[a-z0-9]+(?:'[a-z]+)?", text)
    return [t for t in tokens if t not in _STOP_WORDS and len(t) > 1]


def tokenize_with_positions(text: str) -> list[tuple[str, int]]:
    """Return (token, char_offset) pairs for snippet extraction."""
    text_lower = text.lower()
    result: list[tuple[str, int]] = []
    for m in re.finditer(r"[a-z0-9]+(?:'[a-z]+)?", text_lower):
        token = m.group()
        if token not in _STOP_WORDS and len(token) > 1:
            result.append((token, m.start()))
    return result


# ── Frontmatter parsing ────────────────────────────────────────────────────────

_FM_DELIMITER = re.compile(r"^---\s*$", re.MULTILINE)


def parse_frontmatter(content: str) -> tuple[dict, str]:
    """Split YAML frontmatter from body. Returns (frontmatter_dict, body_text)."""
    parts = _FM_DELIMITER.split(content, maxsplit=2)
    if len(parts) >= 3:
        try:
            fm = yaml.safe_load(parts[1]) or {}
            body = parts[2].strip()
            return fm, body
        except yaml.YAMLError as exc:
            logger.warning("YAML parse error in frontmatter: %s", exc)
            return {}, content
    return {}, content


def note_type_from_frontmatter(fm: dict, path: Path) -> str:
    """Derive note_type from frontmatter 'type' field; fall back to directory name."""
    if fm.get("type"):
        return str(fm["type"])
    # Infer from directory: vault/sources/foo.md -> "source"
    parent = path.parent.name
    type_map = {
        "sources": "source",
        "entities": "entity",
        "concepts": "concept",
        "indexes": "index",
        "timelines": "timeline",
        "meta": "meta",
    }
    return type_map.get(parent, "unknown")


# ── Indexing ───────────────────────────────────────────────────────────────────

def _index_note(idx: WorkspaceIndex, note_path: str, record: NoteRecord) -> None:
    """Add a NoteRecord into the workspace index."""
    idx.notes[record.slug] = record
    idx.doc_count += 1

    # Build token -> positions map
    token_positions: dict[str, list[int]] = defaultdict(list)
    combined_text = f"{record.title} {record.body}"
    for token, pos in tokenize_with_positions(combined_text):
        token_positions[token].append(pos)

    total_tokens = sum(len(v) for v in token_positions.values()) or 1
    doc_term_set: set[str] = set(token_positions.keys())
    idx.note_terms[note_path] = doc_term_set

    for term, positions in token_positions.items():
        tf = len(positions) / total_tokens
        idx.postings[term].append(
            PostingEntry(
                note_path=note_path,
                slug=record.slug,
                tf=tf,
                positions=positions,
            )
        )


def build_workspace_index(vault_root: Path, workspace_id: str) -> WorkspaceIndex:
    """Scan all .md files under vault_root, parse them, and return a built index.

    Does not mutate the cache — callers must store the result themselves.
    """
    idx = WorkspaceIndex(workspace_id=workspace_id)

    if not vault_root.exists():
        logger.warning("Vault directory not found: %s", vault_root)
        return idx

    for md_file in vault_root.rglob("*.md"):
        try:
            content = md_file.read_text(encoding="utf-8")
        except OSError as exc:
            logger.warning("Cannot read %s: %s", md_file, exc)
            continue

        fm, body = parse_frontmatter(content)

        slug = fm.get("slug") or md_file.stem
        title = fm.get("title") or slug
        tags_raw = fm.get("tags") or []
        tags = tuple(str(t) for t in tags_raw) if isinstance(tags_raw, list) else ()
        note_type = note_type_from_frontmatter(fm, md_file)
        vault_path = str(md_file.relative_to(vault_root.parent))

        record = NoteRecord(
            slug=slug,
            title=title,
            note_type=note_type,
            tags=tags,
            vault_path=vault_path,
            body=body,
            frontmatter=fm,
        )
        _index_note(idx, vault_path, record)

    logger.info(
        "Built index for workspace %s: %d notes, %d unique terms",
        workspace_id,
        idx.doc_count,
        len(idx.postings),
    )
    return idx


def get_or_build_index(vault_root: Path, workspace_id: str) -> WorkspaceIndex:
    """Return cached index or build it lazily."""
    if workspace_id not in _INDEX_CACHE:
        _INDEX_CACHE[workspace_id] = build_workspace_index(vault_root, workspace_id)
    return _INDEX_CACHE[workspace_id]


def invalidate_index(workspace_id: str) -> None:
    """Drop the cached index so the next request rebuilds it."""
    _INDEX_CACHE.pop(workspace_id, None)


# ── TF-IDF scoring ─────────────────────────────────────────────────────────────

def compute_idf(idx: WorkspaceIndex, term: str) -> float:
    """Inverse document frequency for a term."""
    doc_freq = len(idx.postings.get(term, []))
    if doc_freq == 0:
        return 0.0
    return math.log((idx.doc_count + 1) / (doc_freq + 1)) + 1.0
