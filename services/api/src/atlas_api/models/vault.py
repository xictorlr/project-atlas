"""Vault note domain models — mirrors packages/shared/src/types/vault.ts."""

from pydantic import BaseModel, ConfigDict

from atlas_api.models.enums import VaultNoteKind


class VaultNoteFrontmatter(BaseModel):
    model_config = ConfigDict(frozen=True)

    title: str
    slug: str
    kind: VaultNoteKind
    workspace_id: str
    source_ids: tuple[str, ...]
    generated_at: str
    model: str | None
    confidence_notes: str | None
    backlinks: tuple[str, ...]
    tags: tuple[str, ...]


class VaultNote(BaseModel):
    model_config = ConfigDict(frozen=True)

    id: str
    workspace_id: str
    kind: VaultNoteKind
    slug: str
    vault_path: str
    frontmatter: VaultNoteFrontmatter
    content_hash: str
    created_at: str
    updated_at: str
