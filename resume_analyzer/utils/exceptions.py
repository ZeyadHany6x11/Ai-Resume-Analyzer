from __future__ import annotations


class ResumeAnalyzerError(Exception):
    """Base class for expected application errors."""

    safe_message = "The resume analysis request could not be completed."


class DocumentParsingError(ResumeAnalyzerError, ValueError):
    safe_message = "Unable to read the uploaded document."


class UnsupportedDocumentError(ResumeAnalyzerError, TypeError):
    safe_message = "Unsupported document source type."


class AnalysisValidationError(ResumeAnalyzerError, ValueError):
    safe_message = "Resume and job description inputs are required."


class EmbeddingProviderError(ResumeAnalyzerError):
    safe_message = "Unable to compute semantic similarity."


class PersistenceError(ResumeAnalyzerError):
    safe_message = "Unable to persist analysis data."


class JobProcessingError(ResumeAnalyzerError):
    safe_message = "Unable to process the analysis job."
