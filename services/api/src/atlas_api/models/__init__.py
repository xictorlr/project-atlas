"""Domain models barrel — Pydantic v2 frozen models matching TypeScript contracts."""

from atlas_api.models.enums import (
    EntityKind,
    JobKind,
    JobStatus,
    OutputArtifactKind,
    SourceKind,
    SourceStatus,
    VaultNoteKind,
    WorkspaceRole,
)
from atlas_api.models.concept import Concept
from atlas_api.models.entity import Entity
from atlas_api.models.evidence import EvidenceExcerpt, EvidencePack
from atlas_api.models.job import Job, JobError
from atlas_api.models.output import OutputArtifact
from atlas_api.models.source import Source, SourceManifest
from atlas_api.models.vault import VaultNote, VaultNoteFrontmatter
from atlas_api.models.workspace import Workspace, WorkspaceMember

__all__ = [
    # Enums
    "EntityKind",
    "JobKind",
    "JobStatus",
    "OutputArtifactKind",
    "SourceKind",
    "SourceStatus",
    "VaultNoteKind",
    "WorkspaceRole",
    # Models
    "Concept",
    "Entity",
    "EvidenceExcerpt",
    "EvidencePack",
    "Job",
    "JobError",
    "OutputArtifact",
    "Source",
    "SourceManifest",
    "VaultNote",
    "VaultNoteFrontmatter",
    "Workspace",
    "WorkspaceMember",
]
