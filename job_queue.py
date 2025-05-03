"""
Очередь задач для обработки изображений.
"""
import json
import os
import uuid
from datetime import datetime
from typing import Dict, List, Optional

JOBS_FILE = 'jobs.json'

def load_jobs() -> Dict[str, dict]:
    """Загружает список задач из файла."""
    if os.path.exists(JOBS_FILE):
        with open(JOBS_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}

def save_jobs(jobs: Dict[str, dict]) -> None:
    """Сохраняет список задач в файл."""
    with open(JOBS_FILE, 'w', encoding='utf-8') as f:
        json.dump(jobs, f, ensure_ascii=False, indent=2)

def add_job(filename: str) -> str:
    """Добавляет новую задачу в очередь."""
    jobs = load_jobs()
    job_id = str(uuid.uuid4())
    jobs[job_id] = {
        'id': job_id,
        'filename': filename,
        'status': 'queued',
        'created_at': datetime.now().isoformat(),
        'result': None
    }
    save_jobs(jobs)
    return job_id

def get_job(job_id: str) -> Optional[dict]:
    """Возвращает информацию о задаче по её идентификатору."""
    jobs = load_jobs()
    return jobs.get(job_id)

def get_all_jobs() -> List[dict]:
    """Возвращает список всех задач."""
    jobs = load_jobs()
    return list(jobs.values())

def update_job(job_id: str, **kwargs) -> None:
    """Обновляет информацию о задаче."""
    jobs = load_jobs()
    if job_id in jobs:
        jobs[job_id].update(kwargs)
        save_jobs(jobs)

def get_next_queued_job() -> Optional[dict]:
    """Возвращает следующую задачу в очереди."""
    jobs = load_jobs()
    for job in jobs.values():
        if job['status'] == 'queued':
            return job
    return None 