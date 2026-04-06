"""Eval execution endpoint.

Route:
  POST /api/v1/evals/run
       Body: {eval_type, workspace_id, test_cases}
       Returns: EvalSuite with per-case results and aggregate metrics.

Supported eval_type values:
  - "search"   — precision@k, recall@k, MRR
  - "compiler" — frontmatter completeness, entity coverage, backlink density

Failure states:
  - Unknown eval_type: 400
  - Workspace not found: 404 (verified before running to fail fast)
  - Individual test case failures are captured in EvalResult.error; the suite
    still returns 200 with those cases marked passed=False.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from atlas_api.config import settings
from atlas_api.db import get_db
from atlas_api.evals.compiler_eval import compute_compiler_metrics
from atlas_api.evals.models import EvalSuite, EvalTestCase
from atlas_api.evals.search_eval import compute_search_metrics
from atlas_api.schemas.workspace import WorkspaceRow

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/evals", tags=["evals"])

_SUPPORTED_EVAL_TYPES = frozenset({"search", "compiler"})


# ── Request / response bodies ─────────────────────────────────────────────────


class EvalRunRequest(BaseModel):
    eval_type: str
    workspace_id: str
    test_cases: list[dict[str, Any]]
    k: int = 5  # rank cutoff for search evals


# ── Helpers ───────────────────────────────────────────────────────────────────


async def _require_workspace(workspace_id: str, db: AsyncSession) -> None:
    result = await db.execute(
        select(WorkspaceRow).where(WorkspaceRow.id == workspace_id)
    )
    if result.scalar_one_or_none() is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Workspace {workspace_id!r} not found",
        )


def _make_search_fn(k: int):
    """Return a synchronous search wrapper over the TF-IDF index."""

    def _search(query: str, workspace_id: str, _k: int) -> list[str]:
        from atlas_api.search.indexer import get_or_build_index
        from atlas_api.search.query import execute_search_lexical

        vault_root = Path(settings.vault_path) / workspace_id
        idx = get_or_build_index(vault_root, workspace_id)
        hits = execute_search_lexical(idx, query, limit=_k)
        return [h.slug for h in hits]

    return _search


# ── Route ─────────────────────────────────────────────────────────────────────


@router.post("/run", response_model=EvalSuite)
async def run_evals(
    body: EvalRunRequest,
    db: AsyncSession = Depends(get_db),
) -> EvalSuite:
    """Run an eval suite and return results with aggregate metrics.

    Supported eval_type values: "search", "compiler".
    """
    if body.eval_type not in _SUPPORTED_EVAL_TYPES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unknown eval_type {body.eval_type!r}. Supported: {sorted(_SUPPORTED_EVAL_TYPES)}",
        )

    await _require_workspace(body.workspace_id, db)

    test_cases = [EvalTestCase(**tc) for tc in body.test_cases]

    if body.eval_type == "search":
        search_fn = _make_search_fn(body.k)
        suite = compute_search_metrics(
            test_cases=test_cases,
            search_fn=search_fn,
            workspace_id=body.workspace_id,
            k=body.k,
        )
    else:  # compiler
        vault_root = Path(settings.vault_path)
        suite = compute_compiler_metrics(
            test_cases=test_cases,
            vault_root=vault_root,
            workspace_id=body.workspace_id,
        )

    logger.info(
        "eval run complete: type=%s workspace=%s cases=%d pass_rate=%.2f",
        body.eval_type,
        body.workspace_id,
        suite.total_cases,
        suite.pass_rate,
    )
    return suite
