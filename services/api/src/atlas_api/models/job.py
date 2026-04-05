"""Job domain models — mirrors packages/shared/src/types/job.ts."""

from typing import Any

from pydantic import BaseModel, ConfigDict

from atlas_api.models.enums import JobKind, JobStatus


class JobError(BaseModel):
    model_config = ConfigDict(frozen=True)

    code: str
    message: str
    retryable: bool


class Job(BaseModel):
    model_config = ConfigDict(frozen=True)

    id: str
    workspace_id: str
    kind: JobKind
    status: JobStatus
    payload: dict[str, Any]
    result: dict[str, Any] | None
    error: JobError | None
    attempt: int
    max_attempts: int
    queued_at: str
    started_at: str | None
    completed_at: str | None
