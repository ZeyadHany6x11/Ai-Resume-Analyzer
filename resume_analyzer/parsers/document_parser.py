from __future__ import annotations

import io

import PyPDF2

from resume_analyzer.utils import DocumentParsingError, UnsupportedDocumentError

DocumentSource = bytes | str | io.BytesIO


class DocumentParser:
    """Extract text from supported resume document sources."""

    def extract_text(self, source: DocumentSource) -> str:
        if isinstance(source, str):
            return source

        if isinstance(source, (bytes, io.BytesIO)):
            stream = io.BytesIO(source) if isinstance(source, bytes) else source
            try:
                reader = PyPDF2.PdfReader(stream)
                pages = [page.extract_text() or "" for page in reader.pages]
                return "\n".join(pages)
            except Exception as exc:
                raise DocumentParsingError(f"Failed to read PDF: {exc}") from exc

        raise UnsupportedDocumentError(f"Unsupported source type: {type(source)}")
