from fastapi.testclient import TestClient

from resume_analyzer.api.main import app, get_job_service_dependency
from resume_analyzer.repositories import SQLiteAnalysisJobRepository, SQLiteAnalysisResultRepository
from resume_analyzer.services import AnalysisJobService


class FakeAnalysisService:
    def analyze(self, cv_source, job_description):
        return {
            "match_score": 84,
            "cv_text": cv_source if isinstance(cv_source, str) else "file text",
            "jd_text": job_description,
            "method": "fake",
            "matched_skills": ["python"],
            "missing_skills": [],
            "extra_skills": [],
            "suggestions": ["solid fit"],
            "strength": "Excellent",
            "similarity_score": 84.0,
            "skill_overlap": 100.0,
        }


def build_test_client(tmp_path):
    database_path = str(tmp_path / "api.db")
    service = AnalysisJobService(
        job_repository=SQLiteAnalysisJobRepository(database_path),
        result_repository=SQLiteAnalysisResultRepository(database_path),
        analysis_service=FakeAnalysisService(),
    )
    app.dependency_overrides[get_job_service_dependency] = lambda: service
    return TestClient(app)


def test_health_endpoint(tmp_path):
    client = build_test_client(tmp_path)

    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_text_analysis_endpoint_creates_completed_background_job(tmp_path):
    client = build_test_client(tmp_path)

    submission = client.post(
        "/analyses/text",
        json={"cv_text": "Python resume", "job_description": "Python job"},
    )

    assert submission.status_code == 202
    analysis_id = submission.json()["analysis_id"]

    status = client.get(f"/analyses/{analysis_id}/status")
    result = client.get(f"/analyses/{analysis_id}")

    assert status.status_code == 200
    assert status.json()["status"] == "completed"
    assert result.status_code == 200
    assert result.json()["result"]["match_score"] == 84


def test_missing_analysis_returns_404(tmp_path):
    client = build_test_client(tmp_path)

    response = client.get("/analyses/missing/status")

    assert response.status_code == 404
