"""Worker entry point — starts the arq worker process."""

import asyncio
import logging

from arq import run_worker
from arq.connections import RedisSettings

from atlas_worker.config import worker_settings
from atlas_worker.jobs import compile_vault, ingest_source

logger = logging.getLogger(__name__)


class WorkerConfig:
    """arq worker configuration."""

    functions = [ingest_source, compile_vault]
    redis_settings = RedisSettings.from_dsn(worker_settings.redis_url)
    max_jobs = worker_settings.max_jobs
    job_timeout = worker_settings.job_timeout
    on_startup = None
    on_shutdown = None


def main() -> None:
    """CLI entry point for atlas-worker."""
    logging.basicConfig(
        level=getattr(logging, worker_settings.log_level.upper(), logging.INFO),
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
    )
    logger.info("Starting atlas-worker", extra={"environment": worker_settings.environment})
    asyncio.run(run_worker(WorkerConfig))  # type: ignore[arg-type]


if __name__ == "__main__":
    main()
