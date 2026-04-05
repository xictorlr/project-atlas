"""Compiler output quality evaluator.

Inputs:
  test_cases: list[EvalTestCase] — each has note_path + expected_entities +
                                   expected_frontmatter_fields
  vault_root: Path               — root of vault directory
  workspace_id: str

Outputs:
  EvalSuite with per-case EvalResults containing:
    - frontmatter_completeness — fraction of expected fields present and non-null
    - entity_coverage          — fraction of expected entities found in note body
    - backlink_density         — number of [[wikilinks]] per 100 words of body

  Aggregate metrics:
    - mean_frontmatter_completeness
    - mean_entity_coverage
    - mean_backlink_density

Failure states:
  - note_path missing on disk: EvalResult.error set, passed=False.
  - Malformed frontmatter YAML: frontmatter_completeness = 0.
  - Empty note body: entity_coverage = 0, backlink_density = 0.

Design:
  - Pure read; no file writes.
  - Reuses frontmatter parsing identical to indexer.py to stay consistent.
"""

from __future__ import annotations

import logging
import re
from pathlib import Path

import yaml

from atlas_api.evals.models import EvalResult, EvalSuite, EvalTestCase, MetricScore

logger = logging.getLogger(__name__)

_FM_DELIMITER = re.compile(r"^---\s*$", re.MULTILINE)
_WIKILINK_RE = re.compile(r"\[\[([^\]|#\n]+?)(?:\|[^\]]*?)?\]\]")


def _parse_frontmatter(content: str) -> tuple[dict, str]:
    parts = _FM_DELIMITER.split(content, maxsplit=2)
    if len(parts) >= 3:
        try:
            fm = yaml.safe_load(parts[1]) or {}
            return fm, parts[2].strip()
        except yaml.YAMLError:
            return {}, content
    return {}, content


def _word_count(text: str) -> int:
    return len(text.split())


def _wikilink_count(text: str) -> int:
    return len(_WIKILINK_RE.findall(text))


def _frontmatter_completeness(fm: dict, expected_fields: list[str]) -> float:
    if not expected_fields:
        return 1.0
    present = sum(1 for f in expected_fields if fm.get(f) not in (None, "", []))
    return present / len(expected_fields)


def _entity_coverage(body: str, expected_entities: list[str]) -> float:
    if not expected_entities:
        return 1.0
    body_lower = body.lower()
    found = sum(1 for ent in expected_entities if ent.lower() in body_lower)
    return found / len(expected_entities)


def _run_case(case: EvalTestCase, vault_root: Path) -> EvalResult:
    if not case.note_path:
        return EvalResult(
            test_case_id=case.id,
            eval_type="compiler",
            passed=False,
            error="test case has no note_path field",
        )

    note_file = vault_root / case.note_path
    if not note_file.exists():
        return EvalResult(
            test_case_id=case.id,
            eval_type="compiler",
            passed=False,
            error=f"note not found on disk: {case.note_path}",
        )

    try:
        content = note_file.read_text(encoding="utf-8")
    except OSError as exc:
        return EvalResult(
            test_case_id=case.id,
            eval_type="compiler",
            passed=False,
            error=f"could not read note: {exc}",
        )

    fm, body = _parse_frontmatter(content)

    fm_score = _frontmatter_completeness(fm, case.expected_frontmatter_fields)
    ent_score = _entity_coverage(body, case.expected_entities)

    words = _word_count(body)
    links = _wikilink_count(body)
    density = (links / words * 100) if words > 0 else 0.0

    # Pass: both completeness and entity coverage >= 0.5
    passed = fm_score >= 0.5 and ent_score >= 0.5

    return EvalResult(
        test_case_id=case.id,
        eval_type="compiler",
        passed=passed,
        metrics=[
            MetricScore(
                name="frontmatter_completeness",
                value=round(fm_score, 4),
                description="Fraction of expected frontmatter fields present and non-null",
            ),
            MetricScore(
                name="entity_coverage",
                value=round(ent_score, 4),
                description="Fraction of expected entities mentioned in note body",
            ),
            MetricScore(
                name="backlink_density",
                value=round(density, 4),
                description="Wikilinks per 100 words of body text",
            ),
        ],
        detail={
            "note_path": case.note_path,
            "word_count": words,
            "wikilink_count": links,
            "expected_entities_found": [
                e for e in case.expected_entities if e.lower() in body.lower()
            ],
        },
    )


def compute_compiler_metrics(
    test_cases: list[EvalTestCase],
    vault_root: Path,
    workspace_id: str,
) -> EvalSuite:
    """Evaluate compiler output quality across all test cases.

    Args:
        test_cases: Labelled eval cases with note_path + expected fields.
        vault_root: Root vault directory (note_path is resolved relative to this).
        workspace_id: Workspace being evaluated.

    Returns:
        EvalSuite with per-case results and aggregate mean metrics.
    """
    results = [_run_case(case, vault_root) for case in test_cases]

    valid = [r for r in results if r.error is None]
    if valid:
        def _agg(name: str) -> float:
            values = [
                next((m.value for m in r.metrics if m.name == name), 0.0)
                for r in valid
            ]
            return sum(values) / len(values)

        mean_fm = _agg("frontmatter_completeness")
        mean_ent = _agg("entity_coverage")
        mean_density = _agg("backlink_density")
    else:
        mean_fm = mean_ent = mean_density = 0.0

    return EvalSuite(
        eval_type="compiler",
        workspace_id=workspace_id,
        results=results,
        aggregate_metrics=[
            MetricScore(
                name="mean_frontmatter_completeness",
                value=round(mean_fm, 4),
                description=f"Mean frontmatter completeness across {len(valid)} valid cases",
            ),
            MetricScore(
                name="mean_entity_coverage",
                value=round(mean_ent, 4),
                description=f"Mean entity coverage across {len(valid)} valid cases",
            ),
            MetricScore(
                name="mean_backlink_density",
                value=round(mean_density, 4),
                description="Mean wikilinks per 100 words across valid cases",
            ),
        ],
    )
