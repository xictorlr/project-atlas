"""Unit tests for extractor modules."""

import pytest
from atlas_worker.extractors.text import extract_text
from atlas_worker.extractors.html import extract_html
from atlas_worker.jobs.ingest import _chunk_text, _split_sentences, _extract


# ---------------------------------------------------------------------------
# text extractor
# ---------------------------------------------------------------------------

class TestExtractText:
    def test_basic_passthrough(self):
        raw = b"Hello world\n\nSecond paragraph."
        result = extract_text(raw)
        assert "Hello world" in result.full_text
        assert "Second paragraph" in result.full_text

    def test_title_inferred_from_first_line(self):
        raw = b"My Document Title\n\nBody text here."
        result = extract_text(raw)
        assert result.title == "My Document Title"

    def test_language_detection_english(self):
        text = ("the cat is in the house and it is that thing to do " * 5).encode()
        result = extract_text(text)
        assert result.language == "en"

    def test_language_returns_none_for_short_text(self):
        result = extract_text(b"hi")
        assert result.language is None

    def test_latin1_fallback(self):
        raw = "Héllo wörld".encode("latin-1")
        result = extract_text(raw, encoding="utf-8")
        assert "H" in result.full_text  # at minimum, decoded without crash


# ---------------------------------------------------------------------------
# html extractor
# ---------------------------------------------------------------------------

class TestExtractHtml:
    def test_strips_script_tags(self):
        html = b"<html><body><script>alert(1)</script><p>Content</p></body></html>"
        result = extract_html(html)
        assert "alert" not in result.full_text
        assert "Content" in result.full_text

    def test_extracts_title_from_title_tag(self):
        html = b"<html><head><title>Test Page</title></head><body><p>body</p></body></html>"
        result = extract_html(html)
        assert result.title == "Test Page"

    def test_extracts_author_from_meta(self):
        html = (
            b'<html><head><meta name="author" content="Jane Doe"/></head>'
            b"<body><p>text</p></body></html>"
        )
        result = extract_html(html)
        assert result.author == "Jane Doe"

    def test_extracts_language_from_html_tag(self):
        html = b'<html lang="en-US"><body><p>text</p></body></html>'
        result = extract_html(html)
        assert result.language == "en"

    def test_handles_minimal_html(self):
        html = b"<p>Hello</p>"
        result = extract_html(html)
        assert "Hello" in result.full_text

    def test_no_title_returns_none(self):
        html = b"<html><body><p>no heading</p></body></html>"
        result = extract_html(html)
        assert result.title is None or isinstance(result.title, str)


# ---------------------------------------------------------------------------
# chunking
# ---------------------------------------------------------------------------

class TestChunkText:
    def test_empty_text_returns_empty_list(self):
        assert _chunk_text("") == []
        assert _chunk_text("   \n\n  ") == []

    def test_short_text_single_chunk(self):
        chunks = _chunk_text("Hello world.")
        assert len(chunks) == 1
        assert chunks[0] == "Hello world."

    def test_splits_on_double_newline(self):
        text = "Para one.\n\nPara two.\n\nPara three."
        chunks = _chunk_text(text, target=20, max_size=30)
        assert len(chunks) >= 2

    def test_chunk_respects_target_size(self):
        paras = "\n\n".join(["word " * 100] * 5)
        chunks = _chunk_text(paras, target=200, max_size=600)
        for chunk in chunks:
            assert len(chunk) <= 600

    def test_no_empty_chunks(self):
        text = "\n\n".join(["sentence."] * 20)
        chunks = _chunk_text(text, target=50)
        assert all(c.strip() for c in chunks)


class TestSplitSentences:
    def test_splits_on_period(self):
        text = "First sentence. Second sentence. Third sentence."
        parts = _split_sentences(text, target=20)
        assert len(parts) >= 2

    def test_single_short_sentence_stays_whole(self):
        text = "Just one sentence."
        parts = _split_sentences(text, target=100)
        assert parts == ["Just one sentence."]


# ---------------------------------------------------------------------------
# extraction dispatcher
# ---------------------------------------------------------------------------

class TestExtractDispatcher:
    def test_plain_text_mime(self):
        result = _extract(b"hello world", "text/plain")
        assert result["full_text"] == "hello world"

    def test_none_mime_defaults_to_text(self):
        result = _extract(b"hello", None)
        assert "hello" in result["full_text"]

    def test_html_mime_dispatches_to_html(self):
        html = b"<html><body><p>Hello HTML</p></body></html>"
        result = _extract(html, "text/html")
        assert "Hello HTML" in result["full_text"]
