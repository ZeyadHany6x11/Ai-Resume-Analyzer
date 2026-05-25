from __future__ import annotations

from typing import Protocol

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity


class SimilarityProvider(Protocol):
    """Compute similarity between two normalized text documents."""

    @property
    def method(self) -> str:
        ...

    def compute(self, cv_text: str, jd_text: str) -> float:
        ...


class TfidfSimilarityProvider:
    @property
    def method(self) -> str:
        return "TF-IDF Cosine Similarity"

    def compute(self, cv_text: str, jd_text: str) -> float:
        vectorizer = TfidfVectorizer()
        tfidf_matrix = vectorizer.fit_transform([cv_text, jd_text])
        score = cosine_similarity(tfidf_matrix[0], tfidf_matrix[1])[0][0]
        return float(score)


class SentenceTransformerSimilarityProvider:
    def __init__(self, model_name: str = "all-MiniLM-L6-v2") -> None:
        self._model_name = model_name
        self._model = None

    @property
    def method(self) -> str:
        return f"SentenceTransformers ({self._model_name})"

    def compute(self, cv_text: str, jd_text: str) -> float:
        if self._model is None:
            from sentence_transformers import SentenceTransformer  # type: ignore

            self._model = SentenceTransformer(self._model_name)

        embeddings = self._model.encode([cv_text, jd_text])
        score = cosine_similarity([embeddings[0]], [embeddings[1]])[0][0]
        return float(score)


class HybridSimilarityProvider:
    """Use SentenceTransformers when available and TF-IDF as a safe fallback."""

    def __init__(
        self,
        model_name: str = "all-MiniLM-L6-v2",
        fallback_provider: SimilarityProvider | None = None,
    ) -> None:
        self._model_name = model_name
        self._fallback_provider = fallback_provider or TfidfSimilarityProvider()
        self._sbert_provider: SentenceTransformerSimilarityProvider | None = None
        self._sbert_failed = False
        self._method = self._fallback_provider.method

    @property
    def method(self) -> str:
        return self._method

    def compute(self, cv_text: str, jd_text: str) -> float:
        if not self._sbert_failed:
            try:
                if self._sbert_provider is None:
                    self._sbert_provider = SentenceTransformerSimilarityProvider(self._model_name)
                score = self._sbert_provider.compute(cv_text, jd_text)
                self._method = self._sbert_provider.method
                return score
            except Exception:
                self._sbert_failed = True

        self._method = self._fallback_provider.method
        return self._fallback_provider.compute(cv_text, jd_text)
