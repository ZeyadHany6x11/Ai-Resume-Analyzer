"""Embedding providers and similarity implementations."""

from resume_analyzer.embeddings.cached import CachedSimilarityProvider
from resume_analyzer.embeddings.providers import (
    HybridSimilarityProvider,
    SentenceTransformerSimilarityProvider,
    SimilarityProvider,
    TfidfSimilarityProvider,
)

__all__ = [
    "HybridSimilarityProvider",
    "CachedSimilarityProvider",
    "SentenceTransformerSimilarityProvider",
    "SimilarityProvider",
    "TfidfSimilarityProvider",
]
