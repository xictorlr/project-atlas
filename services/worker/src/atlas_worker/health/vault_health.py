"""Vault integrity checker.

Inputs:
  workspace_vault_dir: Path — absolute path to vault/{workspace_id}/
  stale_days: int           — notes not updated in this many days are stale (default 30)

Outputs:
  HealthReport with issues for:
    - broken_wikilink       (ERROR)   — [[target]] resolves to no file
    - missing_frontmatter   (ERROR)   — required field absent or null
    - empty_note            (WARNING) — body is blank after frontmatter
    - stale_note            (WARNING) — updated field > stale_days ago
    - orphan_note           (WARNING) — note has no backlinks pointing to it
    - duplicate_slug        (ERROR)   — two files share the same slug value

Failure states:
  - vault dir missing: single ERROR, early return
  - unreadable file: WARNING per file, skip
  - malformed frontmatter YAML: WARNING per file, required fields treated missing

Design:
  - Pure read; never modifies files.
  - Reuses _extract_wikilinks and parse_frontmatter from existing modules.
"""

from __future__ import annotations

import logging
import re
from collections import defaultdict
from datetime import datetime, timezone, timedelta
from pathlib import Path

import yaml

from atlas_worker.health.models import HealthIssue, HealthReport, IssueSeverity

logger = logging.getLogger(__name__)

# Required frontmatter fields common to ALL note types.
_COMMON_REQUIRED = frozenset(
    {"title", "slug", "type", "created", "updated", "workspace_id", "tags"}
)

# Additional required fields per note type.
_TYPE_REQUIRED: dict[str, frozenset[str]] = {
    "source": frozenset({"source_id"}),
    "entity": frozenset({"entity_kind"}),
    "concept": frozenset(),
    "index": frozenset({"index_kind", "generated_at", "generated_by", "entry_count"}),
    "timeline": frozenset(
        {"timeline_kind", "subject_slug", "generated_at", "generated_by"}
    ),
    "meta": frozenset(),
}

_WIKILINK_RE = re.compile(r"\[\[([^\]|#\n]+?)(?:\|[^\]]*?)?\]\]")
_FM_DELIMITER = re.compile(r"^---\s*$", re.MULTILINE)


# ── Internal helpers ──────────────────────────────────────────────────────────


def _parse_frontmatter(content: str) -> tuple[dict, str]:
    parts = _FM_DELIMITER.split(content, maxsplit=2)
    if len(parts) >= 3:
        try:
            fm = yaml.safe_load(parts[1]) or {}
            return fm, parts[2].strip()
        except yaml.YAMLError:
            return {}, content
    return {}, content


def _extract_wikilinks(text: str) -> list[str]:
    return [m.group(1).strip() for m in _WIKILINK_RE.finditer(text)]


def _resolve_link(raw: str, vault_dir: Path) -> Path:
    target = raw.strip()
    if not target.endswith(".md"):
        target += ".md"
    return vault_dir / target


# ── Public entry point ────────────────────────────────────────────────────────


def check_vault(
    workspace_vault_dir: Path,
    stale_days: int = 30,
) -> HealthReport:
    """Run all vault integrity checks and return a HealthReport.

    Args:
        workspace_vault_dir: Absolute path to vault/{workspace_id}/
        stale_days: Notes whose `updated` field is older than this are stale.

    Returns:
        HealthReport populated with issues and summary stats.
    """
    workspace_id = workspace_vault_dir.name
    report = HealthReport(workspace_id=workspace_id)

    if not workspace_vault_dir.exists():
        report.issues.append(
            HealthIssue(
                severity=IssueSeverity.ERROR,
                code="vault_dir_missing",
                message=f"Vault directory not found: {workspace_vault_dir}",
            )
        )
        return report

    md_files = sorted(workspace_vault_dir.rglob("*.md"))
    stale_threshold = datetime.now(tz=timezone.utc) - timedelta(days=stale_days)

    # Track slug -> [paths] for duplicate detection
    slug_to_paths: dict[str, list[str]] = defaultdict(list)
    # Track which slugs are referenced by wikilinks (for orphan detection)
    referenced_slugs: set[str] = set()
    # Per-note slugs collected during first pass
    note_slugs: dict[str, str] = {}  # vault_relative_path -> slug

    notes_scanned = 0
    broken_links = 0
    missing_fields = 0
    empty_notes = 0
    stale_notes = 0

    for note_path in md_files:
        rel = str(note_path.relative_to(workspace_vault_dir))

        try:
            content = note_path.read_text(encoding="utf-8")
        except OSError as exc:
            report.issues.append(
                HealthIssue(
                    severity=IssueSeverity.WARNING,
                    code="unreadable_file",
                    message=f"Could not read file: {exc}",
                    path=rel,
                )
            )
            continue

        notes_scanned += 1
        fm, body = _parse_frontmatter(content)

        # ── Slug tracking ──────────────────────────────────────────────────
        slug: str = fm.get("slug") or note_path.stem
        note_slugs[rel] = slug
        slug_to_paths[slug].append(rel)

        # ── Missing frontmatter fields ─────────────────────────────────────
        note_type: str = str(fm.get("type", "unknown"))
        extra_required = _TYPE_REQUIRED.get(note_type, frozenset())
        all_required = _COMMON_REQUIRED | extra_required

        for field_name in sorted(all_required):
            if not fm.get(field_name):
                report.issues.append(
                    HealthIssue(
                        severity=IssueSeverity.ERROR,
                        code="missing_frontmatter",
                        message=f"Required frontmatter field '{field_name}' is absent or null",
                        path=rel,
                        detail={"field": field_name, "note_type": note_type},
                    )
                )
                missing_fields += 1

        # ── Empty note ─────────────────────────────────────────────────────
        if not body.strip():
            report.issues.append(
                HealthIssue(
                    severity=IssueSeverity.WARNING,
                    code="empty_note",
                    message="Note body is empty after frontmatter",
                    path=rel,
                )
            )
            empty_notes += 1

        # ── Stale note ─────────────────────────────────────────────────────
        updated_raw = fm.get("updated")
        if updated_raw:
            try:
                updated_dt = datetime.fromisoformat(str(updated_raw).replace("Z", "+00:00"))
                if updated_dt < stale_threshold:
                    report.issues.append(
                        HealthIssue(
                            severity=IssueSeverity.WARNING,
                            code="stale_note",
                            message=(
                                f"Note has not been updated in {stale_days}+ days "
                                f"(last updated: {updated_raw})"
                            ),
                            path=rel,
                            detail={"updated": str(updated_raw)},
                        )
                    )
                    stale_notes += 1
            except (ValueError, TypeError):
                pass  # malformed date — already caught by missing_frontmatter

        # ── Broken wikilinks ───────────────────────────────────────────────
        combined_text = content
        for raw_target in _extract_wikilinks(combined_text):
            referenced_slugs.add(raw_target.split("/")[-1])  # track slug portion
            resolved = _resolve_link(raw_target, workspace_vault_dir)
            if not resolved.exists():
                report.issues.append(
                    HealthIssue(
                        severity=IssueSeverity.ERROR,
                        code="broken_wikilink",
                        message=f"Wikilink [[{raw_target}]] target not found",
                        path=rel,
                        detail={"target": raw_target, "resolved": str(resolved)},
                    )
                )
                broken_links += 1

    # ── Duplicate slugs (post-scan) ────────────────────────────────────────
    duplicate_slugs = 0
    for slug, paths in slug_to_paths.items():
        if len(paths) > 1:
            report.issues.append(
                HealthIssue(
                    severity=IssueSeverity.ERROR,
                    code="duplicate_slug",
                    message=f"Slug '{slug}' is used by {len(paths)} notes",
                    detail={"slug": slug, "paths": paths},
                )
            )
            duplicate_slugs += 1

    # ── Orphan notes (post-scan) ───────────────────────────────────────────
    orphan_count = 0
    for rel, slug in note_slugs.items():
        # Skip index/meta notes — they are intentionally standalone
        note_fm_type = ""
        for path in md_files:
            if str(path.relative_to(workspace_vault_dir)) == rel:
                try:
                    content = path.read_text(encoding="utf-8")
                    fm, _ = _parse_frontmatter(content)
                    note_fm_type = str(fm.get("type", ""))
                except OSError:
                    pass
                break

        if note_fm_type in ("index", "meta"):
            continue

        if slug not in referenced_slugs:
            report.issues.append(
                HealthIssue(
                    severity=IssueSeverity.WARNING,
                    code="orphan_note",
                    message="Note has no incoming wikilinks",
                    path=rel,
                    detail={"slug": slug},
                )
            )
            orphan_count += 1

    report.stats = {
        "notes_scanned": notes_scanned,
        "broken_links": broken_links,
        "missing_frontmatter_fields": missing_fields,
        "empty_notes": empty_notes,
        "stale_notes": stale_notes,
        "duplicate_slugs": duplicate_slugs,
        "orphan_notes": orphan_count,
    }

    logger.info(
        "vault health check complete for %s: %d notes, %d errors, %d warnings",
        workspace_id,
        notes_scanned,
        report.error_count,
        report.warning_count,
    )
    return report
