from __future__ import annotations

from functools import lru_cache

from resume_analyzer.cache import InMemoryTTLCache
from resume_analyzer.config import get_settings
from resume_analyzer.embeddings import CachedSimilarityProvider, HybridSimilarityProvider
from resume_analyzer.parsers import DocumentParser
from resume_analyzer.ranking import RankingService
from resume_analyzer.repositories import SQLiteAnalysisJobRepository, SQLiteAnalysisResultRepository
from resume_analyzer.services import (
    AnalysisJobService,
    ResumeAnalysisService,
    SkillExtractionService,
    TextPreprocessingService,
)
from resume_analyzer.utils import configure_logging


def build_analysis_service() -> ResumeAnalysisService:
    settings = get_settings()
    configure_logging(settings)
    similarity_provider = HybridSimilarityProvider(model_name=settings.embedding_model_name)
    if settings.cache_enabled:
        similarity_provider = CachedSimilarityProvider(
            provider=similarity_provider,
            cache=InMemoryTTLCache(default_ttl_seconds=settings.cache_ttl_seconds),
            ttl_seconds=settings.cache_ttl_seconds,
        )

    return ResumeAnalysisService(
        parser=DocumentParser(),
        preprocessor=TextPreprocessingService(),
        skill_extractor=SkillExtractionService(),
        similarity_provider=similarity_provider,
        ranking_service=RankingService(
            semantic_weight=settings.semantic_weight,
            skill_weight=settings.skill_weight,
        ),
    )


@lru_cache(maxsize=1)
def get_analysis_service() -> ResumeAnalysisService:
    return build_analysis_service()


def build_job_service() -> AnalysisJobService:
    settings = get_settings()
    return AnalysisJobService(
        job_repository=SQLiteAnalysisJobRepository(settings.database_path),
        result_repository=SQLiteAnalysisResultRepository(settings.database_path),
        analysis_service=get_analysis_service(),
    )


@lru_cache(maxsize=1)
def get_job_service() -> AnalysisJobService:
    return build_job_service()
