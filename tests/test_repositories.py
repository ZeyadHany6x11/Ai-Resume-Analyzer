from resume_analyzer.repositories import (
    AnalysisJobRecord,
    SQLiteAnalysisJobRepository,
    SQLiteAnalysisResultRepository,
)


def test_sqlite_job_repository_creates_and_updates_job(tmp_path):
    database_path = str(tmp_path / "analysis.db")
    repository = SQLiteAnalysisJobRepository(database_path)

    job_id = repository.create(
        AnalysisJobRecord(
            id="job-1",
            status="queued",
            input_type="text",
            cv_text="Python resume",
            job_description="Python job",
        )
    )
    repository.update_status(job_id, "processing")

    job = repository.get(job_id)

    assert job is not None
    assert job.id == "job-1"
    assert job.status == "processing"
    assert job.cv_text == "Python resume"
    assert job.job_description == "Python job"
    assert job.created_at is not None
    assert job.updated_at is not None


def test_sqlite_result_repository_saves_and_loads_json_result(tmp_path):
    database_path = str(tmp_path / "analysis.db")
    job_repository = SQLiteAnalysisJobRepository(database_path)
    result_repository = SQLiteAnalysisResultRepository(database_path)
    job_id = job_repository.create(
        AnalysisJobRecord(
            id="job-1",
            status="queued",
            input_type="text",
            cv_text="Python resume",
            job_description="Python job",
        )
    )

    result_repository.save(job_id, {"match_score": 88, "matched_skills": ["python"]})
    result = result_repository.get_by_job_id(job_id)

    assert result is not None
    assert result.job_id == job_id
    assert result.result == {"match_score": 88, "matched_skills": ["python"]}
    assert result.created_at is not None
