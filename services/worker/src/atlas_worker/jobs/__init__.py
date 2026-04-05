"""Job registry — import all job modules here to register them with arq."""

from atlas_worker.jobs.ingest import ingest_source
from atlas_worker.jobs.compile import compile_vault

__all__ = ["ingest_source", "compile_vault"]
