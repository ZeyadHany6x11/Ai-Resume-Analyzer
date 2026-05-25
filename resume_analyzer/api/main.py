from __future__ import annotations

from collections.abc import Callable

from fastapi import (
    APIRouter,
    BackgroundTasks,
    Depends,
    FastAPI,
    File,
    Form,
    HTTPException,
    UploadFile,
)
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from resume_analyzer.api.errors import (
    http_exception_handler,
    resume_analyzer_exception_handler,
    unhandled_exception_handler,
    validation_exception_handler,
)
from resume_analyzer.api.middleware import request_context_middleware
from resume_analyzer.api.schemas import (
    AnalysisJobListItem,
    AnalysisJobListResponse,
    AnalysisResultResponse,
    AnalysisStatusResponse,
    AnalysisSubmissionResponse,
    TextAnalysisRequest,
)
from resume_analyzer.config import get_settings
from resume_analyzer.container import get_job_service
from resume_analyzer.services import AnalysisJobService
from resume_analyzer.utils import AnalysisValidationError, ResumeAnalyzerError


class FastAPIBackgroundTasksRunner:
    def __init__(self, background_tasks: BackgroundTasks) -> None:
        self._background_tasks = background_tasks

    def add_task(self, func: Callable, *args, **kwargs) -> None:
        self._background_tasks.add_task(func, *args, **kwargs)


def get_job_service_dependency() -> AnalysisJobService:
    return get_job_service()


app = FastAPI(title="AI Resume Analyzer API")
app.middleware("http")(request_context_middleware)
app.add_exception_handler(ResumeAnalyzerError, resume_analyzer_exception_handler)
app.add_exception_handler(HTTPException, http_exception_handler)
app.add_exception_handler(RequestValidationError, validation_exception_handler)
app.add_exception_handler(Exception, unhandled_exception_handler)
router = APIRouter()


def validate_upload(file: UploadFile, content: bytes) -> None:
    settings = get_settings()
    max_bytes = settings.max_upload_size_mb * 1024 * 1024
    filename = (file.filename or "").lower()

    if not content:
        raise AnalysisValidationError("Uploaded file is empty.")
    if len(content) > max_bytes:
        raise AnalysisValidationError(f"Uploaded file exceeds {settings.max_upload_size_mb} MB.")
    if not filename.endswith(".pdf"):
        raise AnalysisValidationError("Only PDF resume uploads are supported.")
    if file.content_type not in {None, "", "application/pdf", "application/octet-stream"}:
        raise AnalysisValidationError("Uploaded file must be a PDF.")


@router.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@router.post("/analyses/text", response_model=AnalysisSubmissionResponse, status_code=202)
def submit_text_analysis(
    request: TextAnalysisRequest,
    background_tasks: BackgroundTasks,
    job_service: AnalysisJobService = Depends(get_job_service_dependency),
) -> AnalysisSubmissionResponse:
    job = job_service.create_text_job(request.cv_text, request.job_description)
    job_service.enqueue(job.id, FastAPIBackgroundTasksRunner(background_tasks))
    return AnalysisSubmissionResponse(analysis_id=job.id, status=job.status)


@router.post("/analyses/file", response_model=AnalysisSubmissionResponse, status_code=202)
async def submit_file_analysis(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    job_description: str = Form(...),
    job_service: AnalysisJobService = Depends(get_job_service_dependency),
) -> AnalysisSubmissionResponse:
    content = await file.read()
    validate_upload(file, content)
    job = job_service.create_file_job(content, job_description)
    job_service.enqueue(job.id, FastAPIBackgroundTasksRunner(background_tasks))
    return AnalysisSubmissionResponse(analysis_id=job.id, status=job.status)


@router.get("/analyses/{analysis_id}/status", response_model=AnalysisStatusResponse)
def get_analysis_status(
    analysis_id: str,
    job_service: AnalysisJobService = Depends(get_job_service_dependency),
) -> AnalysisStatusResponse:
    job = job_service.get_status(analysis_id)
    if job is None:
        raise HTTPException(status_code=404, detail="Analysis job not found.")
    return AnalysisStatusResponse(
        analysis_id=job.id,
        status=job.status,
        error_message=job.error_message,
    )


@router.get("/analyses", response_model=AnalysisJobListResponse)
def list_analyses(
    status: str | None = None,
    limit: int = 50,
    offset: int = 0,
    job_service: AnalysisJobService = Depends(get_job_service_dependency),
) -> AnalysisJobListResponse:
    jobs = job_service.list_jobs(status=status, limit=limit, offset=offset)
    return AnalysisJobListResponse(
        jobs=[
            AnalysisJobListItem(
                analysis_id=job.id,
                status=job.status,
                input_type=job.input_type,
                created_at=job.created_at,
                updated_at=job.updated_at,
                error_message=job.error_message,
            )
            for job in jobs
        ],
        limit=limit,
        offset=offset,
    )


@router.get("/analyses/{analysis_id}", response_model=AnalysisResultResponse)
def get_analysis_result(
    analysis_id: str,
    job_service: AnalysisJobService = Depends(get_job_service_dependency),
):
    job = job_service.get_status(analysis_id)
    if job is None:
        raise HTTPException(status_code=404, detail="Analysis job not found.")

    result = job_service.get_result(analysis_id)
    response = AnalysisResultResponse(analysis_id=analysis_id, status=job.status, result=result)
    if result is None:
        return JSONResponse(status_code=202, content=response.model_dump())
    return response


app.include_router(router)
app.include_router(router, prefix="/api/v1")
