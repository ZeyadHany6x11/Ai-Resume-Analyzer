import resume_analyzer
from resume_analyzer import analyze, extract_skills, extract_text


def test_legacy_public_imports_remain_available():
    assert callable(analyze)
    assert callable(extract_text)
    assert callable(extract_skills)


def test_smoke_text_analysis_returns_existing_report_shape():
    resume_analyzer._legacy.compute_similarity = lambda _cv, _jd: 0.75
    resume_analyzer._legacy.similarity_method = lambda: "test similarity"

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
