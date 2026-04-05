"""Entity domain models — mirrors packages/shared/src/types/entity.ts."""

from pydantic import BaseModel, ConfigDict

from atlas_api.models.enums import EntityKind


class Entity(BaseModel):
    model_config = ConfigDict(frozen=True)

    id: str
    workspace_id: str
    kind: EntityKind
    name: str
    slug: str
    aliases: tuple[str, ...]
    vault_note_id: str | None
    source_ids: tuple[str, ...]
    created_at: str
    updated_at: str
