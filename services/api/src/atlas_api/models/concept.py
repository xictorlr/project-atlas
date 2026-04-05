"""Concept domain models — mirrors packages/shared/src/types/concept.ts."""

from pydantic import BaseModel, ConfigDict


class Concept(BaseModel):
    model_config = ConfigDict(frozen=True)

    id: str
    workspace_id: str
    name: str
    slug: str
    summary: str | None
    vault_note_id: str | None
    source_ids: tuple[str, ...]
    generated_at: str | None
    model: str | None
    created_at: str
    updated_at: str
