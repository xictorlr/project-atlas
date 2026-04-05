"""Pydantic models for the eval framework.

EvalTestCase  — a single labelled test input
MetricScore   — one named metric value with optional metadata
EvalResult    — result of running one test case through an eval
EvalSuite     — aggregated result of running a full suite
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from pydantic import BaseModel, Field


class EvalTestCase(BaseModel):
    """A single labelled input for an eval run."""

    id: str
    description: str | None = None

    # Search eval fields
    query: str | None = None
    relevant_slugs: list[str] = Field(default_factory=list)

    # Compiler eval fields
    note_path: str | None = None
    expected_entities: list[str] = Field(default_factory=list)
    expected_frontmatter_fields: list[str] = Field(default_factory=list)


class MetricScore(BaseModel):
    """A single named metric value."""

    name: str
    value: float
    description: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class EvalResult(BaseModel):
    """Result of running one EvalTestCase through an evaluator."""

    test_case_id: str
    eval_type: str
    passed: bool
    metrics: list[MetricScore] = Field(default_factory=list)
    detail: dict[str, Any] = Field(default_factory=dict)
    error: str | None = None

    def primary_score(self) -> float | None:
        """Return the value of the first metric, if any."""
        return self.metrics[0].value if self.metrics else None


class EvalSuite(BaseModel):
    """Aggregated result of running all test cases in an eval suite."""

    eval_type: str
    workspace_id: str
    run_at: str = Field(
        default_factory=lambda: datetime.now(tz=timezone.utc).isoformat()
    )
    results: list[EvalResult] = Field(default_factory=list)
    aggregate_metrics: list[MetricScore] = Field(default_factory=list)

    @property
    def total_cases(self) -> int:
        return len(self.results)

    @property
    def passed_cases(self) -> int:
        return sum(1 for r in self.results if r.passed)

    @property
    def pass_rate(self) -> float:
        if not self.results:
            return 0.0
        return self.passed_cases / self.total_cases
