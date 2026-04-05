"""Unit tests and sample eval suite for search quality metrics.

Tests:
  - precision@k, recall@k, MRR arithmetic
  - EvalSuite aggregation
  - Error handling when search_fn raises

Sample eval suite:
  5 labelled test cases derived from the vault fixtures in tests/fixtures/vault/.
  Expected slugs match the fixture notes: research-methodologies,
  knowledge-compilation, semantic-search.
"""

from __future__ import annotations

import pytest

from atlas_api.evals.models import EvalTestCase
from atlas_api.evals.search_eval import (
    _precision_at_k,
    _recall_at_k,
    _reciprocal_rank,
    compute_search_metrics,
)


# ── Metric unit tests ─────────────────────────────────────────────────────────


class TestPrecisionAtK:
    def test_all_relevant(self) -> None:
        assert _precision_at_k(["a", "b", "c"], {"a", "b", "c"}, k=3) == 1.0

    def test_none_relevant(self) -> None:
        assert _precision_at_k(["x", "y"], {"a", "b"}, k=2) == 0.0

    def test_partial_overlap(self) -> None:
        result = _precision_at_k(["a", "x", "b"], {"a", "b"}, k=3)
        assert abs(result - 2 / 3) < 1e-9

    def test_k_less_than_retrieved(self) -> None:
        # Only top-2 considered
        result = _precision_at_k(["a", "b", "c"], {"c"}, k=2)
        assert result == 0.0

    def test_empty_retrieved(self) -> None:
        assert _precision_at_k([], {"a"}, k=5) == 0.0


class TestRecallAtK:
    def test_all_found(self) -> None:
        assert _recall_at_k(["a", "b"], {"a", "b"}, k=5) == 1.0

    def test_none_found(self) -> None:
        assert _recall_at_k(["x", "y"], {"a", "b"}, k=5) == 0.0

    def test_partial(self) -> None:
        result = _recall_at_k(["a", "x", "b"], {"a", "b", "c"}, k=3)
        assert abs(result - 2 / 3) < 1e-9

    def test_empty_relevant_returns_one(self) -> None:
        assert _recall_at_k(["a", "b"], set(), k=5) == 1.0


class TestReciprocalRank:
    def test_first_result_relevant(self) -> None:
        assert _reciprocal_rank(["a", "b", "c"], {"a"}) == 1.0

    def test_second_result_relevant(self) -> None:
        assert _reciprocal_rank(["x", "a", "b"], {"a"}) == 0.5

    def test_no_relevant_result(self) -> None:
        assert _reciprocal_rank(["x", "y"], {"a"}) == 0.0

    def test_empty_retrieved(self) -> None:
        assert _reciprocal_rank([], {"a"}) == 0.0


# ── compute_search_metrics integration ───────────────────────────────────────


def _perfect_search_fn(query: str, workspace_id: str, k: int) -> list[str]:
    """Returns the first relevant slug from the test case as top result."""
    return ["research-methodologies", "semantic-search", "knowledge-compilation"][:k]


def _empty_search_fn(query: str, workspace_id: str, k: int) -> list[str]:
    return []


def _raising_search_fn(query: str, workspace_id: str, k: int) -> list[str]:
    raise RuntimeError("search unavailable")


SAMPLE_EVAL_SUITE = [
    EvalTestCase(
        id="tc-001",
        description="Query about AI research methods",
        query="research methodology artificial intelligence",
        relevant_slugs=["research-methodologies"],
    ),
    EvalTestCase(
        id="tc-002",
        description="Query about knowledge indexing",
        query="knowledge compilation indexing",
        relevant_slugs=["knowledge-compilation"],
    ),
    EvalTestCase(
        id="tc-003",
        description="Query about semantic search",
        query="semantic search vector embeddings",
        relevant_slugs=["semantic-search"],
    ),
    EvalTestCase(
        id="tc-004",
        description="Multi-relevant query",
        query="search retrieval ranking",
        relevant_slugs=["semantic-search", "research-methodologies"],
    ),
    EvalTestCase(
        id="tc-005",
        description="Query with no relevant expected notes",
        query="billing invoices payment",
        relevant_slugs=[],
    ),
]


class TestComputeSearchMetrics:
    def test_perfect_search_gives_high_scores(self) -> None:
        suite = compute_search_metrics(
            SAMPLE_EVAL_SUITE, _perfect_search_fn, workspace_id="ws_test", k=3
        )
        assert suite.total_cases == 5
        assert suite.pass_rate > 0.5

        mrr = next(m for m in suite.aggregate_metrics if m.name == "MRR")
        assert mrr.value > 0.0

    def test_empty_search_gives_zero_mrr(self) -> None:
        suite = compute_search_metrics(
            SAMPLE_EVAL_SUITE, _empty_search_fn, workspace_id="ws_test", k=3
        )
        mrr = next(m for m in suite.aggregate_metrics if m.name == "MRR")
        assert mrr.value == 0.0

    def test_raising_search_fn_captured_as_error(self) -> None:
        suite = compute_search_metrics(
            [SAMPLE_EVAL_SUITE[0]], _raising_search_fn, workspace_id="ws_test", k=3
        )
        assert suite.results[0].passed is False
        assert suite.results[0].error is not None

    def test_aggregate_metrics_present(self) -> None:
        suite = compute_search_metrics(
            SAMPLE_EVAL_SUITE, _perfect_search_fn, workspace_id="ws_test", k=5
        )
        metric_names = {m.name for m in suite.aggregate_metrics}
        assert "mean_precision@5" in metric_names
        assert "mean_recall@5" in metric_names
        assert "MRR" in metric_names

    def test_suite_eval_type(self) -> None:
        suite = compute_search_metrics([], _empty_search_fn, workspace_id="ws_test")
        assert suite.eval_type == "search"

    def test_empty_test_cases_returns_zero_metrics(self) -> None:
        suite = compute_search_metrics([], _empty_search_fn, workspace_id="ws_test")
        for m in suite.aggregate_metrics:
            assert m.value == 0.0
