from resume_analyzer.repositories import (
    SQLiteAnalysisJobRepository,
    SQLiteAnalysisResultRepository,
)
from resume_analyzer.services import AnalysisJobService, InlineBackgroundRunner


class SuccessfulAnalysisService:
    def analyze(self, cv_source, job_description):
        return {
            "match_score": 91,
            "cv_text": cv_source if isinstance(cv_source, str) else "pdf text",
            "jd_text": job_description,
            "method": "fake",
            "matched_skills": ["python"],
            "missing_skills": [],
            "extra_skills": [],
            "suggestions": ["ship it"],
            "strength": "Excellent",
            "similarity_score": 91.0,
            "skill_overlap": 100.0,
        }


class FailingAnalysisService:
    def analyze(self, _cv_source, _job_description):
        raise RuntimeError("analysis crashed")


def build_job_service(tmp_path, analysis_service):
    database_path = str(tmp_path / "analysis.db")
    return AnalysisJobService(
        job_repository=SQLiteAnalysisJobRepository(database_path),
        result_repository=SQLiteAnalysisResultRepository(database_path),
        analysis_service=analysis_service,
    )


def test_inline_background_runner_processes_job_deterministically(tmp_path):
    service = build_job_service(tmp_path, SuccessfulAnalysisService())
    job = service.create_text_job("Python resume", "Python job")

    service.enqueue(job.id, InlineBackgroundRunner())

    status = service.get_status(job.id)
    result = service.get_result(job.id)

    assert status is not None
    assert status.status == "completed"
    assert status.error_message is None
    assert result is not None
    assert result["match_score"] == 91


def test_job_service_records_failed_status_for_unexpected_errors(tmp_path):
    service = build_job_service(tmp_path, FailingAnalysisService())
    job = service.create_text_job("Python resume", "Python job")

    service.enqueue(job.id, InlineBackgroundRunner())

    status = service.get_status(job.id)
    result = service.get_result(job.id)

    assert status is not None
    assert status.status == "failed"
    assert status.error_message == "Unable to process the analysis job."
    assert result is None
