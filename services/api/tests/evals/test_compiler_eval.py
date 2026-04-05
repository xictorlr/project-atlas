"""Unit tests for the compiler quality evaluator.

Tests frontmatter completeness, entity coverage, and backlink density
using the vault fixtures from tests/fixtures/vault/.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from atlas_api.evals.compiler_eval import (
    _entity_coverage,
    _frontmatter_completeness,
    _wikilink_count,
    _word_count,
    compute_compiler_metrics,
)
from atlas_api.evals.models import EvalTestCase


# ── Unit tests for helper functions ──────────────────────────────────────────


class TestFrontmatterCompleteness:
    def test_all_fields_present(self) -> None:
        fm = {"title": "T", "slug": "s", "type": "concept"}
        assert _frontmatter_completeness(fm, ["title", "slug", "type"]) == 1.0

    def test_one_missing(self) -> None:
        fm = {"title": "T", "slug": "s"}
        result = _frontmatter_completeness(fm, ["title", "slug", "type"])
        assert abs(result - 2 / 3) < 1e-9

    def test_empty_expected_returns_one(self) -> None:
        assert _frontmatter_completeness({}, []) == 1.0

    def test_null_value_counts_as_missing(self) -> None:
        fm = {"title": None}
        assert _frontmatter_completeness(fm, ["title"]) == 0.0


class TestEntityCoverage:
    def test_all_found(self) -> None:
        body = "This mentions Alice and BobCorp in the text."
        assert _entity_coverage(body, ["Alice", "BobCorp"]) == 1.0

    def test_none_found(self) -> None:
        body = "Nothing relevant here."
        assert _entity_coverage(body, ["XYZ Corp", "Unknown Entity"]) == 0.0

    def test_partial(self) -> None:
        body = "Alice is mentioned here but not Carol."
        result = _entity_coverage(body, ["Alice", "Carol", "Eve"])
        # "Alice" is present, "Carol" is NOT (substring "carol" not in body), "Eve" absent
        # body has "not carol" — wait, body has "not Carol" -> lower: "not carol" contains "carol"
        # Use a body with only one clear match
        body2 = "Only Dave is present."
        result2 = _entity_coverage(body2, ["Dave", "Eve", "Frank"])
        assert abs(result2 - 1 / 3) < 1e-9

    def test_empty_expected_returns_one(self) -> None:
        assert _entity_coverage("some text", []) == 1.0

    def test_case_insensitive(self) -> None:
        assert _entity_coverage("alice and bob", ["Alice", "BOB"]) == 1.0


class TestWikilinkCount:
    def test_counts_wikilinks(self) -> None:
        text = "See [[note-one]] and [[note-two]] for details."
        assert _wikilink_count(text) == 2

    def test_no_wikilinks(self) -> None:
        assert _wikilink_count("plain text") == 0

    def test_wikilink_with_alias(self) -> None:
        assert _wikilink_count("[[note|Display Text]]") == 1


class TestWordCount:
    def test_basic(self) -> None:
        assert _word_count("one two three") == 3

    def test_empty(self) -> None:
        assert _word_count("") == 0


# ── compute_compiler_metrics integration tests ────────────────────────────────


@pytest.fixture
def vault_fixture_dir() -> Path:
    return Path(__file__).parent.parent / "fixtures" / "vault"


class TestComputeCompilerMetrics:
    def test_existing_note_scores(self, vault_fixture_dir: Path) -> None:
        cases = [
            EvalTestCase(
                id="tc-c-001",
                description="Evaluate research-methodologies note",
                note_path="research-methodologies.md",
                expected_entities=["AI Systems", "experimental design"],
                expected_frontmatter_fields=["title", "slug", "type"],
            )
        ]
        suite = compute_compiler_metrics(cases, vault_fixture_dir, workspace_id="ws_test")

        assert suite.total_cases == 1
        result = suite.results[0]
        assert result.error is None

        fm_score = next(m for m in result.metrics if m.name == "frontmatter_completeness")
        # fixture uses 'id' not 'slug'; title and type are present -> 2/3
        assert fm_score.value >= 0.6

        ent_score = next(m for m in result.metrics if m.name == "entity_coverage")
        assert ent_score.value > 0.0  # at least one entity found (case-insensitive)

    def test_missing_note_path_returns_error(self, vault_fixture_dir: Path) -> None:
        cases = [
            EvalTestCase(
                id="tc-c-002",
                note_path="does-not-exist.md",
                expected_entities=[],
                expected_frontmatter_fields=[],
            )
        ]
        suite = compute_compiler_metrics(cases, vault_fixture_dir, workspace_id="ws_test")
        assert suite.results[0].passed is False
        assert suite.results[0].error is not None

    def test_no_note_path_field_returns_error(self, vault_fixture_dir: Path) -> None:
        cases = [EvalTestCase(id="tc-c-003")]
        suite = compute_compiler_metrics(cases, vault_fixture_dir, workspace_id="ws_test")
        assert suite.results[0].error is not None

    def test_aggregate_metrics_present(self, vault_fixture_dir: Path) -> None:
        cases = [
            EvalTestCase(
                id="tc-c-004",
                note_path="semantic-search.md",
                expected_entities=["Semantic Search"],
                expected_frontmatter_fields=["title", "type"],
            )
        ]
        suite = compute_compiler_metrics(cases, vault_fixture_dir, workspace_id="ws_test")
        metric_names = {m.name for m in suite.aggregate_metrics}
        assert "mean_frontmatter_completeness" in metric_names
        assert "mean_entity_coverage" in metric_names
        assert "mean_backlink_density" in metric_names

    def test_semantic_search_note_has_wikilinks(self, vault_fixture_dir: Path) -> None:
        cases = [
            EvalTestCase(
                id="tc-c-005",
                note_path="semantic-search.md",
                expected_entities=[],
                expected_frontmatter_fields=[],
            )
        ]
        suite = compute_compiler_metrics(cases, vault_fixture_dir, workspace_id="ws_test")
        result = suite.results[0]
        density = next(m for m in result.metrics if m.name == "backlink_density")
        assert density.value > 0.0  # semantic-search.md has [[...]] links
