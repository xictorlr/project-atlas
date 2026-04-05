"""Bidirectional sync between an Atlas vault directory and an Obsidian vault.

Workflow (push):
  1. Walk atlas_dir looking for .md files newer than last sync time.
  2. For each changed file, copy to obsidian_dir preserving relative path.
  3. Record pushed files in SyncResult.

Workflow (pull):
  1. Walk obsidian_dir looking for .md files newer than last sync time.
  2. For each changed file, check if corresponding atlas file was also modified.
     - If atlas file is unchanged: overwrite atlas file with obsidian version.
     - If both changed (conflict): write atlas conflict note alongside original.
  3. Record pulled and conflicted files in SyncResult.

Failure states:
  - obsidian_dir does not exist: raises FileNotFoundError (caller should log and skip).
  - Individual file copy failure: logged, file added to errors list, sync continues.
  - Permission error: logged, added to errors list.
"""

from __future__ import annotations

import logging
import shutil
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path

logger = logging.getLogger(__name__)

_CONFLICT_SUFFIX = ".conflict"


@dataclass(frozen=True)
class SyncResult:
    pushed: tuple[str, ...] = field(default_factory=tuple)
    pulled: tuple[str, ...] = field(default_factory=tuple)
    conflicts: tuple[str, ...] = field(default_factory=tuple)
    errors: tuple[str, ...] = field(default_factory=tuple)
    synced_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    @property
    def has_errors(self) -> bool:
        return len(self.errors) > 0

    @property
    def summary(self) -> str:
        return (
            f"pushed={len(self.pushed)} pulled={len(self.pulled)} "
            f"conflicts={len(self.conflicts)} errors={len(self.errors)}"
        )


class ObsidianSyncer:
    """Sync a workspace vault directory against an Obsidian vault directory.

    Parameters
    ----------
    atlas_dir:
        Root of the Atlas workspace vault (e.g. vault/{workspace_id}/).
    obsidian_dir:
        Root of the user's Obsidian vault (configured per user/workspace).
    last_sync_at:
        UTC datetime of previous sync; files not modified since are skipped.
        Pass None to do a full sync.
    """

    def __init__(
        self,
        atlas_dir: Path,
        obsidian_dir: Path,
        last_sync_at: datetime | None = None,
    ) -> None:
        self._atlas = atlas_dir
        self._obsidian = obsidian_dir
        self._last_sync = last_sync_at

    def push(self) -> SyncResult:
        """Copy new/updated Atlas notes to the Obsidian vault."""
        if not self._obsidian.exists():
            raise FileNotFoundError(
                f"Obsidian vault directory not found: {self._obsidian}"
            )

        pushed: list[str] = []
        errors: list[str] = []

        for src in self._changed_files(self._atlas):
            rel = src.relative_to(self._atlas)
            dst = self._obsidian / rel
            try:
                dst.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(src, dst)
                pushed.append(str(rel))
                logger.debug("pushed note", extra={"path": str(rel)})
            except OSError as exc:
                logger.error("push failed", extra={"path": str(rel), "error": str(exc)})
                errors.append(str(rel))

        return SyncResult(
            pushed=tuple(pushed),
            errors=tuple(errors),
        )

    def pull(self) -> SyncResult:
        """Copy new/updated Obsidian edits back to the Atlas vault.

        Conflict rule: if both sides changed since last sync, write a
        *.conflict copy of the obsidian version alongside the atlas file
        instead of overwriting it.
        """
        if not self._obsidian.exists():
            raise FileNotFoundError(
                f"Obsidian vault directory not found: {self._obsidian}"
            )

        pulled: list[str] = []
        conflicts: list[str] = []
        errors: list[str] = []

        for src in self._changed_files(self._obsidian):
            rel = src.relative_to(self._obsidian)
            dst = self._atlas / rel
            try:
                dst.parent.mkdir(parents=True, exist_ok=True)
                if self._is_atlas_also_changed(dst):
                    conflict_path = dst.with_suffix(f"{_CONFLICT_SUFFIX}{dst.suffix}")
                    shutil.copy2(src, conflict_path)
                    conflicts.append(str(rel))
                    logger.warning(
                        "sync conflict — wrote conflict copy",
                        extra={"path": str(rel), "conflict_file": str(conflict_path)},
                    )
                else:
                    shutil.copy2(src, dst)
                    pulled.append(str(rel))
                    logger.debug("pulled note", extra={"path": str(rel)})
            except OSError as exc:
                logger.error("pull failed", extra={"path": str(rel), "error": str(exc)})
                errors.append(str(rel))

        return SyncResult(
            pulled=tuple(pulled),
            conflicts=tuple(conflicts),
            errors=tuple(errors),
        )

    # ── private helpers ────────────────────────────────────────────────────────

    def _changed_files(self, root: Path) -> list[Path]:
        """Return .md files under root modified after last_sync_at (or all if None)."""
        results: list[Path] = []
        for p in root.rglob("*.md"):
            if not p.is_file():
                continue
            if self._last_sync is None:
                results.append(p)
                continue
            mtime = datetime.fromtimestamp(p.stat().st_mtime, tz=timezone.utc)
            if mtime > self._last_sync:
                results.append(p)
        return results

    def _is_atlas_also_changed(self, atlas_path: Path) -> bool:
        """True if atlas_path exists and was modified after last_sync_at."""
        if not atlas_path.exists():
            return False
        if self._last_sync is None:
            return False
        mtime = datetime.fromtimestamp(atlas_path.stat().st_mtime, tz=timezone.utc)
        return mtime > self._last_sync
