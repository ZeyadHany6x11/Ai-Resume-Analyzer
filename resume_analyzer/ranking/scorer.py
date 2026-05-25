from __future__ import annotations


class RankingService:
    """Convert analysis signals into a user-facing resume match report."""

    def __init__(self, semantic_weight: float = 0.6, skill_weight: float = 0.4) -> None:
        self._semantic_weight = semantic_weight
        self._skill_weight = skill_weight

    def generate_report(
        self,
        similarity_score: float,
        cv_skills: set[str],
        jd_skills: set[str],
        cv_tokens: list[str],
    ) -> dict:
        matched_skills = sorted(cv_skills & jd_skills)
        missing_skills = sorted(jd_skills - cv_skills)
        extra_skills = sorted(cv_skills - jd_skills)

        skill_ratio = len(matched_skills) / len(jd_skills) if jd_skills else 0.0
        blend = self._semantic_weight * similarity_score + self._skill_weight * skill_ratio
        match_score = min(100, round(blend * 100))

        if match_score >= 80:
            strength = "Excellent"
        elif match_score >= 60:
            strength = "Good"
        elif match_score >= 40:
            strength = "Fair"
        else:
            strength = "Needs Work"

        suggestions: list[str] = []

        if missing_skills:
            top_missing = missing_skills[:5]
            suggestions.append(
                f"Acquire or highlight these key skills: **{', '.join(top_missing)}**."
            )
            suggestions.append(
                "Add relevant personal or open-source projects that showcase the missing skills."
            )
            suggestions.append(
                "Consider online courses (Coursera, Udemy, edX, freeCodeCamp) "
                "or certifications for skill gaps."
            )

        if match_score < 60:
            suggestions.append(
                "Tailor your CV summary/objective to mirror the exact language "
                "and keywords in the job description."
            )

        project_keywords = ["project", "projects", "built", "developed", "created", "implemented"]
        if not any(keyword in cv_tokens for keyword in project_keywords):
            suggestions.append(
                "Add a dedicated **Projects** section with brief descriptions "
                "and technologies used."
            )

        certification_keywords = ["certificate", "certification", "certified", "credential"]
        if not any(keyword in cv_tokens for keyword in certification_keywords):
            suggestions.append(
                "Listing relevant certifications can significantly strengthen your application."
            )

        if len(extra_skills) > 10:
            suggestions.append(
                "You have many skills — make sure the most job-relevant ones "
                "are prominently placed near the top of your CV."
            )

        if not suggestions:
            suggestions.append(
                "Great fit! Ensure your CV is concise, well-formatted, "
                "ATS-friendly, and free of typos."
            )

        return {
            "match_score": match_score,
            "matched_skills": matched_skills,
            "missing_skills": missing_skills,
            "extra_skills": extra_skills,
            "suggestions": suggestions,
            "strength": strength,
            "similarity_score": round(similarity_score * 100, 1),
            "skill_overlap": round(skill_ratio * 100, 1),
        }
