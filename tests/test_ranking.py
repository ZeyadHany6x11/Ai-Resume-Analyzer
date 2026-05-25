from resume_analyzer.ranking import RankingService


def test_ranking_service_preserves_weighted_match_score():
    report = RankingService().generate_report(
        similarity_score=0.5,
        cv_skills={"python", "sql"},
        jd_skills={"python", "sql", "aws", "docker"},
        cv_tokens=["built", "certified"],
    )

    assert report["match_score"] == 50
    assert report["similarity_score"] == 50
    assert report["skill_overlap"] == 50
    assert report["strength"] == "Fair"
    assert report["matched_skills"] == ["python", "sql"]
    assert report["missing_skills"] == ["aws", "docker"]


def test_ranking_service_returns_positive_message_for_strong_fit():
    report = RankingService().generate_report(
        similarity_score=1.0,
        cv_skills={"python"},
        jd_skills={"python"},
        cv_tokens=["built", "certified"],
    )

    assert report["match_score"] == 100
    assert report["strength"] == "Excellent"
    assert report["suggestions"] == [
        "Great fit! Ensure your CV is concise, well-formatted, ATS-friendly, and free of typos."
    ]
