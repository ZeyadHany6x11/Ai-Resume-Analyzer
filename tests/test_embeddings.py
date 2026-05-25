from resume_analyzer.embeddings import HybridSimilarityProvider, TfidfSimilarityProvider


class FailingProvider:
    @property
    def method(self):
        return "failing"

    def compute(self, _cv_text, _jd_text):
        raise RuntimeError("boom")


class FixedProvider:
    @property
    def method(self):
        return "fixed"

    def compute(self, _cv_text, _jd_text):
        return 0.42


def test_tfidf_similarity_provider_returns_bounded_score():
    score = TfidfSimilarityProvider().compute("python sql", "python docker")

    assert 0 <= score <= 1


def test_hybrid_similarity_provider_falls_back_deterministically():
    provider = HybridSimilarityProvider(fallback_provider=FixedProvider())
    provider._sbert_provider = FailingProvider()

    assert provider.compute("a", "b") == 0.42
    assert provider.method == "fixed"
