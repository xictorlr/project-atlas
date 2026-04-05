"""Output artifact domain models — mirrors packages/shared/src/types/output.ts."""

from pydantic import BaseModel, ConfigDict

from atlas_api.models.enums import OutputArtifactKind


class OutputArtifact(BaseModel):
    model_config = ConfigDict(frozen=True)

    id: str
    workspace_id: str
    kind: OutputArtifactKind
    title: str
    storage_key: str | None
    public_url: str | None
    evidence_pack_id: str | None
    generated_at: str
    model: str | None
    confidence_notes: str | None
    source_count: int
    created_at: str
    updated_at: str
