"""
Запуск воркера:
    python worker.py
"""
import os
import time
from job_queue import get_next_queued_job, update_job
from model import get_model
from ultralytics.utils.plotting import save_one_box
from PIL import Image

UPLOAD_DIR = 'uploads'
PROCESSED_DIR = 'static'
os.makedirs(PROCESSED_DIR, exist_ok=True)

SLEEP_TIME = 2  # секунд между проверками очереди

# Класс овцы в COCO: 18 (sheep)
SHEEP_CLASS_ID = 18

def process_job(job):
    job_id = job['id']
    filename = job['filename']
    input_path = os.path.join(UPLOAD_DIR, filename)
    output_path = os.path.join(PROCESSED_DIR, f"{job_id}.jpg")
    model = get_model()
    results = model(input_path)
    sheep_count = 0
    im0 = Image.open(input_path).convert("RGB")
    boxes = []
    for r in results:
        for box, cls in zip(r.boxes.xyxy.cpu().numpy(), r.boxes.cls.cpu().numpy()):
            if int(cls) == SHEEP_CLASS_ID:
                sheep_count += 1
                boxes.append(box)
    # Рисуем рамки
    if boxes:
        import cv2
        import numpy as np
        img = cv2.cvtColor(np.array(im0), cv2.COLOR_RGB2BGR)
        font_scale = 0.5
        thickness = 1
        for box, cls, conf in zip(boxes, r.boxes.cls.cpu().numpy(), r.boxes.conf.cpu().numpy()):
            x1, y1, x2, y2 = map(int, box)
            cv2.rectangle(img, (x1, y1), (x2, y2), (0,255,0), 2)
            label = f'{conf:.2f}'
            cv2.putText(
                img, label, (x1, y1-10),
                cv2.FONT_HERSHEY_SIMPLEX, font_scale, (0,255,0), thickness, cv2.LINE_4
            )
        cv2.imwrite(output_path, img)
    else:
        im0.save(output_path)
    update_job(job_id, status='done', result={'sheep_count': sheep_count, 'image': f'/static/{job_id}.jpg'})

def main():
    print("Worker started. Press Ctrl+C to stop.")
    while True:
        job = get_next_queued_job()
        if job:
            print(f"Processing job {job['id']} ({job['filename']})...")
            update_job(job['id'], status='processing')
            try:
                process_job(job)
                print(f"Job {job['id']} done.")
            except Exception as e:
                print(f"Error processing job {job['id']}: {e}")
                update_job(job['id'], status='error', result={'error': str(e)})
        else:
            time.sleep(SLEEP_TIME)

if __name__ == "__main__":
    main() 