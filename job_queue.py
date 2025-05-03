import json
import uuid
import threading
from typing import Optional, Dict, Any, List

JOBS_FILE = 'jobs.json'
LOCK = threading.Lock()

def load_jobs() -> List[Dict[str, Any]]:
    with LOCK:
        try:
            with open(JOBS_FILE, 'r') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return []

def save_jobs(jobs: List[Dict[str, Any]]):
    with LOCK:
        with open(JOBS_FILE, 'w') as f:
            json.dump(jobs, f, indent=2)

def add_job(filename: str) -> str:
    jobs = load_jobs()
    job_id = str(uuid.uuid4())
    job = {
        'id': job_id,
        'filename': filename,
        'status': 'queued',
        'result': None
    }
    jobs.append(job)
    save_jobs(jobs)
    return job_id

def update_job(job_id: str, **kwargs):
    jobs = load_jobs()
    for job in jobs:
        if job['id'] == job_id:
            job.update(kwargs)
            break
    save_jobs(jobs)

def get_job(job_id: str) -> Optional[Dict[str, Any]]:
    jobs = load_jobs()
    for job in jobs:
        if job['id'] == job_id:
            return job
    return None

def get_all_jobs() -> List[Dict[str, Any]]:
    return load_jobs()

def get_next_queued_job() -> Optional[Dict[str, Any]]:
    jobs = load_jobs()
    for job in jobs:
        if job['status'] == 'queued':
            return job
    return None 