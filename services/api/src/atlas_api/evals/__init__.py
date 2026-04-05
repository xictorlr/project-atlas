"""Eval framework for Atlas search and compiler quality.

Exports:
  models          — EvalResult, EvalSuite, MetricScore Pydantic models
  search_eval     — compute_search_metrics (precision@k, recall@k, MRR)
  compiler_eval   — compute_compiler_metrics (frontmatter completeness,
                    entity coverage, backlink density)
"""

from atlas_api.evals.models import EvalResult, EvalSuite, MetricScore, EvalTestCase
from atlas_api.evals.search_eval import compute_search_metrics
from atlas_api.evals.compiler_eval import compute_compiler_metrics

__all__ = [
    "EvalResult",
    "EvalSuite",
    "MetricScore",
    "EvalTestCase",
    "compute_search_metrics",
    "compute_compiler_metrics",
]
