"""Evidence pack endpoint — assemble grounded excerpts for answer generation."""

from pathlib import Path

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field

from atlas_api.config import settings
from atlas_api.models.evidence import EvidencePack
from atlas_api.search.evidence import build_evidence_pack
from atlas_api.search.indexer import get_or_build_index
from atlas_api.search.query import execute_search

router = APIRouter(
    prefix="/workspaces/{workspace_id}/evidence",
    tags=["evidence"],
)


class EvidenceRequest(BaseModel):
    query: str = Field(..., min_length=1, description="Query to ground evidence against")
    max_sources: int = Field(default=10, ge=1, le=50)


def _vault_root(workspace_id: str) -> Path:
    base = Path(settings.vault_path)
    candidate = base / workspace_id
    return candidate if candidate.exists() else base


@router.post("", response_model=EvidencePack, status_code=status.HTTP_200_OK)
async def assemble_evidence(
    workspace_id: str,
    body: EvidenceRequest,
) -> EvidencePack:
    """Search vault notes and return an EvidencePack for answer grounding.

    Steps:
    1. Execute lexical search for the query.
    2. For each top result, load its body from disk.
    3. Build and return the EvidencePack.
    """
    vault_root = _vault_root(workspace_id)
    idx = get_or_build_index(vault_root, workspace_id)
    results = execute_search(idx, body.query, limit=body.max_sources)

    if not results:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No matching notes found for the given query",
        )

    # Load note bodies for passage extraction
    note_bodies: dict[str, str] = {}
    for result in results:
        note_record = idx.notes.get(result.slug)
        if note_record is not None:
            note_bodies[result.slug] = note_record.body

    return build_evidence_pack(
        workspace_id=workspace_id,
        query=body.query,
        results=results,
        note_bodies=note_bodies,
        max_sources=body.max_sources,
    )
