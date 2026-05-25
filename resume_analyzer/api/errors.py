from __future__ import annotations

import logging

from fastapi import HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from resume_analyzer.utils import ResumeAnalyzerError

logger = logging.getLogger(__name__)


def error_response(
    request: Request,
    *,
    status_code: int,
    code: str,
    message: str,
) -> JSONResponse:
    request_id = getattr(request.state, "request_id", None)
    return JSONResponse(
        status_code=status_code,
        content={
            "error": {
                "code": code,
                "message": message,
                "request_id": request_id,
            }
        },
    )


async def resume_analyzer_exception_handler(
    request: Request, exc: ResumeAnalyzerError
) -> JSONResponse:
    logger.warning(
        "Expected application error",
        extra={
            "request_id": getattr(request.state, "request_id", None),
            "category": "application",
        },
    )
    return error_response(
        request,
        status_code=400,
        code=exc.__class__.__name__,
        message=exc.safe_message,
    )


async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
    return error_response(
        request,
        status_code=exc.status_code,
        code="http_error",
        message=str(exc.detail),
    )


async def validation_exception_handler(
    request: Request, exc: RequestValidationError
) -> JSONResponse:
    logger.warning(
        "Request validation failed",
        extra={
            "request_id": getattr(request.state, "request_id", None),
            "category": "validation",
        },
    )
    return error_response(
        request,
        status_code=422,
        code="validation_error",
        message="Request validation failed.",
    )


async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    logger.exception(
        "Unhandled API error",
        extra={
            "request_id": getattr(request.state, "request_id", None),
            "category": "unexpected",
        },
    )
    return error_response(
        request,
        status_code=500,
        code="internal_error",
        message="An unexpected server error occurred.",
    )
