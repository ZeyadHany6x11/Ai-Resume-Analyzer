from resume_analyzer.services import ResumeAnalysisService


class FakeParser:
    def extract_text(self, source):
        return source


class FakePreprocessor:
    def preprocess(self, text):
        return text.lower().split()


class FakeSkillExtractor:
    def extract(self, text, extra_skills=None):
        return {skill for skill in ["python", "sql", "aws"] if skill in text.lower()}


class FakeSimilarityProvider:
    @property
    def method(self):
        return "fake similarity"

    def compute(self, _cv_text, _jd_text):
        return 0.5


class FakeRankingService:
    def generate_report(self, similarity_score, cv_skills, jd_skills, cv_tokens):
        return {
            "match_score": 70,
            "matched_skills": sorted(cv_skills & jd_skills),
            "missing_skills": sorted(jd_skills - cv_skills),
            "extra_skills": sorted(cv_skills - jd_skills),
            "suggestions": ["test suggestion"],
            "strength": "Good",
            "similarity_score": round(similarity_score * 100, 1),
            "skill_overlap": 50,
        }


def test_analysis_service_orchestrates_full_report_shape():
    service = ResumeAnalysisService(
        parser=FakeParser(),
        preprocessor=FakePreprocessor(),
        skill_extractor=FakeSkillExtractor(),
        similarity_provider=FakeSimilarityProvider(),
        ranking_service=FakeRankingService(),
    )

    report = service.analyze("Python SQL resume", "Python AWS job")

    assert report["match_score"] == 70
    assert report["matched_skills"] == ["python"]
    assert report["missing_skills"] == ["aws"]
    assert report["extra_skills"] == ["sql"]
    assert report["cv_text"] == "Python SQL resume"
    assert report["jd_text"] == "Python AWS job"
    assert report["method"] == "fake similarity"
