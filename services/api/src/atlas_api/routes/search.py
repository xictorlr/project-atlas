"""Search endpoints — lexical search over vault notes per workspace."""

from pathlib import Path

from fastapi import APIRouter, HTTPException, Query, status

from atlas_api.config import settings
from atlas_api.search.indexer import get_or_build_index, invalidate_index
from atlas_api.search.models import SearchResponse
from atlas_api.search.query import execute_search_lexical as execute_search

router = APIRouter(
    prefix="/workspaces/{workspace_id}/search",
    tags=["search"],
)


def _vault_root(workspace_id: str) -> Path:
    """Resolve the vault root path for a workspace.

    Convention: {vault_path}/{workspace_id}/ — falls back to {vault_path}/ when the
    workspace subdirectory does not exist (dev single-workspace layout).
    """
    base = Path(settings.vault_path)
    candidate = base / workspace_id
    return candidate if candidate.exists() else base


@router.get("", response_model=SearchResponse)
async def search_vault(
    workspace_id: str,
    q: str = Query(..., min_length=1, description="Search query"),
    limit: int = Query(default=20, ge=1, le=100, description="Maximum results to return"),
) -> SearchResponse:
    """Lexical TF-IDF search over vault notes for a workspace.

    Index is built lazily on first request and cached in memory.
    """
    vault_root = _vault_root(workspace_id)
    idx = get_or_build_index(vault_root, workspace_id)

    results = execute_search(idx, q, limit=limit)

    return SearchResponse(
        query=q,
        total=len(results),
        results=tuple(results),
    )


@router.post("/reindex", status_code=status.HTTP_204_NO_CONTENT)
async def reindex_vault(workspace_id: str) -> None:
    """Invalidate the cached index so the next search request rebuilds it.

    Call this after an ingest or compile job completes.
    """
    invalidate_index(workspace_id)
