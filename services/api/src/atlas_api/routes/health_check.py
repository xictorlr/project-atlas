"""Workspace health check endpoints.

Distinct from routes/health.py which provides the liveness probe /health.

Routes:
  GET  /api/v1/workspaces/{workspace_id}/health
       Returns the last cached health report summary (or triggers a synchronous
       check if none exists yet).

  POST /api/v1/workspaces/{workspace_id}/health/run
       Enqueues a HEALTH_CHECK job and returns the job record. The worker runs
       vault_health.check_vault + source_health.check_sources and stores the
       result in the job's result field.

Failure states:
  - Workspace not found: 404
  - Vault path misconfigured: 500 with descriptive error
"""

from __future__ import annotations

import logging
import uuid
from datetime import datetime, timezone
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from atlas_api.config import settings
from atlas_api.db import get_db
from atlas_api.models.enums import JobKind, JobStatus, SourceStatus
from atlas_api.schemas.job import JobRow
from atlas_api.schemas.source import SourceRow
from atlas_api.schemas.workspace import WorkspaceRow

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/workspaces/{workspace_id}/health",
    tags=["health-check"],
)


# ── Response models ───────────────────────────────────────────────────────────


class HealthIssueSummary(BaseModel):
    severity: str
    code: str
    message: str
    path: str | None = None


class WorkspaceHealthSummary(BaseModel):
    workspace_id: str
    healthy: bool
    error_count: int
    warning_count: int
    checked_at: str
    stats: dict
    issues: list[HealthIssueSummary]


class HealthRunResponse(BaseModel):
    job_id: str
    workspace_id: str
    status: str
    queued_at: str


# ── Helpers ───────────────────────────────────────────────────────────────────


async def _require_workspace(workspace_id: str, db: AsyncSession) -> WorkspaceRow:
    result = await db.execute(
        select(WorkspaceRow).where(WorkspaceRow.id == workspace_id)
    )
    row = result.scalar_one_or_none()
    if row is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Workspace {workspace_id!r} not found",
        )
    return row


def _vault_dir(workspace_id: str) -> Path:
    return Path(settings.vault_path) / workspace_id


def _run_inline_check(workspace_id: str, db_sources: list) -> dict:
    """Run health checks synchronously in-process and return a serialised report."""
    from atlas_worker.health.vault_health import check_vault
    from atlas_worker.health.source_health import check_sources

    vault_dir = _vault_dir(workspace_id)
    vault_report = check_vault(vault_dir)

    # Build lightweight source records from ORM rows
    class _SourceProxy:
        def __init__(self, row: SourceRow) -> None:
            self.id = row.id
            self.workspace_id = row.workspace_id
            self.status = row.status
            # vault_note_path is not yet stored on SourceRow; derive from storage_key
            # convention: vault/{workspace_id}/sources/{id}.md
            self.vault_note_path: str | None = None
            self.manifest = row.manifest

    source_proxies = [_SourceProxy(r) for r in db_sources]
    source_report = check_sources(source_proxies, vault_dir)

    # Merge both reports into one
    all_issues = vault_report.issues + source_report.issues
    merged_stats = {**vault_report.stats, **source_report.stats}
    error_count = sum(1 for i in all_issues if i.severity == "error")
    warning_count = sum(1 for i in all_issues if i.severity == "warning")

    return {
        "workspace_id": workspace_id,
        "healthy": error_count == 0,
        "error_count": error_count,
        "warning_count": warning_count,
        "checked_at": datetime.now(tz=timezone.utc).isoformat(),
        "stats": merged_stats,
        "issues": [
            {
                "severity": i.severity,
                "code": i.code,
                "message": i.message,
                "path": i.path,
            }
            for i in all_issues
        ],
    }


# ── Routes ────────────────────────────────────────────────────────────────────


@router.get("", response_model=WorkspaceHealthSummary)
async def get_workspace_health(
    workspace_id: str,
    db: AsyncSession = Depends(get_db),
) -> WorkspaceHealthSummary:
    """Return the latest health report for a workspace.

    If a completed HEALTH_CHECK job exists, returns its stored result.
    Otherwise runs the check inline (synchronous; suitable for small vaults).
    """
    await _require_workspace(workspace_id, db)

    # Try to return the latest completed health check job result.
    result = await db.execute(
        select(JobRow)
        .where(
            JobRow.workspace_id == workspace_id,
            JobRow.kind == JobKind.HEALTH_CHECK,
            JobRow.status == JobStatus.SUCCEEDED,
        )
        .order_by(JobRow.completed_at.desc())
        .limit(1)
    )
    latest_job = result.scalar_one_or_none()

    if latest_job and latest_job.result:
        raw = latest_job.result
        return WorkspaceHealthSummary(
            workspace_id=raw.get("workspace_id", workspace_id),
            healthy=raw.get("healthy", True),
            error_count=raw.get("error_count", 0),
            warning_count=raw.get("warning_count", 0),
            checked_at=raw.get("checked_at", ""),
            stats=raw.get("stats", {}),
            issues=[HealthIssueSummary(**i) for i in raw.get("issues", [])],
        )

    # No prior result — run inline.
    sources_result = await db.execute(
        select(SourceRow).where(SourceRow.workspace_id == workspace_id)
    )
    db_sources = list(sources_result.scalars().all())

    try:
        report_dict = _run_inline_check(workspace_id, db_sources)
    except Exception as exc:
        logger.exception("inline health check failed for workspace %s", workspace_id)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Health check failed: {exc}",
        ) from exc

    return WorkspaceHealthSummary(
        workspace_id=report_dict["workspace_id"],
        healthy=report_dict["healthy"],
        error_count=report_dict["error_count"],
        warning_count=report_dict["warning_count"],
        checked_at=report_dict["checked_at"],
        stats=report_dict["stats"],
        issues=[HealthIssueSummary(**i) for i in report_dict["issues"]],
    )


@router.post("/run", response_model=HealthRunResponse, status_code=status.HTTP_202_ACCEPTED)
async def run_workspace_health_check(
    workspace_id: str,
    db: AsyncSession = Depends(get_db),
) -> HealthRunResponse:
    """Enqueue a full health check job and return the job record.

    The worker picks up the HEALTH_CHECK job, runs vault and source checks,
    and stores the result dict in job.result.
    """
    await _require_workspace(workspace_id, db)

    now = datetime.now(tz=timezone.utc)
    job_id = f"job_{uuid.uuid4().hex}"

    job_row = JobRow(
        id=job_id,
        workspace_id=workspace_id,
        kind=JobKind.HEALTH_CHECK,
        status=JobStatus.QUEUED,
        payload={"workspace_id": workspace_id},
        result=None,
        error=None,
        attempt=0,
        max_attempts=3,
        queued_at=now,
        started_at=None,
        completed_at=None,
    )
    db.add(job_row)
    await db.flush()

    logger.info("enqueued HEALTH_CHECK job %s for workspace %s", job_id, workspace_id)

    return HealthRunResponse(
        job_id=job_id,
        workspace_id=workspace_id,
        status=JobStatus.QUEUED,
        queued_at=now.isoformat(),
    )
