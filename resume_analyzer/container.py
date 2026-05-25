from __future__ import annotations

from functools import lru_cache

from resume_analyzer.embeddings import HybridSimilarityProvider
from resume_analyzer.parsers import DocumentParser
from resume_analyzer.ranking import RankingService
from resume_analyzer.services import (
    ResumeAnalysisService,
    SkillExtractionService,
    TextPreprocessingService,
)


def build_analysis_service() -> ResumeAnalysisService:
    return ResumeAnalysisService(
        parser=DocumentParser(),
        preprocessor=TextPreprocessingService(),
        skill_extractor=SkillExtractionService(),
        similarity_provider=HybridSimilarityProvider(),
        ranking_service=RankingService(),
    )


@lru_cache(maxsize=1)
def get_analysis_service() -> ResumeAnalysisService:
    return build_analysis_service()
