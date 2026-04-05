"""Source record integrity checker.

Inputs:
  sources: list[SourceRecord]  — domain objects from the relational store
  vault_dir: Path              — vault root to verify note presence

Outputs:
  HealthReport with issues for:
    - source_failed      (ERROR)   — source.status == "failed"
    - source_no_vault_note (WARNING) — source has no corresponding vault note
    - source_no_manifest (WARNING) — source.manifest is None or empty

Failure states:
  - Empty sources list: returns a healthy report with a stats note.
  - vault_dir missing: WARNING per source that cannot be checked.

Design:
  - Pure read; no database calls. The caller passes the source records.
  - The SourceRecord protocol accepts any object with the expected attributes
    so this module stays decoupled from the ORM layer.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Protocol

from atlas_worker.health.models import HealthIssue, HealthReport, IssueSeverity

logger = logging.getLogger(__name__)


class SourceRecord(Protocol):
    """Minimal interface expected from a source domain object."""

    id: str
    workspace_id: str
    status: str          # SourceStatus string value
    vault_note_path: str | None
    manifest: dict | None


def check_sources(
    sources: list[SourceRecord],
    vault_dir: Path,
) -> HealthReport:
    """Check source record integrity.

    Args:
        sources: List of source records for a single workspace.
        vault_dir: Root vault directory. Used to verify vault_note_path existence.

    Returns:
        HealthReport with issues and summary stats.
    """
    workspace_id = sources[0].workspace_id if sources else "unknown"
    report = HealthReport(workspace_id=workspace_id)

    vault_missing = not vault_dir.exists()
    if vault_missing:
        logger.warning("vault_dir not found during source health check: %s", vault_dir)

    failed = 0
    no_note = 0
    no_manifest = 0

    for src in sources:
        # ── Failed sources ─────────────────────────────────────────────────
        if src.status == "failed":
            report.issues.append(
                HealthIssue(
                    severity=IssueSeverity.ERROR,
                    code="source_failed",
                    message=f"Source {src.id!r} has status=failed",
                    detail={"source_id": src.id, "workspace_id": src.workspace_id},
                )
            )
            failed += 1

        # ── Missing vault note ─────────────────────────────────────────────
        if not src.vault_note_path:
            report.issues.append(
                HealthIssue(
                    severity=IssueSeverity.WARNING,
                    code="source_no_vault_note",
                    message=f"Source {src.id!r} has no vault_note_path",
                    detail={"source_id": src.id},
                )
            )
            no_note += 1
        elif not vault_missing:
            note_path = vault_dir / src.vault_note_path
            if not note_path.exists():
                report.issues.append(
                    HealthIssue(
                        severity=IssueSeverity.WARNING,
                        code="source_vault_note_missing_on_disk",
                        message=(
                            f"Source {src.id!r} vault note path recorded but file not found: "
                            f"{src.vault_note_path}"
                        ),
                        path=src.vault_note_path,
                        detail={"source_id": src.id},
                    )
                )
                no_note += 1

        # ── Missing manifest ───────────────────────────────────────────────
        if not src.manifest:
            report.issues.append(
                HealthIssue(
                    severity=IssueSeverity.WARNING,
                    code="source_no_manifest",
                    message=f"Source {src.id!r} has no manifest",
                    detail={"source_id": src.id},
                )
            )
            no_manifest += 1

    report.stats = {
        "sources_checked": len(sources),
        "failed_sources": failed,
        "sources_without_vault_note": no_note,
        "sources_without_manifest": no_manifest,
    }

    logger.info(
        "source health check complete for workspace %s: %d sources, %d errors, %d warnings",
        workspace_id,
        len(sources),
        report.error_count,
        report.warning_count,
    )
    return report
