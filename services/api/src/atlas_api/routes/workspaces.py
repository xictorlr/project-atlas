"""Workspace CRUD endpoints."""

import re
import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from atlas_api.db import get_db
from atlas_api.models.enums import WorkspaceRole
from atlas_api.models.workspace import Workspace, WorkspaceMember
from atlas_api.schemas.workspace import WorkspaceMemberRow, WorkspaceRow

router = APIRouter(prefix="/workspaces", tags=["workspaces"])

_PLACEHOLDER_USER_ID = "system"


# ── Request bodies ────────────────────────────────────────────────────────────


class CreateWorkspaceRequest(BaseModel):
    name: str
    description: str | None = None
    is_private: bool = False


class UpdateWorkspaceRequest(BaseModel):
    name: str | None = None
    description: str | None = None
    is_private: bool | None = None


# ── Helpers ───────────────────────────────────────────────────────────────────


def _slugify(name: str) -> str:
    """Convert a workspace name to a URL-safe slug."""
    slug = name.lower().strip()
    slug = re.sub(r"[^a-z0-9]+", "-", slug)
    slug = slug.strip("-")
    return slug or "workspace"


def _row_to_model(row: WorkspaceRow) -> Workspace:
    members = tuple(
        WorkspaceMember(
            user_id=m.user_id,
            role=WorkspaceRole(m.role),
            joined_at=m.joined_at.isoformat(),
        )
        for m in row.members
    )
    return Workspace(
        id=row.id,
        slug=row.slug,
        name=row.name,
        description=row.description,
        owner_id=row.owner_id,
        members=members,
        is_private=row.is_private,
        created_at=row.created_at.isoformat(),
        updated_at=row.updated_at.isoformat(),
    )


async def _get_or_404(workspace_id: str, db: AsyncSession) -> WorkspaceRow:
    result = await db.execute(
        select(WorkspaceRow)
        .where(WorkspaceRow.id == workspace_id)
        .options(selectinload(WorkspaceRow.members))
    )
    row = result.scalar_one_or_none()
    if row is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Workspace {workspace_id!r} not found",
        )
    return row


# ── Routes ────────────────────────────────────────────────────────────────────


@router.get("", response_model=list[Workspace])
async def list_workspaces(db: AsyncSession = Depends(get_db)) -> list[Workspace]:
    """List all workspaces visible to the current user."""
    result = await db.execute(
        select(WorkspaceRow).options(selectinload(WorkspaceRow.members))
    )
    rows = result.scalars().all()
    return [_row_to_model(r) for r in rows]


@router.get("/{workspace_id}", response_model=Workspace)
async def get_workspace(
    workspace_id: str, db: AsyncSession = Depends(get_db)
) -> Workspace:
    """Get a single workspace by ID."""
    row = await _get_or_404(workspace_id, db)
    return _row_to_model(row)


@router.post("", response_model=Workspace, status_code=status.HTTP_201_CREATED)
async def create_workspace(
    body: CreateWorkspaceRequest,
    db: AsyncSession = Depends(get_db),
) -> Workspace:
    """Create a new workspace."""
    workspace_id = str(uuid.uuid4())
    slug_base = _slugify(body.name)

    # Ensure slug uniqueness by appending a short suffix when needed.
    slug = slug_base
    existing = await db.execute(select(WorkspaceRow).where(WorkspaceRow.slug == slug))
    if existing.scalar_one_or_none() is not None:
        slug = f"{slug_base}-{workspace_id[:8]}"

    now = datetime.now(tz=timezone.utc)
    row = WorkspaceRow(
        id=workspace_id,
        slug=slug,
        name=body.name,
        description=body.description,
        owner_id=_PLACEHOLDER_USER_ID,
        is_private=body.is_private,
        created_at=now,
        updated_at=now,
    )
    db.add(row)

    # Add the creator as owner member.
    member_row = WorkspaceMemberRow(
        id=str(uuid.uuid4()),
        workspace_id=workspace_id,
        user_id=_PLACEHOLDER_USER_ID,
        role=WorkspaceRole.OWNER,
        joined_at=now,
    )
    db.add(member_row)
    await db.flush()

    # Reload with members relationship populated.
    reloaded = await _get_or_404(workspace_id, db)
    return _row_to_model(reloaded)


@router.patch("/{workspace_id}", response_model=Workspace)
async def update_workspace(
    workspace_id: str,
    body: UpdateWorkspaceRequest,
    db: AsyncSession = Depends(get_db),
) -> Workspace:
    """Update workspace metadata."""
    row = await _get_or_404(workspace_id, db)

    if body.name is not None:
        row.name = body.name
    if body.description is not None:
        row.description = body.description
    if body.is_private is not None:
        row.is_private = body.is_private

    row.updated_at = datetime.now(tz=timezone.utc)
    await db.flush()

    reloaded = await _get_or_404(workspace_id, db)
    return _row_to_model(reloaded)


@router.delete("/{workspace_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_workspace(
    workspace_id: str, db: AsyncSession = Depends(get_db)
) -> None:
    """Delete a workspace and all its contents."""
    row = await _get_or_404(workspace_id, db)
    await db.delete(row)
    await db.flush()
