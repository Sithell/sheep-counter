"""
FastAPI сервер для обработки изображений с помощью YOLO.
"""
from fastapi import FastAPI, UploadFile, File, HTTPException, Query
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from enum import Enum
from typing import Optional, Dict, List, Union
from pydantic import BaseModel, Field
import aiofiles
import os
from job_queue import add_job, get_job, get_all_jobs

class JobStatus(str, Enum):
    """Статусы задачи обработки изображения."""
    QUEUED = "queued"
    PROCESSING = "processing"
    DONE = "done"
    ERROR = "error"

class DetectionResult(BaseModel):
    """Результат обработки изображения."""
    sheep_count: int = Field(description="Количество найденных овец")
    image: str = Field(description="URL обработанного изображения")

class JobError(BaseModel):
    """Информация об ошибке при обработке."""
    error: str = Field(description="Описание ошибки")

class Job(BaseModel):
    """Информация о задаче обработки изображения."""
    id: str = Field(description="Уникальный идентификатор задачи")
    filename: str = Field(description="Имя загруженного файла")
    status: JobStatus = Field(description="Текущий статус задачи")
    result: Optional[Union[DetectionResult, JobError]] = Field(
        None,
        description="Результат обработки или информация об ошибке"
    )

class JobsResponse(BaseModel):
    """Ответ со списком задач и информацией о пагинации."""
    items: List[Job] = Field(description="Список задач")
    total: int = Field(description="Общее количество задач")
    limit: int = Field(description="Количество задач на странице")
    offset: int = Field(description="Смещение от начала списка")

app = FastAPI(
    title="Sheep Counter API",
    description="API для детекции объектов на изображениях с помощью YOLO",
    version="1.0.0"
)

# Раздача обработанных изображений
app.mount("/static", StaticFiles(directory="static"), name="static")

UPLOAD_DIR = 'uploads'
os.makedirs(UPLOAD_DIR, exist_ok=True)

@app.post(
    "/job",
    response_model=Job,
    summary="Загрузить изображение",
    description="Загружает изображение и создает задачу на обработку"
)
async def create_job(
    file: UploadFile = File(..., description="Изображение для обработки")
) -> Job:
    if not file.content_type.startswith('image/'):
        raise HTTPException(status_code=400, detail="File must be an image")
    
    filename = file.filename
    save_path = os.path.join(UPLOAD_DIR, filename)
    
    async with aiofiles.open(save_path, 'wb') as out_file:
        content = await file.read()
        await out_file.write(content)
    
    job_id = add_job(filename)
    return Job(
        id=job_id,
        filename=filename,
        status=JobStatus.QUEUED,
        result=None
    )

@app.get(
    "/job",
    response_model=Job,
    summary="Получить статус задачи",
    description="Возвращает информацию о задаче по её идентификатору"
)
def get_job_status(
    id: str = Query(..., description="Идентификатор задачи")
) -> Job:
    job = get_job(id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return Job(**job)

@app.get(
    "/jobs",
    response_model=JobsResponse,
    summary="Получить список задач",
    description="Возвращает список задач с пагинацией"
)
def list_jobs(
    limit: int = Query(10, ge=1, le=100, description="Количество задач на странице"),
    offset: int = Query(0, ge=0, description="Смещение от начала списка")
) -> JobsResponse:
    all_jobs = get_all_jobs()
    total = len(all_jobs)
    jobs = all_jobs[offset:offset + limit]
    return JobsResponse(
        items=[Job(**job) for job in jobs],
        total=total,
        limit=limit,
        offset=offset
    )
