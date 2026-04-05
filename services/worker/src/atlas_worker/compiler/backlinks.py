"""Backlink verifier for vault notes.

Scans all .md files in a workspace vault directory for [[wikilinks]] and
verifies that their targets exist on disk.

Inputs:
  - workspace_vault_dir: Path to vault/{workspace_id}/

Outputs:
  - BacklinkReport: broken links, valid links, and per-note details

Design:
  - Pure read operation — never modifies files.
  - Broken links are logged at WARNING level.
  - wikilink syntax: [[path/to/target]] or [[path/to/target|Display Text]]
    The path is resolved relative to the workspace vault dir.
    Extension .md is assumed if not present.
"""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass, field
from pathlib import Path

logger = logging.getLogger(__name__)

_WIKILINK_RE = re.compile(r"\[\[([^\]|#\n]+?)(?:\|[^\]]*?)?\]\]")


# ---------------------------------------------------------------------------
# Data contracts
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class BrokenLink:
    source_file: Path
    raw_target: str  # e.g. "entities/unknown-org"
    resolved_path: Path  # absolute path that was checked


@dataclass
class BacklinkReport:
    workspace_id: str
    notes_scanned: int = 0
    valid_links: int = 0
    broken_links: list[BrokenLink] = field(default_factory=list)

    @property
    def broken_count(self) -> int:
        return len(self.broken_links)

    @property
    def total_links(self) -> int:
        return self.valid_links + self.broken_count


# ---------------------------------------------------------------------------
# Core logic
# ---------------------------------------------------------------------------


def _extract_wikilinks(text: str) -> list[str]:
    """Return all raw wikilink targets from a Markdown body."""
    return [m.group(1).strip() for m in _WIKILINK_RE.finditer(text)]


def _resolve_target(raw: str, workspace_vault_dir: Path) -> Path:
    """Resolve a wikilink target to an absolute path.

    Assumes .md extension if none given.
    """
    target = raw.strip()
    if not target.endswith(".md"):
        target = target + ".md"
    return workspace_vault_dir / target


def verify_all(workspace_vault_dir: Path) -> BacklinkReport:
    """Scan all notes in workspace_vault_dir and report broken wikilinks.

    Args:
        workspace_vault_dir: Absolute path to vault/{workspace_id}/

    Returns:
        BacklinkReport with counts and broken link details.
    """
    workspace_id = workspace_vault_dir.name
    report = BacklinkReport(workspace_id=workspace_id)

    if not workspace_vault_dir.exists():
        logger.warning("workspace vault dir does not exist: %s", workspace_vault_dir)
        return report

    md_files = sorted(workspace_vault_dir.rglob("*.md"))
    report.notes_scanned = len(md_files)

    for note_path in md_files:
        try:
            text = note_path.read_text(encoding="utf-8")
        except OSError as exc:
            logger.error("could not read %s: %s", note_path, exc)
            continue

        targets = _extract_wikilinks(text)
        for raw in targets:
            resolved = _resolve_target(raw, workspace_vault_dir)
            if resolved.exists():
                report.valid_links += 1
            else:
                broken = BrokenLink(
                    source_file=note_path,
                    raw_target=raw,
                    resolved_path=resolved,
                )
                report.broken_links.append(broken)
                logger.warning(
                    "broken wikilink in %s: [[%s]] -> %s (not found)",
                    note_path.relative_to(workspace_vault_dir),
                    raw,
                    resolved,
                )

    logger.info(
        "backlink check complete: %d notes, %d valid, %d broken",
        report.notes_scanned,
        report.valid_links,
        report.broken_count,
    )
    return report
