from __future__ import annotations

import json
import uuid
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Protocol

from resume_analyzer.database import connect, initialize_database
from resume_analyzer.utils import PersistenceError


def utc_now_iso() -> str:
    return datetime.now(UTC).isoformat()


@dataclass(frozen=True)
class AnalysisJobRecord:
    id: str
    status: str
    input_type: str
    job_description: str
    cv_text: str | None = None
    cv_file: bytes | None = None
    error_message: str | None = None
    created_at: str | None = None
    updated_at: str | None = None


@dataclass(frozen=True)
class AnalysisResultRecord:
    job_id: str
    result: dict
    created_at: str


class AnalysisJobRepository(Protocol):
    def create(self, job: AnalysisJobRecord) -> str: ...

    def update_status(self, job_id: str, status: str, error_message: str | None = None) -> None: ...

    def get(self, job_id: str) -> AnalysisJobRecord | None: ...


class AnalysisResultRepository(Protocol):
    def save(self, job_id: str, result: dict) -> None: ...

    def get_by_job_id(self, job_id: str) -> AnalysisResultRecord | None: ...


class SQLiteAnalysisJobRepository:
    def __init__(self, database_path: str) -> None:
        self._database_path = database_path
        initialize_database(database_path)

    def create(self, job: AnalysisJobRecord) -> str:
        job_id = job.id or str(uuid.uuid4())
        now = utc_now_iso()
        try:
            with connect(self._database_path) as connection:
                connection.execute(
                    """
                    INSERT INTO analysis_jobs (
                        id, status, input_type, cv_text, cv_file, job_description,
                        error_message, created_at, updated_at
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        job_id,
                        job.status,
                        job.input_type,
                        job.cv_text,
                        job.cv_file,
                        job.job_description,
                        job.error_message,
                        job.created_at or now,
                        job.updated_at or now,
                    ),
                )
        except Exception as exc:
            raise PersistenceError(f"Failed to create analysis job: {exc}") from exc
        return job_id

    def update_status(self, job_id: str, status: str, error_message: str | None = None) -> None:
        try:
            with connect(self._database_path) as connection:
                connection.execute(
                    """
                    UPDATE analysis_jobs
                    SET status = ?, error_message = ?, updated_at = ?
                    WHERE id = ?
                    """,
                    (status, error_message, utc_now_iso(), job_id),
                )
        except Exception as exc:
            raise PersistenceError(f"Failed to update analysis job: {exc}") from exc

    def get(self, job_id: str) -> AnalysisJobRecord | None:
        try:
            with connect(self._database_path) as connection:
                row = connection.execute(
                    "SELECT * FROM analysis_jobs WHERE id = ?",
                    (job_id,),
                ).fetchone()
        except Exception as exc:
            raise PersistenceError(f"Failed to load analysis job: {exc}") from exc

        if row is None:
            return None

        return AnalysisJobRecord(
            id=row["id"],
            status=row["status"],
            input_type=row["input_type"],
            cv_text=row["cv_text"],
            cv_file=row["cv_file"],
            job_description=row["job_description"],
            error_message=row["error_message"],
            created_at=row["created_at"],
            updated_at=row["updated_at"],
        )


class SQLiteAnalysisResultRepository:
    def __init__(self, database_path: str) -> None:
        self._database_path = database_path
        initialize_database(database_path)

    def save(self, job_id: str, result: dict) -> None:
        try:
            with connect(self._database_path) as connection:
                connection.execute(
                    """
                    INSERT OR REPLACE INTO analysis_results (job_id, result_json, created_at)
                    VALUES (?, ?, ?)
                    """,
                    (job_id, json.dumps(result), utc_now_iso()),
                )
        except Exception as exc:
            raise PersistenceError(f"Failed to save analysis result: {exc}") from exc

    def get_by_job_id(self, job_id: str) -> AnalysisResultRecord | None:
        try:
            with connect(self._database_path) as connection:
                row = connection.execute(
                    "SELECT * FROM analysis_results WHERE job_id = ?",
                    (job_id,),
                ).fetchone()
        except Exception as exc:
            raise PersistenceError(f"Failed to load analysis result: {exc}") from exc

        if row is None:
            return None

        return AnalysisResultRecord(
            job_id=row["job_id"],
            result=json.loads(row["result_json"]),
            created_at=row["created_at"],
        )
