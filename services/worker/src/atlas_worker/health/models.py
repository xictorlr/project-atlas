"""Shared data contracts for health check results.

HealthReport is the top-level output of both vault_health and source_health.
It is intentionally a plain dataclass so it can be serialised by the API layer
without importing any web framework here.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
from datetime import datetime, timezone


class IssueSeverity(StrEnum):
    ERROR = "error"      # blocks normal operation
    WARNING = "warning"  # degraded but functional
    INFO = "info"        # advisory


@dataclass(frozen=True)
class HealthIssue:
    """A single integrity issue found during a health check."""

    severity: IssueSeverity
    code: str           # machine-readable code, e.g. "broken_wikilink"
    message: str        # human-readable description
    path: str | None = None   # vault-relative path when applicable
    detail: dict | None = None  # extra structured context


@dataclass
class HealthReport:
    """Aggregated result of a health check run.

    Inputs:
      workspace_id: str
    Outputs:
      issues: list[HealthIssue]
      checked_at: ISO 8601 UTC timestamp string
      stats: dict with summary counts (e.g. notes_scanned, sources_checked)

    Failure states:
      - If the vault directory is missing, a single ERROR issue is appended and
        the report is returned (not raised).
    """

    workspace_id: str
    issues: list[HealthIssue] = field(default_factory=list)
    stats: dict = field(default_factory=dict)
    checked_at: str = field(
        default_factory=lambda: datetime.now(tz=timezone.utc).isoformat()
    )

    # ── Convenience properties ────────────────────────────────────────────────

    @property
    def error_count(self) -> int:
        return sum(1 for i in self.issues if i.severity == IssueSeverity.ERROR)

    @property
    def warning_count(self) -> int:
        return sum(1 for i in self.issues if i.severity == IssueSeverity.WARNING)

    @property
    def healthy(self) -> bool:
        """True when there are no ERROR-severity issues."""
        return self.error_count == 0

    def to_dict(self) -> dict:
        """Serialise to a plain dict suitable for JSON responses."""
        return {
            "workspace_id": self.workspace_id,
            "healthy": self.healthy,
            "error_count": self.error_count,
            "warning_count": self.warning_count,
            "checked_at": self.checked_at,
            "stats": self.stats,
            "issues": [
                {
                    "severity": i.severity,
                    "code": i.code,
                    "message": i.message,
                    "path": i.path,
                    "detail": i.detail,
                }
                for i in self.issues
            ],
        }
