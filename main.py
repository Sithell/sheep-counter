"""
Запуск сервера:
    uvicorn main:app --reload
"""
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
import aiofiles
import os
from job_queue import add_job, get_job, get_all_jobs

app = FastAPI()

# Раздача обработанных изображений
app.mount("/static", StaticFiles(directory="static"), name="static")

UPLOAD_DIR = 'uploads'
os.makedirs(UPLOAD_DIR, exist_ok=True)

@app.post("/job")
async def create_job(file: UploadFile = File(...)):
    if not file.content_type.startswith('image/'):
        raise HTTPException(status_code=400, detail="File must be an image.")
    filename = file.filename
    save_path = os.path.join(UPLOAD_DIR, filename)
    # Сохраняем файл асинхронно
    async with aiofiles.open(save_path, 'wb') as out_file:
        content = await file.read()
        await out_file.write(content)
    job_id = add_job(filename)
    return {"job_id": job_id}

@app.get("/job")
def get_job_status(id: str):
    job = get_job(id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found.")
    return job

@app.get("/jobs")
def list_jobs():
    return get_all_jobs()
