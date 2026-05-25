from __future__ import annotations

import asyncio
import io
import logging
import time
from collections.abc import Callable
from datetime import UTC, datetime, timedelta

from resume_analyzer.repositories import (
    AnalysisJobRecord,
    AnalysisJobRepository,
    AnalysisResultRepository,
)
from resume_analyzer.services.analysis import ResumeAnalysisService
from resume_analyzer.services.background import BackgroundRunner
from resume_analyzer.utils import JobProcessingError, ResumeAnalyzerError

logger = logging.getLogger(__name__)


class AnalysisJobService:
    """Manage persisted analysis jobs and background processing."""

    def __init__(
        self,
        job_repository: AnalysisJobRepository,
        result_repository: AnalysisResultRepository,
        analysis_service: ResumeAnalysisService,
        max_retries: int = 2,
        timeout_seconds: float = 120.0,
        clock: Callable[[], float] = time.monotonic,
    ) -> None:
        self._job_repository = job_repository
        self._result_repository = result_repository
        self._analysis_service = analysis_service
        self._max_retries = max_retries
        self._timeout_seconds = timeout_seconds
        self._clock = clock

    def create_text_job(self, cv_text: str, job_description: str) -> AnalysisJobRecord:
        job = AnalysisJobRecord(
            id="",
            status="queued",
            input_type="text",
            cv_text=cv_text,
            job_description=job_description,
        )
        job_id = self._job_repository.create(job)
        created = self._job_repository.get(job_id)
        if created is None:
            raise JobProcessingError(f"Created job {job_id} could not be loaded.")
        return created

    def create_file_job(self, cv_file: bytes, job_description: str) -> AnalysisJobRecord:
        job = AnalysisJobRecord(
            id="",
            status="queued",
            input_type="file",
            cv_file=cv_file,
            job_description=job_description,
        )
        job_id = self._job_repository.create(job)
        created = self._job_repository.get(job_id)
        if created is None:
            raise JobProcessingError(f"Created job {job_id} could not be loaded.")
        return created

    def enqueue(self, job_id: str, runner: BackgroundRunner) -> None:
        runner.add_task(self.run_analysis_job, job_id)

    def get_status(self, job_id: str) -> AnalysisJobRecord | None:
        return self._job_repository.get(job_id)

    def get_result(self, job_id: str) -> dict | None:
        result = self._result_repository.get_by_job_id(job_id)
        return result.result if result else None

    def run_analysis_job(self, job_id: str) -> None:
        job = self._job_repository.get(job_id)
        if job is None:
            raise JobProcessingError(f"Analysis job {job_id} was not found.")

        attempt = 0
        while attempt <= self._max_retries:
            attempt += 1
            self._job_repository.update_status(job_id, "processing")
            logger.info(
                "Analysis job started",
                extra={"job_id": job_id, "attempt": attempt, "category": "job_lifecycle"},
            )

            started_at = self._clock()
            try:
                cv_source = self._resolve_cv_source(job)
                result = self._analysis_service.analyze(cv_source, job.job_description)
                elapsed = self._clock() - started_at
                if elapsed > self._timeout_seconds:
                    raise JobProcessingError("Analysis job exceeded timeout budget.")

                self._result_repository.save(job_id, result)
                self._job_repository.update_status(job_id, "completed")
                logger.info(
                    "Analysis job completed",
                    extra={"job_id": job_id, "attempt": attempt, "category": "job_lifecycle"},
                )
                return
            except asyncio.CancelledError:
                logger.warning(
                    "Analysis job cancelled",
                    extra={"job_id": job_id, "attempt": attempt, "category": "job_lifecycle"},
                )
                self._job_repository.update_status(job_id, "failed", "Analysis job was cancelled.")
                raise
            except ResumeAnalyzerError as exc:
                logger.warning(
                    "Analysis job failed with expected application error",
                    extra={"job_id": job_id, "attempt": attempt, "category": "application"},
                )
                self._job_repository.update_status(job_id, "failed", exc.safe_message)
                return
            except Exception:
                if attempt <= self._max_retries:
                    logger.warning(
                        "Analysis job attempt failed and will retry",
                        extra={"job_id": job_id, "attempt": attempt, "category": "retry"},
                    )
                    continue
                logger.exception(
                    "Analysis job failed after retries",
                    extra={"job_id": job_id, "attempt": attempt, "category": "unexpected"},
                )
                self._job_repository.update_status(
                    job_id, "failed", JobProcessingError.safe_message
                )
                return

    def cleanup_stale_jobs(self, stale_age_seconds: int, limit: int = 100) -> int:
        older_than = datetime.now(UTC) - timedelta(seconds=stale_age_seconds)
        stale_jobs = self._job_repository.find_stale(
            statuses=["queued", "processing"],
            older_than=older_than.isoformat(),
            limit=limit,
        )
        for job in stale_jobs:
            self._job_repository.update_status(
                job.id,
                "failed",
                "Analysis job expired before completion.",
            )
        return len(stale_jobs)

    def _resolve_cv_source(self, job: AnalysisJobRecord):
        if job.input_type == "text" and job.cv_text is not None:
            return job.cv_text
        if job.input_type == "file" and job.cv_file is not None:
            return io.BytesIO(job.cv_file)
        raise JobProcessingError(f"Analysis job {job.id} has invalid input data.")
