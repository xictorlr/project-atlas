"""HTML extractor — uses BeautifulSoup4 to strip tags and preserve structure."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class HtmlResult:
    full_text: str
    title: str | None
    author: str | None
    language: str | None


def extract_html(raw: bytes, encoding: str = "utf-8") -> HtmlResult:
    """Extract readable text from an HTML document.

    Inputs:  raw bytes of an HTML file.
    Outputs: HtmlResult with stripped text, title, author, and lang attribute.
    Failures: falls back to html.parser if lxml is unavailable.
    """
    from bs4 import BeautifulSoup  # deferred import

    try:
        soup = BeautifulSoup(raw, "lxml")
    except Exception:
        soup = BeautifulSoup(raw, "html.parser")

    # Remove script, style, and navigation noise.
    for tag in soup(["script", "style", "nav", "footer", "header"]):
        tag.decompose()

    title = _extract_title(soup)
    author = _extract_author(soup)
    language = _extract_language(soup)
    full_text = _extract_body_text(soup)

    return HtmlResult(full_text=full_text, title=title, author=author, language=language)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _extract_title(soup: object) -> str | None:
    from bs4 import BeautifulSoup, Tag  # type: ignore[attr-defined]

    # Prefer <title> tag, then <h1>.
    title_tag = soup.find("title")  # type: ignore[union-attr]
    if title_tag and title_tag.get_text(strip=True):
        return title_tag.get_text(strip=True)[:200]
    h1 = soup.find("h1")  # type: ignore[union-attr]
    if h1 and h1.get_text(strip=True):
        return h1.get_text(strip=True)[:200]
    return None


def _extract_author(soup: object) -> str | None:
    # <meta name="author" content="..."> pattern.
    meta = soup.find("meta", attrs={"name": "author"})  # type: ignore[union-attr]
    if meta:
        content = meta.get("content", "").strip()  # type: ignore[union-attr]
        if content:
            return content[:200]
    return None


def _extract_language(soup: object) -> str | None:
    html_tag = soup.find("html")  # type: ignore[union-attr]
    if html_tag:
        lang = html_tag.get("lang", "")  # type: ignore[union-attr]
        if lang:
            return str(lang).split("-")[0].lower()[:10]
    return None


def _extract_body_text(soup: object) -> str:
    # Get text with a single newline between block-level elements.
    lines = []
    for element in soup.find_all(["p", "h1", "h2", "h3", "h4", "h5", "h6", "li", "td", "th"]):  # type: ignore[union-attr]
        text = element.get_text(separator=" ", strip=True)  # type: ignore[union-attr]
        if text:
            lines.append(text)
    if lines:
        return "\n\n".join(lines)
    # Fallback: all text
    return soup.get_text(separator="\n", strip=True)  # type: ignore[union-attr]
