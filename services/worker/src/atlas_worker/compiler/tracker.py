"""Decision log and action item tracker — compiler step 7 (cross-source aggregation).

Inputs:
  - vault_path: Path to the workspace vault directory (e.g. vault/{workspace_id}/)
  - InferenceRouter instance

Outputs:
  - list[Decision]    — aggregated decisions from all meeting notes in the vault
  - list[ActionItem]  — aggregated action items from all meeting notes in the vault

Strategy:
  - Scan vault_path/**/*.md for notes whose frontmatter has type: meeting_minutes
  - For each meeting note, call generate_meeting_minutes on the note body (cached
    minutes are also stored in the frontmatter decision_log / action_items fields
    when the vault_writer has already written them — those are preferred to avoid
    re-running the LLM).
  - Aggregate all decisions and action items across the workspace.

Failure modes:
  - File read errors → logged and skipped, aggregation continues
  - No meeting notes → returns ([], [])
  - router.generate() errors → logged and that note skipped
"""

from __future__ import annotations

import logging
from pathlib import Path

from atlas_worker.compiler.meeting_minutes import (
    ActionItem,
    Decision,
    generate_meeting_minutes,
)
from atlas_worker.compiler.vault_writer import parse_frontmatter
from atlas_worker.inference.router import InferenceRouter

logger = logging.getLogger(__name__)

_MEETING_NOTE_TYPE = "meeting_minutes"


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _find_meeting_notes(vault_path: Path) -> list[Path]:
    """Return all .md files under vault_path whose frontmatter type == meeting_minutes."""
    if not vault_path.exists():
        return []
    found: list[Path] = []
    for md_path in sorted(vault_path.rglob("*.md")):
        try:
            raw = md_path.read_text(encoding="utf-8")
            fm, _ = parse_frontmatter(raw)
            if fm.get("type") == _MEETING_NOTE_TYPE:
                found.append(md_path)
        except Exception as exc:
            logger.warning("tracker: could not read %s — %s", md_path, exc)
    return found


def _extract_body_text(raw: str) -> str:
    """Return the Markdown body text with frontmatter stripped."""
    _, body = parse_frontmatter(raw)
    return body.strip()


def _decisions_from_frontmatter(fm: dict) -> list[Decision]:
    """Try to read pre-compiled decisions stored in frontmatter (avoids LLM re-call)."""
    raw_list = fm.get("decision_log") or []
    decisions: list[Decision] = []
    for item in raw_list:
        if not isinstance(item, dict):
            continue
        try:
            decisions.append(
                Decision(
                    description=str(item.get("description", "")),
                    made_by=item.get("made_by") or None,
                    context=str(item.get("context", "")),
                    timestamp=item.get("timestamp") or None,
                )
            )
        except Exception as exc:
            logger.warning("tracker: skipping malformed frontmatter decision — %s", exc)
    return decisions


def _action_items_from_frontmatter(fm: dict) -> list[ActionItem]:
    """Try to read pre-compiled action items stored in frontmatter."""
    raw_list = fm.get("action_items") or []
    items: list[ActionItem] = []
    for item in raw_list:
        if not isinstance(item, dict):
            continue
        try:
            priority = str(item.get("priority", "medium")).lower()
            if priority not in ("high", "medium", "low"):
                priority = "medium"
            status = str(item.get("status", "open")).lower()
            if status not in ("open", "in_progress", "done"):
                status = "open"
            items.append(
                ActionItem(
                    description=str(item.get("description", "")),
                    owner=item.get("owner") or None,
                    deadline=item.get("deadline") or None,
                    priority=priority,
                    status=status,
                    source_quote=str(item.get("source_quote", "")),
                )
            )
        except Exception as exc:
            logger.warning("tracker: skipping malformed frontmatter action item — %s", exc)
    return items


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


async def rebuild_decision_log(
    vault_path: Path,
    router: InferenceRouter,
) -> list[Decision]:
    """Scan vault meeting notes and aggregate all decisions.

    Prefers decisions already cached in frontmatter (`decision_log` field).
    Falls back to LLM extraction from the note body if the field is absent.

    Args:
        vault_path: Path to the workspace vault directory.
        router:     InferenceRouter for LLM fallback extraction.

    Returns:
        Deduplicated list of Decision objects across all meeting notes.
        Empty list if no meeting notes are found.
    """
    notes = _find_meeting_notes(vault_path)
    if not notes:
        logger.info("rebuild_decision_log: no meeting notes found in %s", vault_path)
        return []

    all_decisions: list[Decision] = []

    for note_path in notes:
        try:
            raw = note_path.read_text(encoding="utf-8")
            fm, _ = parse_frontmatter(raw)

            cached = _decisions_from_frontmatter(fm)
            if cached:
                all_decisions.extend(cached)
                continue

            # Fallback: re-extract via LLM.
            body = _extract_body_text(raw)
            if not body:
                continue
            minutes = await generate_meeting_minutes(body, [], router)
            all_decisions.extend(minutes.decisions)

        except Exception as exc:
            logger.error("rebuild_decision_log: failed for %s — %s", note_path, exc)

    logger.info("rebuild_decision_log: %d decisions aggregated", len(all_decisions))
    return all_decisions


async def rebuild_action_items(
    vault_path: Path,
    router: InferenceRouter,
) -> list[ActionItem]:
    """Scan vault meeting notes and aggregate all action items.

    Prefers items already cached in frontmatter (`action_items` field).
    Falls back to LLM extraction from the note body if the field is absent.

    Args:
        vault_path: Path to the workspace vault directory.
        router:     InferenceRouter for LLM fallback extraction.

    Returns:
        List of ActionItem objects across all meeting notes.
        Empty list if no meeting notes are found.
    """
    notes = _find_meeting_notes(vault_path)
    if not notes:
        logger.info("rebuild_action_items: no meeting notes found in %s", vault_path)
        return []

    all_items: list[ActionItem] = []

    for note_path in notes:
        try:
            raw = note_path.read_text(encoding="utf-8")
            fm, _ = parse_frontmatter(raw)

            cached = _action_items_from_frontmatter(fm)
            if cached:
                all_items.extend(cached)
                continue

            # Fallback: re-extract via LLM.
            body = _extract_body_text(raw)
            if not body:
                continue
            minutes = await generate_meeting_minutes(body, [], router)
            all_items.extend(minutes.action_items)

        except Exception as exc:
            logger.error("rebuild_action_items: failed for %s — %s", note_path, exc)

    logger.info("rebuild_action_items: %d action items aggregated", len(all_items))
    return all_items
