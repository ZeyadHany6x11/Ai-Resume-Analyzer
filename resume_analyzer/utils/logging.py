from __future__ import annotations

import json
import logging
from datetime import UTC, datetime

from resume_analyzer.config import Settings


class StructuredFormatter(logging.Formatter):
    """Compact JSON formatter for app logs with optional trace fields."""

    extra_fields = (
        "request_id",
        "job_id",
        "job_correlation_id",
        "attempt",
        "category",
        "duration_ms",
        "path",
        "method",
        "status_code",
    )

    def format(self, record: logging.LogRecord) -> str:
        payload = {
            "timestamp": datetime.fromtimestamp(record.created, tz=UTC).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        for field in self.extra_fields:
            value = getattr(record, field, None)
            if value is not None:
                payload[field] = value
        if record.exc_info and record.levelno >= logging.ERROR:
            payload["exception"] = self.formatException(record.exc_info)
        return json.dumps(payload, ensure_ascii=False)


def configure_logging(settings: Settings) -> None:
    root = logging.getLogger()
    root.setLevel(getattr(logging, settings.log_level.upper(), logging.INFO))

    handler = logging.StreamHandler()
    handler.setFormatter(StructuredFormatter())
    root.handlers.clear()
    root.addHandler(handler)
