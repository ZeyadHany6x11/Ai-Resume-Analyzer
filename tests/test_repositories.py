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


def test_sqlite_job_repository_filters_and_paginates_jobs(tmp_path):
    database_path = str(tmp_path / "analysis.db")
    repository = SQLiteAnalysisJobRepository(database_path)
    for index in range(3):
        repository.create(
            AnalysisJobRecord(
                id=f"job-{index}",
                status="queued" if index < 2 else "completed",
                input_type="text",
                cv_text="Python resume",
                job_description="Python job",
            )
        )

    first_page = repository.list(status="queued", limit=1, offset=0)
    second_page = repository.list(status="queued", limit=1, offset=1)

    assert len(first_page) == 1
    assert len(second_page) == 1
    assert first_page[0].id != second_page[0].id


def test_sqlite_repositories_cleanup_expired_jobs_and_results(tmp_path):
    database_path = str(tmp_path / "analysis.db")
    job_repository = SQLiteAnalysisJobRepository(database_path)
    result_repository = SQLiteAnalysisResultRepository(database_path)
    job_id = job_repository.create(
        AnalysisJobRecord(
            id="job-old",
            status="completed",
            input_type="text",
            cv_text="Python resume",
            job_description="Python job",
            created_at="2020-01-01T00:00:00+00:00",
            updated_at="2020-01-01T00:00:00+00:00",
        )
    )
    result_repository.save(job_id, {"match_score": 88})

    deleted_jobs = job_repository.cleanup("2021-01-01T00:00:00+00:00")

    assert deleted_jobs == 1
    assert job_repository.get(job_id) is None
    assert result_repository.get_by_job_id(job_id) is None
