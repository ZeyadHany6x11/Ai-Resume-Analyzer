import pytest
from pydantic import ValidationError

from resume_analyzer.config import Settings
from resume_analyzer.parsers import DocumentParser
from resume_analyzer.services import ResumeAnalysisService
from resume_analyzer.utils import AnalysisValidationError, DocumentParsingError


def test_settings_read_environment_variables(monkeypatch):
    monkeypatch.setenv("RESUME_ANALYZER_LOG_LEVEL", "DEBUG")
    monkeypatch.setenv("RESUME_ANALYZER_DATABASE_PATH", "custom.db")

    settings = Settings()

    assert settings.log_level == "DEBUG"
    assert settings.database_path == "custom.db"


def test_settings_validate_score_weights():
    with pytest.raises(ValidationError):
        Settings(semantic_weight=1.5)


def test_parser_raises_typed_document_error_for_invalid_pdf():
    with pytest.raises(DocumentParsingError):
        DocumentParser().extract_text(b"not a pdf")


def test_analysis_service_validates_required_text():
    class Parser:
        def extract_text(self, _source):
            return ""

    class Noop:
        def preprocess(self, text):
            return text.split()

    class Skills:
        def extract(self, _text, _extra_skills=None):
            return set()

    class Similarity:
        @property
        def method(self):
            return "fake"

        def compute(self, _cv, _jd):
            return 0.0

    class Ranking:
        def generate_report(self, *_args, **_kwargs):
            return {}

    service = ResumeAnalysisService(Parser(), Noop(), Skills(), Similarity(), Ranking())

    with pytest.raises(AnalysisValidationError):
        service.analyze("", "job")
