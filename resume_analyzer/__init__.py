"""Public compatibility entrypoint for the resume analyzer package."""

from __future__ import annotations

from resume_analyzer.container import get_analysis_service


def _service():
    return get_analysis_service()


def analyze(cv_source, jd_text):
    return _service().analyze(cv_source, jd_text)


def compute_similarity(cv_text: str, jd_text: str) -> float:
    return _service().compute_similarity(cv_text, jd_text)


def extract_skills(text: str, extra_skills=None) -> set[str]:
    return _service().extract_skills(text, extra_skills)


def extract_text(source) -> str:
    return _service().extract_text(source)


def generate_report(
    similarity_score: float, cv_skills: set[str], jd_skills: set[str], cv_tokens: list[str]
) -> dict:
    return _service().generate_report(similarity_score, cv_skills, jd_skills, cv_tokens)


def preprocess_text(text: str) -> list[str]:
    return _service().preprocess_text(text)


def similarity_method() -> str:
    return _service().similarity_method


__all__ = [
    "analyze",
    "compute_similarity",
    "extract_skills",
    "extract_text",
    "generate_report",
    "preprocess_text",
    "similarity_method",
]
