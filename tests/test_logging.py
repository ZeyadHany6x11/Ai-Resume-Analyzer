import json
import logging

from resume_analyzer.utils.logging import StructuredFormatter


def test_structured_formatter_includes_trace_and_job_fields():
    record = logging.LogRecord(
        name="test",
        level=logging.INFO,
        pathname=__file__,
        lineno=1,
        msg="hello",
        args=(),
        exc_info=None,
    )
    record.request_id = "req-1"
    record.job_id = "job-1"
    record.job_correlation_id = "job-1"
    record.category = "job_lifecycle"

    payload = json.loads(StructuredFormatter().format(record))

    assert payload["message"] == "hello"
    assert payload["request_id"] == "req-1"
    assert payload["job_id"] == "job-1"
    assert payload["job_correlation_id"] == "job-1"
    assert payload["category"] == "job_lifecycle"
