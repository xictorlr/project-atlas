"""Local file storage service for source artifacts.

Storage layout: {base_dir}/{workspace_id}/{source_id}/{filename}
Storage key format: {workspace_id}/{source_id}/{filename}

Interface is designed so the local disk implementation can be swapped
for S3/GCS by replacing this module — callers depend only on the three
public functions.
"""

import hashlib
import logging
from dataclasses import dataclass
from pathlib import Path

from atlas_api.config import settings

logger = logging.getLogger(__name__)


def _storage_root() -> Path:
    """Resolve the storage root from vault_path config.

    Places storage/ as a sibling of the vault directory so the vault
    itself remains a clean Markdown-only directory.
    """
    vault = Path(settings.vault_path).resolve()
    return vault.parent / "storage"


@dataclass(frozen=True)
class SaveResult:
    """Returned by save_file — carries the key and content hash."""

    storage_key: str
    sha256: str
    file_size_bytes: int


def save_file(
    workspace_id: str,
    source_id: str,
    content: bytes,
    filename: str,
) -> SaveResult:
    """Write content to local disk and return its storage key and hash.

    Creates parent directories on first write. The operation is
    idempotent: writing the same bytes to the same key overwrites
    silently (safe for retries).

    Args:
        workspace_id: Workspace UUID that owns the source.
        source_id: Source UUID — used as the directory name under workspace.
        content: Raw file bytes.
        filename: Original filename (used as the leaf name in storage).

    Returns:
        SaveResult with storage_key, sha256 hex digest, and file_size_bytes.

    Raises:
        OSError: If the directory cannot be created or the file cannot be written.
    """
    storage_key = f"{workspace_id}/{source_id}/{filename}"
    dest = _storage_root() / storage_key
    dest.parent.mkdir(parents=True, exist_ok=True)

    dest.write_bytes(content)

    sha256 = hashlib.sha256(content).hexdigest()
    logger.info(
        "Stored file",
        extra={
            "storage_key": storage_key,
            "sha256": sha256,
            "file_size_bytes": len(content),
        },
    )
    return SaveResult(
        storage_key=storage_key,
        sha256=sha256,
        file_size_bytes=len(content),
    )


def get_file(storage_key: str) -> bytes:
    """Read a stored file by its storage key.

    Args:
        storage_key: The key returned by save_file.

    Returns:
        Raw file bytes.

    Raises:
        FileNotFoundError: If no file exists at the given key.
        ValueError: If storage_key contains path-traversal sequences.
    """
    _validate_storage_key(storage_key)
    path = _storage_root() / storage_key
    if not path.is_file():
        raise FileNotFoundError(f"No stored file at key: {storage_key}")
    return path.read_bytes()


def delete_file(storage_key: str) -> None:
    """Delete a stored file by its storage key.

    No-op if the file does not exist (idempotent delete).

    Args:
        storage_key: The key returned by save_file.

    Raises:
        ValueError: If storage_key contains path-traversal sequences.
    """
    _validate_storage_key(storage_key)
    path = _storage_root() / storage_key
    if path.is_file():
        path.unlink()
        logger.info("Deleted stored file", extra={"storage_key": storage_key})


def _validate_storage_key(storage_key: str) -> None:
    """Reject keys that would escape the storage root via path traversal."""
    if ".." in Path(storage_key).parts:
        raise ValueError(f"Invalid storage key (path traversal detected): {storage_key}")
