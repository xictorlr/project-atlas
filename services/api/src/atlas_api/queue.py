"""Job queue helpers — enqueue work via arq/Redis.

All job payloads are also persisted to the jobs table before enqueuing
so the API can report status without polling Redis.
"""

import logging
import uuid
from datetime import datetime, timezone
from typing import Any

from arq import create_pool
from arq.connections import RedisSettings

from atlas_api.config import settings
from atlas_api.models.enums import JobKind, JobStatus
from atlas_api.schemas.job import JobRow

logger = logging.getLogger(__name__)

_JOB_KIND_MAP: dict[str, JobKind] = {
    "ingest_source": JobKind.INGEST,
    "compile_vault": JobKind.COMPILE,
}


async def enqueue_job(
    job_type: str,
    payload: dict[str, Any],
    workspace_id: str,
    db: Any,  # AsyncSession — typed as Any to avoid circular import
) -> JobRow:
    """Persist a job record and push it onto the Redis queue.

    Args:
        job_type: arq function name (e.g. "ingest_source", "compile_vault").
        payload:  Keyword arguments forwarded to the arq job function.
        workspace_id: Owning workspace — stored in the jobs table.
        db: Open AsyncSession; caller controls commit/rollback.

    Returns:
        The newly created JobRow (status=queued, flushed but not committed).

    Raises:
        KeyError: If job_type is not in the known job kind map.
        ConnectionError: If Redis is unreachable.
    """
    job_kind = _JOB_KIND_MAP.get(job_type)
    if job_kind is None:
        raise KeyError(f"Unknown job type: {job_type!r}")

    job_id = str(uuid.uuid4())
    now = datetime.now(tz=timezone.utc)

    job_row = JobRow(
        id=job_id,
        workspace_id=workspace_id,
        kind=job_kind,
        status=JobStatus.QUEUED,
        payload=payload,
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

    redis_settings = RedisSettings.from_dsn(settings.redis_queue_url)
    redis = await create_pool(redis_settings)
    try:
        await redis.enqueue_job(job_type, **payload, _job_id=job_id)
        logger.info(
            "Enqueued job",
            extra={"job_id": job_id, "job_type": job_type, "workspace_id": workspace_id},
        )
    finally:
        await redis.aclose()

    return job_row
