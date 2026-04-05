"""Health check package for atlas-worker.

Exports:
  vault_health.check_vault    — vault integrity scan (broken links, missing
                                 frontmatter, orphans, duplicates, stale notes,
                                 empty notes).
  source_health.check_sources — source record integrity scan.
  models.HealthReport          — shared result contract.
"""

from atlas_worker.health.models import HealthReport, HealthIssue, IssueSeverity
from atlas_worker.health.vault_health import check_vault
from atlas_worker.health.source_health import check_sources

__all__ = [
    "HealthReport",
    "HealthIssue",
    "IssueSeverity",
    "check_vault",
    "check_sources",
]
