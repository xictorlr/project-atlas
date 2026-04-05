"""Vault compilation job — orchestrates the full compiler pipeline.

Pipeline:
  1. Query all sources with status=ingested for the workspace.
  2. For each source, run source_notes.generate_source_note().
  3. For each compiled source, run entity_extraction.extract_and_generate().
  4. Run index_generator.rebuild_indexes().
  5. Run backlinks.verify_all().
  6. Return job result manifest.

Idempotency:
  - Re-running on an already-compiled source updates, not duplicates.
  - vault_writer handles the "created / updated / skipped / conflict" logic.

This job works with either a real DB context or a plain fixture dict for tests.
The ctx dict is expected to contain:
  - "vault_root":  Path  (required — where to write vault notes)
  - "db":          optional async SQLAlchemy session

When no DB session is present the job accepts an explicit `sources` list of
SourceRecord objects so unit tests can drive the pipeline without a database.
"""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from atlas_worker.compiler import backlinks, entity_extraction, index_generator, source_notes
from atlas_worker.compiler.source_notes import SourceRecord, SourceNoteResult

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Result manifest
# ---------------------------------------------------------------------------


@dataclass
class CompileVaultResult:
    job: str = "compile_vault"
    workspace_id: str = ""
    status: str = "ok"
    notes_created: int = 0
    notes_updated: int = 0
    notes_skipped: int = 0
    notes_conflict: int = 0
    entities_found: int = 0
    broken_links: int = 0
    total_time_ms: int = 0
    errors: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "job": self.job,
            "workspace_id": self.workspace_id,
            "status": self.status,
            "notes_created": self.notes_created,
            "notes_updated": self.notes_updated,
            "notes_skipped": self.notes_skipped,
            "notes_conflict": self.notes_conflict,
            "entities_found": self.entities_found,
            "broken_links": self.broken_links,
            "total_time_ms": self.total_time_ms,
            "errors": self.errors,
        }


# ---------------------------------------------------------------------------
# DB query stub (replaced by real implementation once DB layer exists)
# ---------------------------------------------------------------------------


async def _query_ingested_sources(db: Any, workspace_id: str) -> list[SourceRecord]:
    """Query the DB for all sources with status=ingested.

    Returns an empty list if db is None or not yet implemented.
    """
    if db is None:
        return []
    # TODO: replace with actual ORM query once models are wired
    # e.g.: result = await db.execute(select(Source).where(...))
    return []


async def _mark_source_compiled(db: Any, source_id: str) -> None:
    """Update source record status to 'compiled'."""
    if db is None:
        return
    # TODO: update source record in DB


# ---------------------------------------------------------------------------
# Orchestrator
# ---------------------------------------------------------------------------


async def compile_vault(
    ctx: dict,
    workspace_id: str,
    *,
    sources: list[SourceRecord] | None = None,
    job_id: str = "job_unknown",
) -> dict[str, Any]:
    """Compile ingested sources into Markdown vault entries.

    Args:
        ctx:          arq context. Expected keys: `vault_root` (Path), `db` (optional).
        workspace_id: UUID of the workspace to compile.
        sources:      Optional explicit list of SourceRecord objects (for tests /
                      direct invocation without a DB).
        job_id:       Job identifier injected by the caller for provenance.

    Returns:
        Job result manifest dict.
    """
    start = time.monotonic()
    result = CompileVaultResult(workspace_id=workspace_id)

    vault_root: Path = ctx.get("vault_root", Path("vault"))
    db: Any = ctx.get("db")

    # 1. Collect sources to compile.
    if sources is None:
        sources = await _query_ingested_sources(db, workspace_id)

    workspace_vault_dir = vault_root / workspace_id

    # 2. Source note generation.
    compiled_pairs: list[tuple[SourceRecord, SourceNoteResult]] = []
    for record in sources:
        try:
            note_result = source_notes.generate_source_note(record, vault_root)
            compiled_pairs.append((record, note_result))

            if note_result.action == "created":
                result.notes_created += 1
            elif note_result.action == "updated":
                result.notes_updated += 1
            elif note_result.action == "skipped":
                result.notes_skipped += 1
            elif note_result.action == "conflict":
                result.notes_conflict += 1
                logger.warning(
                    "conflict on source note %s — skipping entity extraction for this source",
                    note_result.path,
                )
                continue

            await _mark_source_compiled(db, record.source_id)

        except Exception as exc:
            msg = f"source_notes failed for {record.source_id}: {exc}"
            logger.error(msg)
            result.errors.append(msg)
            continue

    # 3. Entity extraction for successfully written notes.
    for record, note_result in compiled_pairs:
        if note_result.action == "conflict":
            continue
        try:
            note_text = note_result.path.read_text(encoding="utf-8") if note_result.path.exists() else ""
            extraction = entity_extraction.extract_and_generate(
                record=record,
                note_text=note_text,
                vault_root=vault_root,
                compile_job_id=job_id,
                source_note_path=note_result.path,
            )
            result.entities_found += len(extraction.entities)
        except Exception as exc:
            msg = f"entity_extraction failed for {record.source_id}: {exc}"
            logger.error(msg)
            result.errors.append(msg)

    # 4. Rebuild indexes.
    try:
        index_generator.rebuild_indexes(workspace_vault_dir)
    except Exception as exc:
        msg = f"index_generator failed: {exc}"
        logger.error(msg)
        result.errors.append(msg)

    # 5. Backlink verification.
    try:
        backlink_report = backlinks.verify_all(workspace_vault_dir)
        result.broken_links = backlink_report.broken_count
    except Exception as exc:
        msg = f"backlinks.verify_all failed: {exc}"
        logger.error(msg)
        result.errors.append(msg)

    result.total_time_ms = int((time.monotonic() - start) * 1000)
    if result.errors:
        result.status = "partial"

    logger.info(
        "compile_vault complete: workspace=%s created=%d updated=%d "
        "skipped=%d conflict=%d entities=%d broken_links=%d errors=%d time=%dms",
        workspace_id,
        result.notes_created,
        result.notes_updated,
        result.notes_skipped,
        result.notes_conflict,
        result.entities_found,
        result.broken_links,
        len(result.errors),
        result.total_time_ms,
    )

    return result.to_dict()
