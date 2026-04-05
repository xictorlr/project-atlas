"""Vault note read endpoints — disk-based, no DB required.

Endpoints:
  GET  /api/v1/workspaces/{id}/vault/notes                    list all notes
  GET  /api/v1/workspaces/{id}/vault/notes/{slug}             single note
  GET  /api/v1/workspaces/{id}/vault/graph                    wikilink graph

All reads are from the Markdown vault on disk. The vault_path setting controls
the root; workspace notes live under {vault_path}/{workspace_id}/ or fall back
to {vault_path}/ for single-workspace dev layouts.

Failure states:
  - Vault directory missing: returns empty list / 404 as appropriate.
  - Malformed frontmatter: note is returned with safe defaults; error is logged.
  - Slug not found: 404.
"""

from __future__ import annotations

import hashlib
import logging
import re
from pathlib import Path

from fastapi import APIRouter, HTTPException, status

from atlas_api.config import settings
from atlas_api.models.enums import VaultNoteKind
from atlas_api.models.vault import VaultNote, VaultNoteFrontmatter
from atlas_api.search.indexer import parse_frontmatter, note_type_from_frontmatter
from atlas_api.search.models import LinkGraph, LinkGraphEdge, LinkGraphNode

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/workspaces/{workspace_id}/vault",
    tags=["vault"],
)

# ── Wikilink extraction ────────────────────────────────────────────────────────

_WIKILINK_RE = re.compile(r"\[\[([^\]|#]+?)(?:\|[^\]]*)?\]\]")


def _extract_wikilinks(text: str) -> list[str]:
    """Return all wikilink targets from a Markdown body.

    [[target]] and [[target|alias]] both yield "target".
    """
    return [m.group(1).strip() for m in _WIKILINK_RE.finditer(text)]


# ── Vault path resolution ──────────────────────────────────────────────────────

def _vault_root(workspace_id: str) -> Path:
    base = Path(settings.vault_path)
    candidate = base / workspace_id
    return candidate if candidate.exists() else base


# ── Note parsing ───────────────────────────────────────────────────────────────

_NOTE_KIND_MAP: dict[str, VaultNoteKind] = {
    "source": VaultNoteKind.SOURCE,
    "entity": VaultNoteKind.ENTITY,
    "concept": VaultNoteKind.CONCEPT,
    "index": VaultNoteKind.INDEX,
    "timeline": VaultNoteKind.TIMELINE,
}


def _kind_from_type_str(type_str: str) -> VaultNoteKind:
    return _NOTE_KIND_MAP.get(type_str, VaultNoteKind.SOURCE)


def _content_hash(raw: bytes) -> str:
    digest = hashlib.sha256(raw).hexdigest()
    return f"sha256:{digest}"


def _parse_note(md_file: Path, vault_root: Path, workspace_id: str) -> VaultNote | None:
    """Parse a single .md file into a VaultNote.

    Returns None when the file cannot be read. Logs a warning in that case.
    """
    try:
        raw_bytes = md_file.read_bytes()
        content = raw_bytes.decode("utf-8")
    except OSError as exc:
        logger.warning("Cannot read %s: %s", md_file, exc)
        return None

    fm, _body = parse_frontmatter(content)
    type_str = note_type_from_frontmatter(fm, md_file)

    slug = str(fm.get("slug") or md_file.stem)
    title = str(fm.get("title") or slug)
    kind = _kind_from_type_str(type_str)

    tags_raw = fm.get("tags") or []
    tags = tuple(str(t) for t in tags_raw) if isinstance(tags_raw, list) else ()

    source_ids_raw = fm.get("source_ids") or (
        [fm["source_id"]] if fm.get("source_id") else []
    )
    source_ids = tuple(str(s) for s in source_ids_raw) if isinstance(source_ids_raw, list) else ()

    backlinks_raw = fm.get("backlinks") or []
    backlinks = tuple(str(b) for b in backlinks_raw) if isinstance(backlinks_raw, list) else ()

    generated_at = str(fm.get("generated_at") or fm.get("updated") or fm.get("created") or "")
    created_at = str(fm.get("created") or "")
    updated_at = str(fm.get("updated") or "")

    note_workspace_id = str(fm.get("workspace_id") or workspace_id)

    frontmatter = VaultNoteFrontmatter(
        title=title,
        slug=slug,
        kind=kind,
        workspace_id=note_workspace_id,
        source_ids=source_ids,
        generated_at=generated_at,
        model=fm.get("model"),
        confidence_notes=fm.get("generation_notes") or fm.get("confidence_notes"),
        backlinks=backlinks,
        tags=tags,
    )

    vault_path = str(md_file.relative_to(vault_root.parent))

    return VaultNote(
        id=slug,
        workspace_id=note_workspace_id,
        kind=kind,
        slug=slug,
        vault_path=vault_path,
        frontmatter=frontmatter,
        content_hash=_content_hash(raw_bytes),
        created_at=created_at,
        updated_at=updated_at,
    )


def _list_notes(vault_root: Path, workspace_id: str) -> list[VaultNote]:
    """Scan vault_root for all .md files and return parsed VaultNote list."""
    if not vault_root.exists():
        logger.warning("Vault root not found: %s", vault_root)
        return []

    notes: list[VaultNote] = []
    for md_file in sorted(vault_root.rglob("*.md")):
        note = _parse_note(md_file, vault_root, workspace_id)
        if note is not None:
            notes.append(note)
    return notes


# ── Routes ─────────────────────────────────────────────────────────────────────


@router.get("/notes", response_model=list[VaultNote])
async def list_vault_notes(workspace_id: str) -> list[VaultNote]:
    """List all vault notes for a workspace.

    Scans disk; no DB dependency. Returns empty list when vault is absent.
    """
    vault_root = _vault_root(workspace_id)
    return _list_notes(vault_root, workspace_id)


@router.get("/notes/{slug}", response_model=VaultNote)
async def get_vault_note(workspace_id: str, slug: str) -> VaultNote:
    """Read a single vault note by slug.

    Searches across all .md files in the workspace vault; returns 404 when
    the slug cannot be matched.
    """
    vault_root = _vault_root(workspace_id)
    if not vault_root.exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Vault not found for workspace {workspace_id!r}",
        )

    for md_file in vault_root.rglob("*.md"):
        if md_file.stem == slug:
            note = _parse_note(md_file, vault_root, workspace_id)
            if note is not None and note.slug == slug:
                return note

    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=f"Note {slug!r} not found in workspace {workspace_id!r}",
    )


@router.get("/graph", response_model=LinkGraph)
async def get_vault_graph(workspace_id: str) -> LinkGraph:
    """Return a wikilink graph for the workspace vault.

    Nodes: all vault notes (slug, title, type, path).
    Edges: directed wikilinks [[target]] parsed from note bodies.
    """
    vault_root = _vault_root(workspace_id)
    notes = _list_notes(vault_root, workspace_id)

    slug_set = {n.slug for n in notes}
    nodes = tuple(
        LinkGraphNode(
            slug=n.slug,
            title=n.frontmatter.title,
            note_type=n.kind.value,
            vault_path=n.vault_path,
        )
        for n in notes
    )

    edges: list[LinkGraphEdge] = []
    for md_file in vault_root.rglob("*.md"):
        try:
            content = md_file.read_text(encoding="utf-8")
        except OSError:
            continue

        _fm, body = parse_frontmatter(content)
        source_slug = md_file.stem
        if source_slug not in slug_set:
            continue

        for target_raw in _extract_wikilinks(body):
            # Normalize: strip leading folder prefix (entities/foo -> foo)
            target_slug = target_raw.split("/")[-1].split("#")[0].strip()
            if target_slug in slug_set and target_slug != source_slug:
                edges.append(LinkGraphEdge(source=source_slug, target=target_slug))

    return LinkGraph(
        workspace_id=workspace_id,
        nodes=nodes,
        edges=tuple(edges),
    )
