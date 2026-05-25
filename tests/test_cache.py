from resume_analyzer.cache import InMemoryTTLCache
from resume_analyzer.embeddings import CachedSimilarityProvider


class MutableClock:
    def __init__(self):
        self.now = 0.0

    def __call__(self):
        return self.now


class CountingProvider:
    @property
    def method(self):
        return "counting"

    def __init__(self):
        self.calls = 0

    def compute(self, _cv_text, _jd_text):
        self.calls += 1
        return 0.9


def test_in_memory_cache_expires_with_injected_clock():
    clock = MutableClock()
    cache = InMemoryTTLCache(default_ttl_seconds=10, clock=clock)
    cache.set("key", "value")

    assert cache.get("key") == "value"

    clock.now = 11

    assert cache.get("key") is None


def test_cached_similarity_provider_reuses_stable_key():
    provider = CountingProvider()
    cache = InMemoryTTLCache(default_ttl_seconds=60)
    cached = CachedSimilarityProvider(provider, cache, ttl_seconds=60)

    assert cached.compute("python sql", "python") == 0.9
    assert cached.compute("python sql", "python") == 0.9

    assert provider.calls == 1


def test_cached_similarity_provider_recomputes_after_expiration():
    clock = MutableClock()
    provider = CountingProvider()
    cache = InMemoryTTLCache(default_ttl_seconds=5, clock=clock)
    cached = CachedSimilarityProvider(provider, cache, ttl_seconds=5)

    cached.compute("python sql", "python")
    clock.now = 6
    cached.compute("python sql", "python")

    assert provider.calls == 2
