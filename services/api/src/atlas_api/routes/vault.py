"""Vault note read endpoints."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from atlas_api.db import get_db
from atlas_api.models.vault import VaultNote

router = APIRouter(
    prefix="/workspaces/{workspace_id}/vault",
    tags=["vault"],
)


@router.get("/notes", response_model=list[VaultNote])
async def list_vault_notes(
    workspace_id: str, db: AsyncSession = Depends(get_db)
) -> list[VaultNote]:
    """List all vault notes for a workspace."""
    raise HTTPException(status_code=status.HTTP_501_NOT_IMPLEMENTED, detail="Not implemented")


@router.get("/notes/{note_id}", response_model=VaultNote)
async def get_vault_note(
    workspace_id: str, note_id: str, db: AsyncSession = Depends(get_db)
) -> VaultNote:
    """Get a single vault note."""
    raise HTTPException(status_code=status.HTTP_501_NOT_IMPLEMENTED, detail="Not implemented")
