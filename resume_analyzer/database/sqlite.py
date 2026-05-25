from __future__ import annotations

import sqlite3
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path


def connect(database_path: str) -> sqlite3.Connection:
    parent = Path(database_path).parent
    if parent != Path("."):
        parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(database_path)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    return connection


@contextmanager
def connection_scope(database_path: str) -> Iterator[sqlite3.Connection]:
    connection = connect(database_path)
    try:
        yield connection
    finally:
        connection.close()


@contextmanager
def transaction(database_path: str) -> Iterator[sqlite3.Connection]:
    connection = connect(database_path)
    try:
        yield connection
        connection.commit()
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()


def initialize_database(database_path: str) -> None:
    with transaction(database_path) as connection:
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS analysis_jobs (
                id TEXT PRIMARY KEY,
                status TEXT NOT NULL,
                input_type TEXT NOT NULL,
                cv_text TEXT,
                cv_file BLOB,
                job_description TEXT NOT NULL,
                error_message TEXT,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
            """
        )
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS analysis_results (
                job_id TEXT PRIMARY KEY,
                result_json TEXT NOT NULL,
                created_at TEXT NOT NULL,
                FOREIGN KEY(job_id) REFERENCES analysis_jobs(id) ON DELETE CASCADE
            )
            """
        )
