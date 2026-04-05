"""Plain-text extractor — passthrough with basic metadata heuristics."""

from __future__ import annotations

import re
from dataclasses import dataclass


@dataclass(frozen=True)
class TextResult:
    full_text: str
    title: str | None
    language: str | None


def extract_text(raw: bytes, encoding: str = "utf-8") -> TextResult:
    """Decode and return plain text with minimal metadata extraction.

    Inputs:  raw bytes of a plain-text file.
    Outputs: TextResult with full_text, inferred title, and detected language tag.
    Failures: UnicodeDecodeError falls back to latin-1.
    """
    try:
        text = raw.decode(encoding)
    except UnicodeDecodeError:
        text = raw.decode("latin-1")

    title = _infer_title(text)
    language = _detect_language_hint(text)
    return TextResult(full_text=text, title=title, language=language)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _infer_title(text: str) -> str | None:
    """Return the first non-empty line if it looks like a heading."""
    for line in text.splitlines():
        stripped = line.strip()
        if stripped:
            # Accept lines up to 200 chars as a title candidate.
            return stripped[:200] if len(stripped) <= 200 else None
    return None


# Minimal language detection by common stop-word frequency.
_LANG_HINTS: dict[str, frozenset[str]] = {
    "en": frozenset({"the", "and", "of", "to", "in", "is", "it", "that"}),
    "es": frozenset({"de", "la", "el", "en", "que", "y", "los", "las", "un"}),
    "fr": frozenset({"de", "la", "le", "les", "et", "en", "un", "une", "du"}),
    "de": frozenset({"der", "die", "das", "und", "in", "zu", "den", "ist"}),
}


def _detect_language_hint(text: str) -> str | None:
    """Return ISO-639-1 code for the most likely language, or None if uncertain."""
    words = re.findall(r"\b[a-zA-Z]{2,}\b", text.lower())
    if not words:
        return None
    sample = set(words[:500])
    scores = {lang: len(sample & hints) for lang, hints in _LANG_HINTS.items()}
    best_lang, best_score = max(scores.items(), key=lambda x: x[1])
    return best_lang if best_score >= 3 else None
