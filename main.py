"""
FastAPI сервер для обработки изображений с помощью YOLO.
"""
from fastapi import FastAPI, UploadFile, File, HTTPException, Query
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.openapi.utils import get_openapi
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response
from enum import Enum
from typing import Optional, Dict, List, Union
from pydantic import BaseModel, Field
from datetime import datetime, timedelta
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
    report: str = Field(description="URL отчета об обработке")
    duration: int = Field(description="Время обработки в миллисекундах")

class JobError(BaseModel):
    """Информация об ошибке при обработке."""
    error: str = Field(description="Описание ошибки")

class Job(BaseModel):
    """Информация о задаче обработки изображения."""
    id: str = Field(description="Уникальный идентификатор задачи")
    filename: str = Field(description="Имя загруженного файла")
    status: JobStatus = Field(description="Текущий статус задачи")
    created_at: datetime = Field(description="Время создания задачи")
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

# Настройка CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],  # Разрешаем запросы с фронтенда
    allow_credentials=True,
    allow_methods=["*"],  # Разрешаем все методы
    allow_headers=["*"],  # Разрешаем все заголовки
)

class CharsetMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        response = await call_next(request)
        if "Content-Type" in response.headers:
            if "application/json" in response.headers["Content-Type"]:
                response.headers["Content-Type"] = "application/json; charset=utf-8"
        return response

app.add_middleware(CharsetMiddleware)

def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema
    
    openapi_schema = get_openapi(
        title=app.title,
        version=app.version,
        description=app.description,
        routes=app.routes,
    )
    
    # Устанавливаем кодировку UTF-8
    openapi_schema["info"]["x-logo"] = {
        "url": "https://fastapi.tiangolo.com/img/logo-margin/logo-teal.png"
    }
    
    app.openapi_schema = openapi_schema
    return app.openapi_schema

app.openapi = custom_openapi

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
        created_at=datetime.now(),
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
    description="Возвращает список задач с пагинацией, отсортированный по дате создания (новые сначала)"
)
def list_jobs(
    limit: int = Query(10, ge=1, le=100, description="Количество задач на странице"),
    offset: int = Query(0, ge=0, description="Смещение от начала списка")
) -> JobsResponse:
    all_jobs = get_all_jobs()
    # Сортируем по created_at в обратном порядке (новые сначала)
    all_jobs.sort(key=lambda x: x['created_at'], reverse=True)
    total = len(all_jobs)
    jobs = all_jobs[offset:offset + limit]
    return JobsResponse(
        items=[Job(**job) for job in jobs],
        total=total,
        limit=limit,
        offset=offset
    )
