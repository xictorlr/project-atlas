"""Job status endpoints."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select, desc
from sqlalchemy.ext.asyncio import AsyncSession

from atlas_api.db import get_db
from atlas_api.models.enums import JobKind, JobStatus
from atlas_api.models.job import Job, JobError
from atlas_api.schemas.job import JobRow
from atlas_api.schemas.workspace import WorkspaceRow

router = APIRouter(
    prefix="/workspaces/{workspace_id}/jobs",
    tags=["jobs"],
)


# ── Helpers ───────────────────────────────────────────────────────────────────


def _row_to_model(row: JobRow) -> Job:
    error: JobError | None = None
    if row.error is not None:
        error = JobError(
            code=row.error.get("code", "UNKNOWN"),
            message=row.error.get("message", ""),
            retryable=row.error.get("retryable", False),
        )
    return Job(
        id=row.id,
        workspace_id=row.workspace_id,
        kind=JobKind(row.kind),
        status=JobStatus(row.status),
        payload=row.payload,
        result=row.result,
        error=error,
        attempt=row.attempt,
        max_attempts=row.max_attempts,
        queued_at=row.queued_at.isoformat(),
        started_at=row.started_at.isoformat() if row.started_at else None,
        completed_at=row.completed_at.isoformat() if row.completed_at else None,
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


# ── Routes ────────────────────────────────────────────────────────────────────


@router.get("", response_model=list[Job])
async def list_jobs(
    workspace_id: str, db: AsyncSession = Depends(get_db)
) -> list[Job]:
    """List all jobs for a workspace, newest first."""
    await _require_workspace(workspace_id, db)
    result = await db.execute(
        select(JobRow)
        .where(JobRow.workspace_id == workspace_id)
        .order_by(desc(JobRow.queued_at))
    )
    return [_row_to_model(r) for r in result.scalars().all()]


@router.get("/{job_id}", response_model=Job)
async def get_job(
    workspace_id: str, job_id: str, db: AsyncSession = Depends(get_db)
) -> Job:
    """Get a single job by ID."""
    await _require_workspace(workspace_id, db)
    result = await db.execute(
        select(JobRow).where(
            JobRow.id == job_id,
            JobRow.workspace_id == workspace_id,
        )
    )
    row = result.scalar_one_or_none()
    if row is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Job {job_id!r} not found in workspace {workspace_id!r}",
        )
    return _row_to_model(row)
