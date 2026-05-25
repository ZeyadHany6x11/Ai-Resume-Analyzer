from resume_analyzer.services import SkillExtractionService


def test_skill_extraction_finds_single_and_multi_word_skills():
    service = SkillExtractionService(["python", "machine learning", "sql"])

    skills = service.extract("Built Python APIs and machine learning pipelines.")

    assert skills == {"python", "machine learning"}


def test_skill_extraction_respects_word_boundaries():
    service = SkillExtractionService(["r", "sql"])

    skills = service.extract("Worked with browser APIs and SQL databases.")

    assert skills == {"sql"}


def test_skill_extraction_accepts_extra_skills():
    service = SkillExtractionService(["python"])

    skills = service.extract("Production experience with Snowpark.", extra_skills=["Snowpark"])

    assert skills == {"snowpark"}


def test_skill_extraction_detects_years_of_known_skill():
    service = SkillExtractionService(["python"])

    skills = service.extract("5+ years of Python development.")

    assert skills == {"python"}
