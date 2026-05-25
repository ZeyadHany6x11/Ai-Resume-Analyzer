"""Database connection and schema utilities."""

from resume_analyzer.database.sqlite import connect, initialize_database

__all__ = ["connect", "initialize_database"]
