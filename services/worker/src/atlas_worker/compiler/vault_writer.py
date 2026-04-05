"""Safe Markdown file writer for vault notes.

Handles directory creation, idempotent updates, and conflict detection.
Never destroys user edits — a conflict is recorded as a review task instead.
"""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass
from pathlib import Path
from typing import NamedTuple

import yaml

logger = logging.getLogger(__name__)

_FRONTMATTER_RE = re.compile(
    r"^---\r?\n(.*?)\r?\n---\r?\n",
    re.DOTALL,
)

# Marker added to generated sections so idempotent re-runs can replace them.
_GENERATED_SECTION_START = "<!-- atlas:generated -->"
_GENERATED_SECTION_END = "<!-- /atlas:generated -->"


class ConflictRecord(NamedTuple):
    path: Path
    reason: str
    existing_hash: str
    incoming_hash: str


@dataclass(frozen=True)
class WriteResult:
    path: Path
    action: str  # "created" | "updated" | "skipped" | "conflict"
    conflict: ConflictRecord | None = None


def _content_hash(text: str) -> str:
    """SHA-256 of UTF-8 text, prefixed sha256:."""
    import hashlib

    digest = hashlib.sha256(text.encode("utf-8")).hexdigest()
    return f"sha256:{digest}"


def parse_frontmatter(raw: str) -> tuple[dict, str]:
    """Split raw Markdown content into (frontmatter_dict, body).

    Returns empty dict and the full raw string if no frontmatter found.
    """
    match = _FRONTMATTER_RE.match(raw)
    if not match:
        return {}, raw
    fm = yaml.safe_load(match.group(1)) or {}
    body = raw[match.end():]
    return fm, body


def render_frontmatter(fm: dict) -> str:
    """Render a dict to a YAML frontmatter block."""
    return f"---\n{yaml.dump(fm, allow_unicode=True, sort_keys=False)}---\n\n"


def write_note(
    path: Path,
    frontmatter: dict,
    body: str,
    *,
    generated_section: str | None = None,
) -> WriteResult:
    """Write or update a vault note.

    - Creates directories as needed.
    - On create: writes frontmatter + body (+ generated_section if given).
    - On update: preserves `created` field, updates `updated` field,
      replaces the generated section if present, leaves user-authored body
      content outside the generated block untouched.
    - If a generated section is not found in an existing file and body
      content differs, records a ConflictRecord instead of overwriting.

    Args:
        path:              Absolute path to the target .md file.
        frontmatter:       Frontmatter dict. `created` is preserved from
                           the existing file if it exists.
        body:              Markdown body text (outside any generated block).
        generated_section: Optional compiler-authored section that replaces
                           the <!-- atlas:generated -->…<!-- /atlas:generated -->
                           block.

    Returns:
        WriteResult describing what happened.
    """
    path.parent.mkdir(parents=True, exist_ok=True)

    full_body = _assemble_body(body, generated_section)
    incoming_text = render_frontmatter(frontmatter) + full_body

    if not path.exists():
        path.write_text(incoming_text, encoding="utf-8")
        logger.info("created vault note: %s", path)
        return WriteResult(path=path, action="created")

    existing_text = path.read_text(encoding="utf-8")
    existing_fm, existing_body = parse_frontmatter(existing_text)

    # Preserve the original `created` timestamp — invariant from schema.
    if "created" in existing_fm:
        frontmatter = {**frontmatter, "created": existing_fm["created"]}

    # Re-assemble with potentially updated `updated` field.
    full_body = _assemble_body(body, generated_section)
    incoming_text = render_frontmatter(frontmatter) + full_body

    if existing_text == incoming_text:
        return WriteResult(path=path, action="skipped")

    # If a generated block exists, replace it safely.
    if _GENERATED_SECTION_START in existing_text:
        updated_text = _replace_generated_section(existing_text, frontmatter, generated_section)
        path.write_text(updated_text, encoding="utf-8")
        logger.info("updated vault note (generated section): %s", path)
        return WriteResult(path=path, action="updated")

    # No generated block and content differs — possible user edit.
    # Record conflict rather than overwriting.
    conflict = ConflictRecord(
        path=path,
        reason="no generated block found; body content differs",
        existing_hash=_content_hash(existing_text),
        incoming_hash=_content_hash(incoming_text),
    )
    logger.warning(
        "conflict detected for %s — existing content preserved; review required",
        path,
    )
    return WriteResult(path=path, action="conflict", conflict=conflict)


def _assemble_body(body: str, generated_section: str | None) -> str:
    if generated_section is None:
        return body
    return (
        body.rstrip()
        + f"\n\n{_GENERATED_SECTION_START}\n"
        + generated_section.strip()
        + f"\n{_GENERATED_SECTION_END}\n"
    )


def _replace_generated_section(
    existing_text: str,
    frontmatter: dict,
    generated_section: str | None,
) -> str:
    """Replace frontmatter + generated section in an existing note."""
    existing_fm, existing_body = parse_frontmatter(existing_text)

    # Keep `created` from existing.
    if "created" in existing_fm:
        frontmatter = {**frontmatter, "created": existing_fm["created"]}

    # Strip old generated block from body.
    gen_re = re.compile(
        rf"{re.escape(_GENERATED_SECTION_START)}.*?{re.escape(_GENERATED_SECTION_END)}\n?",
        re.DOTALL,
    )
    clean_body = gen_re.sub("", existing_body).rstrip()

    full_body = _assemble_body(clean_body, generated_section)
    return render_frontmatter(frontmatter) + full_body
