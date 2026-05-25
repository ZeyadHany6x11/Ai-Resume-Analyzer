from __future__ import annotations

from collections.abc import Callable

from fastapi import BackgroundTasks, Depends, FastAPI, File, Form, HTTPException, UploadFile
from fastapi.responses import JSONResponse

from resume_analyzer.api.schemas import (
    AnalysisResultResponse,
    AnalysisStatusResponse,
    AnalysisSubmissionResponse,
    TextAnalysisRequest,
)
from resume_analyzer.container import get_job_service
from resume_analyzer.services import AnalysisJobService


class FastAPIBackgroundTasksRunner:
    def __init__(self, background_tasks: BackgroundTasks) -> None:
        self._background_tasks = background_tasks

    def add_task(self, func: Callable, *args, **kwargs) -> None:
        self._background_tasks.add_task(func, *args, **kwargs)


def get_job_service_dependency() -> AnalysisJobService:
    return get_job_service()


app = FastAPI(title="AI Resume Analyzer API")


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/analyses/text", response_model=AnalysisSubmissionResponse, status_code=202)
def submit_text_analysis(
    request: TextAnalysisRequest,
    background_tasks: BackgroundTasks,
    job_service: AnalysisJobService = Depends(get_job_service_dependency),
) -> AnalysisSubmissionResponse:
    job = job_service.create_text_job(request.cv_text, request.job_description)
    job_service.enqueue(job.id, FastAPIBackgroundTasksRunner(background_tasks))
    return AnalysisSubmissionResponse(analysis_id=job.id, status=job.status)


@app.post("/analyses/file", response_model=AnalysisSubmissionResponse, status_code=202)
async def submit_file_analysis(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    job_description: str = Form(...),
    job_service: AnalysisJobService = Depends(get_job_service_dependency),
) -> AnalysisSubmissionResponse:
    content = await file.read()
    job = job_service.create_file_job(content, job_description)
    job_service.enqueue(job.id, FastAPIBackgroundTasksRunner(background_tasks))
    return AnalysisSubmissionResponse(analysis_id=job.id, status=job.status)


@app.get("/analyses/{analysis_id}/status", response_model=AnalysisStatusResponse)
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


@app.get("/analyses/{analysis_id}", response_model=AnalysisResultResponse)
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
