from __future__ import annotations

from resume_analyzer.embeddings import SimilarityProvider
from resume_analyzer.parsers import DocumentParser, DocumentSource
from resume_analyzer.ranking import RankingService
from resume_analyzer.services.skill_extraction import SkillExtractionService
from resume_analyzer.services.text_preprocessing import TextPreprocessingService


class ResumeAnalysisService:
    """Coordinate the resume analysis business workflow."""

    def __init__(
        self,
        parser: DocumentParser,
        preprocessor: TextPreprocessingService,
        skill_extractor: SkillExtractionService,
        similarity_provider: SimilarityProvider,
        ranking_service: RankingService,
    ) -> None:
        self._parser = parser
        self._preprocessor = preprocessor
        self._skill_extractor = skill_extractor
        self._similarity_provider = similarity_provider
        self._ranking_service = ranking_service

    @property
    def similarity_method(self) -> str:
        return self._similarity_provider.method

    def extract_text(self, source: DocumentSource) -> str:
        return self._parser.extract_text(source)

    def preprocess_text(self, text: str) -> list[str]:
        return self._preprocessor.preprocess(text)

    def extract_skills(self, text: str, extra_skills=None) -> set[str]:
        return self._skill_extractor.extract(text, extra_skills)

    def compute_similarity(self, cv_text: str, jd_text: str) -> float:
        return self._similarity_provider.compute(cv_text, jd_text)

    def generate_report(
        self,
        similarity_score: float,
        cv_skills: set[str],
        jd_skills: set[str],
        cv_tokens: list[str],
    ) -> dict:
        return self._ranking_service.generate_report(
            similarity_score=similarity_score,
            cv_skills=cv_skills,
            jd_skills=jd_skills,
            cv_tokens=cv_tokens,
        )

    def analyze(self, cv_source: DocumentSource, jd_text: str) -> dict:
        cv_text = self.extract_text(cv_source)
        cv_tokens = self.preprocess_text(cv_text)
        jd_tokens = self.preprocess_text(jd_text)

        cv_skills = self.extract_skills(cv_text)
        jd_skills = self.extract_skills(jd_text)

        joined_cv = " ".join(cv_tokens)
        joined_jd = " ".join(jd_tokens)
        similarity_score = self.compute_similarity(joined_cv, joined_jd)

        report = self.generate_report(similarity_score, cv_skills, jd_skills, cv_tokens)
        report["cv_text"] = cv_text
        report["jd_text"] = jd_text
        report["method"] = self.similarity_method
        return report
