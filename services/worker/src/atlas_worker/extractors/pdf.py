"""PDF extractor — uses pdfplumber to extract text and metadata."""

from __future__ import annotations

import io
from dataclasses import dataclass, field


@dataclass(frozen=True)
class PdfResult:
    full_text: str
    title: str | None
    author: str | None
    page_count: int
    language: str | None = None


def extract_pdf(raw: bytes) -> PdfResult:
    """Extract text and metadata from a PDF byte payload.

    Inputs:  raw bytes of a PDF file.
    Outputs: PdfResult with concatenated page text, title, author, page_count.
    Failures: raises ValueError if pdfplumber cannot open the bytes.
    """
    import pdfplumber  # deferred so the module is importable without the dep installed

    with pdfplumber.open(io.BytesIO(raw)) as pdf:
        meta = pdf.metadata or {}
        pages_text: list[str] = []
        for page in pdf.pages:
            page_text = page.extract_text() or ""
            pages_text.append(page_text)

        full_text = "\n\n".join(p for p in pages_text if p.strip())
        title = _clean_meta_str(meta.get("Title")) or _infer_title_from_text(full_text)
        author = _clean_meta_str(meta.get("Author"))
        page_count = len(pdf.pages)

    return PdfResult(
        full_text=full_text,
        title=title,
        author=author,
        page_count=page_count,
    )


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _clean_meta_str(value: object) -> str | None:
    if not isinstance(value, str):
        return None
    cleaned = value.strip()
    return cleaned if cleaned else None


def _infer_title_from_text(text: str) -> str | None:
    for line in text.splitlines():
        stripped = line.strip()
        if stripped and len(stripped) <= 200:
            return stripped
    return None
