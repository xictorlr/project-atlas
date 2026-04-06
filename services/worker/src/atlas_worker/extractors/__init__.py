"""Text extraction modules for supported source mime types."""

from atlas_worker.extractors.audio import AudioResult, extract_audio
from atlas_worker.extractors.docx import DocxResult, extract_docx
from atlas_worker.extractors.html import extract_html
from atlas_worker.extractors.ocr import OcrResult, extract_ocr
from atlas_worker.extractors.pdf import extract_pdf
from atlas_worker.extractors.pptx import PptxResult, extract_pptx
from atlas_worker.extractors.text import extract_text
from atlas_worker.extractors.xlsx import XlsxResult, extract_xlsx

__all__ = [
    "extract_text",
    "extract_pdf",
    "extract_html",
    "AudioResult",
    "extract_audio",
    "OcrResult",
    "extract_ocr",
    "DocxResult",
    "extract_docx",
    "XlsxResult",
    "extract_xlsx",
    "PptxResult",
    "extract_pptx",
]
