"""Obsidian sync and vault export endpoints.

Endpoints:
  POST /api/v1/workspaces/{id}/export
      Exports the workspace vault as a ZIP and returns the file.
      Query param: format (zip | flat) — only "zip" is currently implemented.

  GET  /api/v1/workspaces/{id}/sync/status
      Returns status about the last sync for this workspace (stub — extend when
      sync state is persisted to DB).

Failure states:
  - Vault directory missing: 404.
  - Export write error: 500.
  - Workspace not found: 404.
"""

from __future__ import annotations

import logging
import tempfile
from pathlib import Path

from fastapi import APIRouter, HTTPException, status
from fastapi.responses import FileResponse
from pydantic import BaseModel

from atlas_api.config import settings

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/workspaces/{workspace_id}",
    tags=["sync"],
)


class SyncStatusResponse(BaseModel):
    workspace_id: str
    obsidian_sync_enabled: bool
    last_sync_at: str | None
    message: str


@router.post(
    "/export",
    summary="Export workspace vault as ZIP",
    response_class=FileResponse,
)
async def export_vault(workspace_id: str, format: str = "zip") -> FileResponse:
    """Export the workspace vault to a downloadable ZIP archive.

    The ZIP includes all .md notes plus a minimal .obsidian/ config stub for
    immediate Obsidian compatibility.

    Parameters
    ----------
    format:
        Only "zip" is supported. Returns 422 for other values.
    """
    if format != "zip":
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Unsupported export format: {format!r}. Only 'zip' is supported.",
        )

    vault_root = Path(settings.vault_path)
    vault_dir = vault_root / workspace_id
    if not vault_dir.exists():
        vault_dir = vault_root  # single-workspace dev fallback
    if not vault_dir.exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Vault directory not found for workspace: {workspace_id}",
        )

    # Import here to keep startup fast when sync is not used.
    from atlas_worker.sync.export import VaultExporter

    tmp = tempfile.NamedTemporaryFile(
        suffix=".zip",
        delete=False,
        prefix=f"atlas-export-{workspace_id}-",
    )
    tmp.close()
    dest_path = Path(tmp.name)

    try:
        exporter = VaultExporter(vault_dir=vault_dir, workspace_id=workspace_id)
        result = exporter.export_zip(dest_path)
    except FileNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc
    except OSError as exc:
        logger.error("export failed", extra={"workspace_id": workspace_id, "error": str(exc)})
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Export failed due to a filesystem error.",
        ) from exc

    logger.info(
        "export complete",
        extra={
            "workspace_id": workspace_id,
            "note_count": result.note_count,
            "size_bytes": result.size_bytes,
        },
    )

    return FileResponse(
        path=str(dest_path),
        media_type="application/zip",
        filename=f"{workspace_id}-vault.zip",
    )


@router.get(
    "/sync/status",
    summary="Obsidian sync status for workspace",
    response_model=SyncStatusResponse,
)
async def get_sync_status(workspace_id: str) -> SyncStatusResponse:
    """Return current Obsidian sync state for a workspace.

    In this initial implementation the sync state is not persisted; this
    endpoint returns the configuration status. Extend when a sync_events table
    is added.
    """
    return SyncStatusResponse(
        workspace_id=workspace_id,
        obsidian_sync_enabled=True,
        last_sync_at=None,
        message="Sync state persistence not yet implemented. Use POST /export for vault download.",
    )
