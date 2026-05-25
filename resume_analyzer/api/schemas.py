from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class TextAnalysisRequest(BaseModel):
    cv_text: str = Field(min_length=1)
    job_description: str = Field(min_length=1)


class AnalysisSubmissionResponse(BaseModel):
    analysis_id: str
    status: str


class AnalysisStatusResponse(BaseModel):
    analysis_id: str
    status: str
    error_message: str | None = None


class AnalysisJobListItem(BaseModel):
    analysis_id: str
    status: str
    input_type: str
    created_at: str | None = None
    updated_at: str | None = None
    error_message: str | None = None


class AnalysisJobListResponse(BaseModel):
    jobs: list[AnalysisJobListItem]
    limit: int
    offset: int


class AnalysisResultResponse(BaseModel):
    analysis_id: str
    status: str
    result: dict[str, Any] | None = None


class ErrorBody(BaseModel):
    code: str
    message: str
    request_id: str | None = None


class ErrorResponse(BaseModel):
    error: ErrorBody
