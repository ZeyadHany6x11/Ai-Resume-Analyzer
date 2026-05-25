from fastapi.testclient import TestClient

import resume_analyzer.api.main as api_main
from resume_analyzer.api.main import app, get_job_service_dependency
from resume_analyzer.config import Settings
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


def test_versioned_text_endpoint_preserves_existing_behavior(tmp_path):
    client = build_test_client(tmp_path)

    response = client.post(
        "/api/v1/analyses/text",
        json={"cv_text": "Python resume", "job_description": "Python job"},
    )

    assert response.status_code == 202
    assert "analysis_id" in response.json()


def test_list_analyses_endpoint_returns_paginated_jobs(tmp_path):
    client = build_test_client(tmp_path)
    client.post(
        "/api/v1/analyses/text",
        json={"cv_text": "Python resume", "job_description": "Python job"},
    )

    response = client.get("/api/v1/analyses", params={"status": "completed", "limit": 10})

    assert response.status_code == 200
    body = response.json()
    assert body["limit"] == 10
    assert body["offset"] == 0
    assert len(body["jobs"]) == 1
    assert body["jobs"][0]["status"] == "completed"


def test_request_headers_include_trace_and_timing(tmp_path):
    client = build_test_client(tmp_path)

    response = client.get("/health", headers={"X-Request-ID": "req-test"})

    assert response.headers["X-Request-ID"] == "req-test"
    assert float(response.headers["X-Process-Time-Ms"]) >= 0


def test_missing_analysis_returns_404(tmp_path):
    client = build_test_client(tmp_path)

    response = client.get("/analyses/missing/status")

    assert response.status_code == 404
    assert response.json() == {
        "error": {
            "code": "http_error",
            "message": "Analysis job not found.",
            "request_id": response.headers["X-Request-ID"],
        }
    }


def test_file_upload_rejects_non_pdf(tmp_path):
    client = build_test_client(tmp_path)

    response = client.post(
        "/api/v1/analyses/file",
        data={"job_description": "Python job"},
        files={"file": ("resume.txt", b"plain text", "text/plain")},
    )

    assert response.status_code == 400
    assert response.json()["error"]["code"] == "AnalysisValidationError"


def test_file_upload_rejects_empty_pdf(tmp_path):
    client = build_test_client(tmp_path)

    response = client.post(
        "/api/v1/analyses/file",
        data={"job_description": "Python job"},
        files={"file": ("resume.pdf", b"", "application/pdf")},
    )

    assert response.status_code == 400
    assert response.json()["error"]["message"] == "Resume and job description inputs are required."


def test_file_upload_rejects_oversized_pdf(tmp_path, monkeypatch):
    client = build_test_client(tmp_path)
    monkeypatch.setattr(
        api_main,
        "get_settings",
        lambda: Settings(max_upload_size_mb=0),
    )

    response = client.post(
        "/api/v1/analyses/file",
        data={"job_description": "Python job"},
        files={"file": ("resume.pdf", b"%PDF-too-large", "application/pdf")},
    )

    assert response.status_code == 400
    assert response.json()["error"]["code"] == "AnalysisValidationError"


def test_file_upload_accepts_pdf_shape(tmp_path):
    client = build_test_client(tmp_path)

    response = client.post(
        "/api/v1/analyses/file",
        data={"job_description": "Python job"},
        files={"file": ("resume.pdf", b"%PDF-sample", "application/pdf")},
    )

    assert response.status_code == 202
    assert response.json()["status"] == "queued"
