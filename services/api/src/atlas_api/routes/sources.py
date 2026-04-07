"""Source CRUD and upload endpoints."""

import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from atlas_api.db import get_db
from atlas_api.models.enums import SourceKind, SourceStatus
from atlas_api.models.source import Source, SourceManifest
from atlas_api.queue import enqueue_job
from atlas_api.schemas.source import SourceRow
from atlas_api.schemas.workspace import WorkspaceRow
from atlas_api.storage import delete_file, save_file

router = APIRouter(
    prefix="/workspaces/{workspace_id}/sources",
    tags=["sources"],
)


# ── Request bodies ────────────────────────────────────────────────────────────


class CreateSourceRequest(BaseModel):
    title: str
    kind: SourceKind
    origin_url: str | None = None
    description: str | None = None


# ── Helpers ───────────────────────────────────────────────────────────────────


def _row_to_model(row: SourceRow) -> Source:
    manifest: SourceManifest | None = None
    if row.manifest is not None:
        manifest = SourceManifest(
            ingested_at=row.manifest.get("ingested_at", ""),
            normalized_at=row.manifest.get("normalized_at"),
            origin_url=row.manifest.get("origin_url"),
            mime_type=row.manifest.get("mime_type"),
            file_size_bytes=row.manifest.get("file_size_bytes"),
            chunk_count=row.manifest.get("chunk_count"),
            model=row.manifest.get("model"),
            confidence_notes=row.manifest.get("confidence_notes"),
            needs_reingest=bool(row.manifest.get("needs_reingest", False)),
        )
    return Source(
        id=row.id,
        workspace_id=row.workspace_id,
        kind=SourceKind(row.kind),
        status=SourceStatus(row.status),
        title=row.title,
        description=row.description,
        storage_key=row.storage_key,
        manifest=manifest,
        created_at=row.created_at.isoformat(),
        updated_at=row.updated_at.isoformat(),
    )


async def _require_workspace(workspace_id: str, db: AsyncSession) -> None:
    result = await db.execute(
        select(WorkspaceRow).where(WorkspaceRow.id == workspace_id)
    )
    if result.scalar_one_or_none() is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Workspace {workspace_id!r} not found",
        )


async def _get_source_or_404(
    workspace_id: str, source_id: str, db: AsyncSession
) -> SourceRow:
    result = await db.execute(
        select(SourceRow).where(
            SourceRow.id == source_id,
            SourceRow.workspace_id == workspace_id,
        )
    )
    row = result.scalar_one_or_none()
    if row is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Source {source_id!r} not found in workspace {workspace_id!r}",
        )
    return row


# ── Routes ────────────────────────────────────────────────────────────────────


@router.get("", response_model=list[Source])
async def list_sources(
    workspace_id: str, db: AsyncSession = Depends(get_db)
) -> list[Source]:
    """List all sources in a workspace."""
    await _require_workspace(workspace_id, db)
    result = await db.execute(
        select(SourceRow).where(SourceRow.workspace_id == workspace_id)
    )
    return [_row_to_model(r) for r in result.scalars().all()]


@router.get("/{source_id}", response_model=Source)
async def get_source(
    workspace_id: str, source_id: str, db: AsyncSession = Depends(get_db)
) -> Source:
    """Get a single source record."""
    await _require_workspace(workspace_id, db)
    row = await _get_source_or_404(workspace_id, source_id, db)
    return _row_to_model(row)


@router.post("", response_model=Source, status_code=status.HTTP_201_CREATED)
async def create_source(
    workspace_id: str,
    body: CreateSourceRequest,
    db: AsyncSession = Depends(get_db),
) -> Source:
    """Register a new source (URL or metadata only — no file)."""
    await _require_workspace(workspace_id, db)

    source_id = str(uuid.uuid4())
    now = datetime.now(tz=timezone.utc)

    # For metadata-only sources, storage_key is a placeholder path.
    storage_key = f"{workspace_id}/{source_id}/.meta"

    manifest: dict | None = None
    if body.origin_url is not None:
        manifest = {
            "ingested_at": now.isoformat(),
            "normalized_at": None,
            "origin_url": body.origin_url,
            "mime_type": None,
            "file_size_bytes": None,
            "chunk_count": None,
            "model": None,
            "confidence_notes": None,
        }

    row = SourceRow(
        id=source_id,
        workspace_id=workspace_id,
        kind=body.kind,
        status=SourceStatus.PENDING,
        title=body.title,
        description=body.description,
        storage_key=storage_key,
        manifest=manifest,
        created_at=now,
        updated_at=now,
    )
    db.add(row)
    await db.flush()

    return _row_to_model(row)


@router.post("/upload", response_model=Source, status_code=status.HTTP_201_CREATED)
async def upload_source(
    workspace_id: str,
    file: UploadFile = File(...),
    title: str = Form(...),
    kind: SourceKind = Form(SourceKind.ARTICLE),
    description: str | None = Form(None),
    db: AsyncSession = Depends(get_db),
) -> Source:
    """Upload a file and create a source record."""
    await _require_workspace(workspace_id, db)

    content = await file.read()
    filename = file.filename or "upload"
    source_id = str(uuid.uuid4())
    now = datetime.now(tz=timezone.utc)

    save_result = save_file(
        workspace_id=workspace_id,
        source_id=source_id,
        content=content,
        filename=filename,
    )

    manifest = {
        "ingested_at": now.isoformat(),
        "normalized_at": None,
        "origin_url": None,
        "mime_type": file.content_type,
        "file_size_bytes": save_result.file_size_bytes,
        "chunk_count": None,
        "model": None,
        "confidence_notes": None,
    }

    row = SourceRow(
        id=source_id,
        workspace_id=workspace_id,
        kind=kind,
        status=SourceStatus.PENDING,
        title=title,
        description=description,
        storage_key=save_result.storage_key,
        manifest=manifest,
        created_at=now,
        updated_at=now,
    )
    db.add(row)
    await db.flush()

    await enqueue_job(
        job_type="ingest_source",
        payload={"source_id": source_id},
        workspace_id=workspace_id,
        db=db,
    )

    return _row_to_model(row)


@router.post("/{source_id}/reingest", response_model=Source)
async def reingest_source(
    workspace_id: str, source_id: str, db: AsyncSession = Depends(get_db)
) -> Source:
    """Re-queue an existing source for ingestion.

    Used after a previous ingest failed (e.g. backend was missing) or after
    the source file has been updated. The job re-runs against the current
    storage_key — no upload needed.
    """
    await _require_workspace(workspace_id, db)
    row = await _get_source_or_404(workspace_id, source_id, db)

    row.status = SourceStatus.PENDING
    row.updated_at = datetime.now(tz=timezone.utc)
    await db.flush()

    await enqueue_job(
        job_type="ingest_source",
        payload={"source_id": source_id},
        workspace_id=workspace_id,
        db=db,
    )

    return _row_to_model(row)


@router.delete("/{source_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_source(
    workspace_id: str, source_id: str, db: AsyncSession = Depends(get_db)
) -> None:
    """Delete a source and its stored artifacts."""
    await _require_workspace(workspace_id, db)
    row = await _get_source_or_404(workspace_id, source_id, db)

    # Best-effort storage cleanup — do not fail the request if file is missing.
    try:
        delete_file(row.storage_key)
    except (FileNotFoundError, ValueError):
        pass

    await db.delete(row)
    await db.flush()
