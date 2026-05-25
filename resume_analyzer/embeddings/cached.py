from __future__ import annotations

import hashlib

from resume_analyzer.cache import Cache
from resume_analyzer.embeddings.providers import SimilarityProvider


class CachedSimilarityProvider:
    """Cache expensive similarity computations by stable text content hashes."""

    def __init__(self, provider: SimilarityProvider, cache: Cache, ttl_seconds: int) -> None:
        self._provider = provider
        self._cache = cache
        self._ttl_seconds = ttl_seconds

    @property
    def method(self) -> str:
        return self._provider.method

    def compute(self, cv_text: str, jd_text: str) -> float:
        key = self._cache_key(cv_text, jd_text)
        cached = self._cache.get(key)
        if cached is not None:
            return float(cached)

        score = self._provider.compute(cv_text, jd_text)
        self._cache.set(key, score, ttl_seconds=self._ttl_seconds)
        return score

    def _cache_key(self, cv_text: str, jd_text: str) -> str:
        digest = hashlib.sha256()
        digest.update(type(self._provider).__name__.encode("utf-8"))
        digest.update(b"\0")
        digest.update(cv_text.encode("utf-8"))
        digest.update(b"\0")
        digest.update(jd_text.encode("utf-8"))
        return f"similarity:{digest.hexdigest()}"
