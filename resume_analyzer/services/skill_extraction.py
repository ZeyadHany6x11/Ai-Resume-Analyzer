from __future__ import annotations

import re
from collections.abc import Iterable

from skills_list import SKILLS_DATABASE


class SkillExtractionService:
    """Extract known skills from resume or job-description text."""

    def __init__(self, skills_database: Iterable[str] = SKILLS_DATABASE) -> None:
        self._skills_database = [skill.lower() for skill in skills_database]

    def extract(self, text: str, extra_skills: Iterable[str] | None = None) -> set[str]:
        text_lower = text.lower()
        skill_pool = list(self._skills_database)
        if extra_skills:
            skill_pool.extend(skill.lower() for skill in extra_skills)

        found: set[str] = set()

        for skill in skill_pool:
            if " " not in skill:
                pattern = r"\b" + re.escape(skill) + r"\b"
                if re.search(pattern, text_lower):
                    found.add(skill)
            elif skill in text_lower:
                found.add(skill)

        pattern_years = re.compile(
            r"\d+\+?\s+years?\s+(?:of\s+)?([a-z][a-z0-9+#.\-/]+)",
            re.IGNORECASE,
        )
        for match in pattern_years.finditer(text_lower):
            candidate = match.group(1).strip().lower()
            if candidate in self._skills_database:
                found.add(candidate)

        return found
