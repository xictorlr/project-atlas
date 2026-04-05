"""Search quality evaluator.

Inputs:
  test_cases: list[EvalTestCase] — each has query + relevant_slugs
  search_fn: Callable            — (query, workspace_id, k) -> list[str] (slugs)
  workspace_id: str
  k: int                         — cutoff for precision/recall/MRR (default 5)

Outputs:
  EvalSuite with per-case EvalResults containing:
    - precision@k  — fraction of top-k results that are relevant
    - recall@k     — fraction of relevant notes found in top-k
    - mrr          — mean reciprocal rank of first relevant result

  Aggregate metrics:
    - mean_precision@k
    - mean_recall@k
    - MRR

Failure states:
  - search_fn raises: EvalResult.error is set, passed=False, case is counted as failed.
  - Empty relevant_slugs: precision@k = 0, recall@k = 1.0 (nothing to miss), MRR = 0.

Design:
  - Pure computation; no I/O. The caller wires in the real search function.
  - All arithmetic is explicit; no external ML deps.
"""

from __future__ import annotations

import logging
from collections.abc import Callable

from atlas_api.evals.models import EvalResult, EvalSuite, EvalTestCase, MetricScore

logger = logging.getLogger(__name__)


def _precision_at_k(retrieved: list[str], relevant: set[str], k: int) -> float:
    top_k = retrieved[:k]
    if not top_k:
        return 0.0
    hits = sum(1 for slug in top_k if slug in relevant)
    return hits / len(top_k)


def _recall_at_k(retrieved: list[str], relevant: set[str], k: int) -> float:
    if not relevant:
        return 1.0  # nothing to find — convention
    top_k = retrieved[:k]
    hits = sum(1 for slug in top_k if slug in relevant)
    return hits / len(relevant)


def _reciprocal_rank(retrieved: list[str], relevant: set[str]) -> float:
    for rank, slug in enumerate(retrieved, start=1):
        if slug in relevant:
            return 1.0 / rank
    return 0.0


def _run_case(
    case: EvalTestCase,
    search_fn: Callable[[str, str, int], list[str]],
    workspace_id: str,
    k: int,
) -> EvalResult:
    if not case.query:
        return EvalResult(
            test_case_id=case.id,
            eval_type="search",
            passed=False,
            error="test case has no query field",
        )

    relevant = set(case.relevant_slugs)

    try:
        retrieved = search_fn(case.query, workspace_id, k)
    except Exception as exc:
        logger.warning("search_fn raised for case %s: %s", case.id, exc)
        return EvalResult(
            test_case_id=case.id,
            eval_type="search",
            passed=False,
            error=str(exc),
        )

    p_at_k = _precision_at_k(retrieved, relevant, k)
    r_at_k = _recall_at_k(retrieved, relevant, k)
    mrr = _reciprocal_rank(retrieved, relevant)

    # Pass criterion: at least one relevant result in top-k
    passed = any(slug in relevant for slug in retrieved[:k])

    return EvalResult(
        test_case_id=case.id,
        eval_type="search",
        passed=passed,
        metrics=[
            MetricScore(name=f"precision@{k}", value=round(p_at_k, 4)),
            MetricScore(name=f"recall@{k}", value=round(r_at_k, 4)),
            MetricScore(name="mrr", value=round(mrr, 4)),
        ],
        detail={
            "query": case.query,
            "retrieved": retrieved,
            "relevant": list(relevant),
        },
    )


def compute_search_metrics(
    test_cases: list[EvalTestCase],
    search_fn: Callable[[str, str, int], list[str]],
    workspace_id: str,
    k: int = 5,
) -> EvalSuite:
    """Evaluate search quality across all test cases.

    Args:
        test_cases: Labelled eval cases with query + relevant_slugs.
        search_fn:  Function (query, workspace_id, k) -> list[str slugs].
                    Must return results in ranked order.
        workspace_id: Workspace to query.
        k:          Rank cutoff for precision/recall.

    Returns:
        EvalSuite with per-case results and aggregate mean metrics.
    """
    results = [_run_case(case, search_fn, workspace_id, k) for case in test_cases]

    # Aggregate
    valid = [r for r in results if r.error is None]
    if valid:
        mean_p = sum(
            next((m.value for m in r.metrics if m.name == f"precision@{k}"), 0.0)
            for r in valid
        ) / len(valid)
        mean_r = sum(
            next((m.value for m in r.metrics if m.name == f"recall@{k}"), 0.0)
            for r in valid
        ) / len(valid)
        mean_mrr = sum(
            next((m.value for m in r.metrics if m.name == "mrr"), 0.0)
            for r in valid
        ) / len(valid)
    else:
        mean_p = mean_r = mean_mrr = 0.0

    return EvalSuite(
        eval_type="search",
        workspace_id=workspace_id,
        results=results,
        aggregate_metrics=[
            MetricScore(
                name=f"mean_precision@{k}",
                value=round(mean_p, 4),
                description=f"Mean precision at rank {k} across {len(valid)} valid cases",
            ),
            MetricScore(
                name=f"mean_recall@{k}",
                value=round(mean_r, 4),
                description=f"Mean recall at rank {k} across {len(valid)} valid cases",
            ),
            MetricScore(
                name="MRR",
                value=round(mean_mrr, 4),
                description="Mean Reciprocal Rank across valid cases",
            ),
        ],
    )
