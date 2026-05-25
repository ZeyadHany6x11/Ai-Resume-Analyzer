"""Persistence repositories."""

from resume_analyzer.repositories.analysis import (
    AnalysisJobRecord,
    AnalysisJobRepository,
    AnalysisResultRecord,
    AnalysisResultRepository,
    JobStatus,
    SQLiteAnalysisJobRepository,
    SQLiteAnalysisResultRepository,
)

__all__ = [
    "AnalysisJobRecord",
    "AnalysisJobRepository",
    "AnalysisResultRecord",
    "AnalysisResultRepository",
    "JobStatus",
    "SQLiteAnalysisJobRepository",
    "SQLiteAnalysisResultRepository",
]
