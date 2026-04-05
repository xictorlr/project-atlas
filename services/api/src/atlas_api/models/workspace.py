"""Workspace domain models — mirrors packages/shared/src/types/workspace.ts."""

from pydantic import BaseModel, ConfigDict

from atlas_api.models.enums import WorkspaceRole


class WorkspaceMember(BaseModel):
    model_config = ConfigDict(frozen=True)

    user_id: str
    role: WorkspaceRole
    joined_at: str


class Workspace(BaseModel):
    model_config = ConfigDict(frozen=True)

    id: str
    slug: str
    name: str
    description: str | None
    owner_id: str
    members: tuple[WorkspaceMember, ...]
    is_private: bool
    created_at: str
    updated_at: str
