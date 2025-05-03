"""
Фоновый обработчик задач для детекции объектов на изображениях.
"""
import os
import time
from job_queue import get_next_queued_job, update_job
from model import get_model
from PIL import Image
from typing import Dict

UPLOAD_DIR = 'uploads'
PROCESSED_DIR = 'static'
os.makedirs(PROCESSED_DIR, exist_ok=True)

SLEEP_TIME = 2  # секунд между проверками очереди

# Класс овцы в COCO: 18 (sheep)
SHEEP_CLASS_ID = 18

def process_job(job):
    """Обработка одной задачи."""
    job_id = job['id']
    filename = job['filename']
    input_path = os.path.join(UPLOAD_DIR, filename)
    output_path = os.path.join(PROCESSED_DIR, f"{job_id}.jpg")
    
    # Обновляем статус на processing
    update_job(job_id, status='processing')
    
    model = get_model()
    results = model(input_path)
    
    # Открываем изображение
    im0 = Image.open(input_path).convert("RGB")
    
    # Собираем боксы овец
    boxes = []
    confidences = []
    
    for r in results:
        for box, cls, conf in zip(r.boxes.xyxy.cpu().numpy(), 
                                r.boxes.cls.cpu().numpy(),
                                r.boxes.conf.cpu().numpy()):
            if int(cls) == SHEEP_CLASS_ID:
                boxes.append(box)
                confidences.append(conf)
    
    # Рисуем рамки
    if boxes:
        import cv2
        import numpy as np
        img = cv2.cvtColor(np.array(im0), cv2.COLOR_RGB2BGR)
        font_scale = 1.0
        thickness = 2
        
        for box, conf in zip(boxes, confidences):
            x1, y1, x2, y2 = map(int, box)
            cv2.rectangle(img, (x1, y1), (x2, y2), (0,255,0), 2)
            label = f'Sheep: {conf:.2f}'
            
            cv2.putText(
                img, label, (x1, y1-10),
                cv2.FONT_HERSHEY_SIMPLEX,
                font_scale, (0,255,0),
                thickness,
                cv2.LINE_8
            )
        
        cv2.imwrite(output_path, img)
    else:
        im0.save(output_path)
    
    # Обновляем задачу с результатом
    update_job(
        job_id,
        status='done',
        result={
            'sheep_count': len(boxes),
            'image': f'/static/{job_id}.jpg'
        }
    )

def main():
    """Основной цикл обработки задач."""
    print("Worker started. Press Ctrl+C to stop.")
    while True:
        job = get_next_queued_job()
        if job:
            print(f"Processing job {job['id']} ({job['filename']})...")
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