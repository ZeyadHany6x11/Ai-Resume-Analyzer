"""Compatibility entrypoint for the resume analyzer package.

The project is being migrated from a flat module to a package-based
architecture. During the transition, re-export the legacy public functions so
existing imports such as ``from resume_analyzer import analyze`` keep working.
"""

from __future__ import annotations

import importlib.util
from pathlib import Path
from types import ModuleType


def _load_legacy_module() -> ModuleType:
    legacy_path = Path(__file__).resolve().parent.parent / "resume_analyzer.py"
    spec = importlib.util.spec_from_file_location("_legacy_resume_analyzer", legacy_path)
    if spec is None or spec.loader is None:
        raise ImportError(f"Cannot load legacy analyzer module from {legacy_path}")

    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


_legacy = _load_legacy_module()

analyze = _legacy.analyze
compute_similarity = _legacy.compute_similarity
extract_skills = _legacy.extract_skills
extract_text = _legacy.extract_text
generate_report = _legacy.generate_report
preprocess_text = _legacy.preprocess_text
similarity_method = _legacy.similarity_method

__all__ = [
    "analyze",
    "compute_similarity",
    "extract_skills",
    "extract_text",
    "generate_report",
    "preprocess_text",
    "similarity_method",
]
