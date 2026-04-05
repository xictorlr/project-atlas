"""Evidence domain models — mirrors packages/shared/src/types/evidence.ts."""

from pydantic import BaseModel, ConfigDict


class EvidenceExcerpt(BaseModel):
    model_config = ConfigDict(frozen=True)

    source_id: str
    chunk_index: int
    text: str
    score: float
    location_hint: str | None


class EvidencePack(BaseModel):
    model_config = ConfigDict(frozen=True)

    id: str
    workspace_id: str
    query: str
    excerpts: tuple[EvidenceExcerpt, ...]
    note_refs: tuple[str, ...]
    model: str | None
    generated_at: str
