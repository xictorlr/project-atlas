"""Worker entry point — starts the arq worker process."""

import asyncio
import logging
from typing import Any

from arq import run_worker
from arq.connections import RedisSettings

from atlas_worker.config import worker_settings
from atlas_worker.inference.router import InferenceRouter
from atlas_worker.jobs import compile_vault, generate_output, ingest_source

logger = logging.getLogger(__name__)


async def on_startup(ctx: dict[str, Any]) -> None:
    """Initialize InferenceRouter and RAGPipeline, attach to worker context."""
    from atlas_worker.search.rag import RAGPipeline
    from atlas_worker.search.vector_store import PgVectorStore

    router = InferenceRouter.from_config(worker_settings)
    health = await router.health()
    logger.info(
        "InferenceRouter ready: ollama=%s whisper=%s vlm=%s overall=%s",
        health.ollama.available,
        health.whisper.available,
        health.vlm.available,
        health.overall_status,
    )
    ctx["router"] = router

    # RAG pipeline — needed by generate_output and adapters
    try:
        vector_store = PgVectorStore(worker_settings.database_url)
        rag = RAGPipeline(vector_store=vector_store, router=router)
        ctx["rag"] = rag
        logger.info("RAGPipeline ready")
    except Exception as exc:
        logger.warning("RAGPipeline not available: %s — output generation will be limited", exc)

    # Vault root path
    ctx["vault_root"] = worker_settings.root / "vault"


async def on_shutdown(ctx: dict[str, Any]) -> None:
    """Clean up inference resources."""
    router: InferenceRouter | None = ctx.get("router")
    if router:
        router.unload_all()
        await router.close()
    logger.info("Worker shutdown complete")


class WorkerConfig:
    """arq worker configuration."""

    functions = [ingest_source, compile_vault, generate_output]
    redis_settings = RedisSettings.from_dsn(worker_settings.redis_url)
    max_jobs = worker_settings.max_jobs
    job_timeout = worker_settings.job_timeout
    on_startup = on_startup
    on_shutdown = on_shutdown


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
