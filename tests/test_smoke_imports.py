import resume_analyzer
from resume_analyzer import analyze, extract_skills, extract_text


def test_legacy_public_imports_remain_available():
    assert callable(analyze)
    assert callable(extract_text)
    assert callable(extract_skills)


def test_smoke_text_analysis_returns_existing_report_shape():
    class FakeService:
        def analyze(self, cv_source, jd_text):
            return {
                "match_score": 75,
                "similarity_score": 75.0,
                "skill_overlap": 50.0,
                "matched_skills": ["python"],
                "missing_skills": ["aws"],
                "extra_skills": ["sql"],
                "suggestions": ["test"],
                "strength": "Good",
                "cv_text": cv_source,
                "jd_text": jd_text,
                "method": "test similarity",
            }

    resume_analyzer.get_analysis_service.cache_clear()
    resume_analyzer.get_analysis_service = lambda: FakeService()

    report = analyze(
        "Python developer with Django, machine learning, SQL, and Docker experience.",
        "Looking for Python, machine learning, SQL, Docker, and AWS experience.",
    )

    assert "match_score" in report
    assert "similarity_score" in report
    assert "skill_overlap" in report
    assert "matched_skills" in report
    assert "missing_skills" in report
    assert "suggestions" in report
    assert "cv_text" in report
    assert "jd_text" in report
    assert "method" in report
