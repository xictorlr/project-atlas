"""Source domain models — mirrors packages/shared/src/types/source.ts."""

from pydantic import BaseModel, ConfigDict

from atlas_api.models.enums import SourceKind, SourceStatus


class SourceManifest(BaseModel):
    model_config = ConfigDict(frozen=True)

    ingested_at: str
    normalized_at: str | None
    origin_url: str | None
    mime_type: str | None
    file_size_bytes: int | None
    chunk_count: int | None
    model: str | None
    confidence_notes: str | None
    needs_reingest: bool = False


class Source(BaseModel):
    model_config = ConfigDict(frozen=True)

    id: str
    workspace_id: str
    kind: SourceKind
    status: SourceStatus
    title: str
    description: str | None
    storage_key: str
    manifest: SourceManifest | None
    created_at: str
    updated_at: str
