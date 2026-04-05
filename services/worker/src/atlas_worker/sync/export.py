"""Export a workspace vault as a ZIP archive or flat directory.

ZIP export includes:
  - All .md files from vault/{workspace_id}/
  - .obsidian/ config stub for immediate Obsidian compatibility

Failure states:
  - vault_dir does not exist: raises FileNotFoundError.
  - dest_path parent does not exist: raises FileNotFoundError.
  - Individual file write error: propagated to caller (no partial archives).
"""

from __future__ import annotations

import json
import logging
import zipfile
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

logger = logging.getLogger(__name__)

# Minimal .obsidian/app.json to mark as an Obsidian vault on open.
_OBSIDIAN_APP_JSON: dict[str, object] = {
    "promptDelete": False,
    "trashOption": "system",
}

# Minimal .obsidian/appearance.json
_OBSIDIAN_APPEARANCE_JSON: dict[str, object] = {
    "theme": "moonstone",
}


@dataclass(frozen=True)
class ExportResult:
    workspace_id: str
    dest_path: Path
    note_count: int
    exported_at: datetime

    @property
    def size_bytes(self) -> int:
        return self.dest_path.stat().st_size if self.dest_path.exists() else 0


class VaultExporter:
    """Export a workspace vault to a ZIP archive.

    Parameters
    ----------
    vault_dir:
        Root of the workspace's vault directory.
    workspace_id:
        Used as the top-level folder name inside the ZIP.
    """

    def __init__(self, vault_dir: Path, workspace_id: str) -> None:
        self._vault = vault_dir
        self._workspace_id = workspace_id

    def export_zip(self, dest_path: Path) -> ExportResult:
        """Write all vault .md files plus .obsidian config to a ZIP at dest_path.

        dest_path is overwritten if it exists. Parent must exist.
        """
        if not self._vault.exists():
            raise FileNotFoundError(
                f"Vault directory not found: {self._vault}"
            )

        prefix = self._workspace_id
        note_count = 0

        with zipfile.ZipFile(dest_path, mode="w", compression=zipfile.ZIP_DEFLATED) as zf:
            # Write .obsidian stub
            zf.writestr(
                f"{prefix}/.obsidian/app.json",
                json.dumps(_OBSIDIAN_APP_JSON, indent=2),
            )
            zf.writestr(
                f"{prefix}/.obsidian/appearance.json",
                json.dumps(_OBSIDIAN_APPEARANCE_JSON, indent=2),
            )

            # Write all .md files
            for md_file in sorted(self._vault.rglob("*.md")):
                if not md_file.is_file():
                    continue
                rel = md_file.relative_to(self._vault)
                arc_name = f"{prefix}/{rel}"
                zf.write(md_file, arcname=arc_name)
                note_count += 1
                logger.debug("exported note", extra={"arc_name": arc_name})

        logger.info(
            "vault exported",
            extra={
                "workspace_id": self._workspace_id,
                "note_count": note_count,
                "dest": str(dest_path),
            },
        )

        return ExportResult(
            workspace_id=self._workspace_id,
            dest_path=dest_path,
            note_count=note_count,
            exported_at=datetime.now(timezone.utc),
        )
