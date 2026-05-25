import io

import pytest

from resume_analyzer.parsers import DocumentParser


def test_document_parser_returns_plain_text_unchanged():
    assert DocumentParser().extract_text("plain resume text") == "plain resume text"


def test_document_parser_rejects_unsupported_source_type():
    with pytest.raises(TypeError, match="Unsupported source type"):
        DocumentParser().extract_text(object())


def test_document_parser_wraps_invalid_pdf_errors():
    with pytest.raises(ValueError, match="Failed to read PDF"):
        DocumentParser().extract_text(io.BytesIO(b"not a pdf"))


def test_document_parser_rejects_truncated_pdf_bytes():
    with pytest.raises(ValueError, match="Failed to read PDF"):
        DocumentParser().extract_text(b"%PDF-1.4\ntruncated")
